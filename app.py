from flask import Blueprint,current_app, render_template, jsonify,request, redirect, url_for, session,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse

import os
from datetime import datetime
from glob import glob

import plotly.io as pio
import pandas as pd
import json
from pathlib import Path
import shutil
import numpy as np
import io

import proteovis as pv
from utils import *
from models import *
from forms import *
import gcs_utils

main = Blueprint('main', __name__)


@main.before_request
@login_required
def before_request():
    pass


# logoutページのルーティング
@main.route('/logout')
def logout():
  # logout_user関数を呼び出し
  logout_user()
  # トップページにリダイレクト
  return redirect(url_for('main.index'))



@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('/new_experiment', methods=['GET', 'POST'])
def new_experiment():
    if request.method == 'POST':
        experiment_name = request.form.get('experiment-name')
        user_name = request.form.get('user-name')
        project_code = request.form.get('project-code')
        bucket_name = current_app.config['GCS_BUCKET_NAME']

        # Check if experiment already exists in GCS
        # We check if any object exists with the experiment name as a prefix.
        if gcs_utils.list_blobs_with_prefix(bucket_name, prefix=f"{experiment_name}/"):
            return render_template('new_experiment.html', error="Error: An experiment with that name already exists. Please choose a different name.")

        new_experiment_rec = Experiment(name=experiment_name,
                                        user_id=user_name,
                                        project_code=project_code)
        db.session.add(new_experiment_rec)
        db.session.commit()

        exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)

        analysis_prefix = exppath.analysis_prefix
        raw_prefix = exppath.raw_prefix
        worksheet_prefix = exppath.worksheet_prefix

        # No need for os.makedirs with GCS

        files = request.files.getlist('files[]')

        # Upload raw files
        if files:
            for file in files:
                if file.filename:
                    blob_name = f"{raw_prefix}/{file.filename}"
                    gcs_utils.upload_blob_from_file_object(bucket_name, file.stream, blob_name)
                    print(f"Uploaded file: {blob_name}")

        print(f"Experiment Name: {experiment_name}")
        print(f"User Name: {user_name}")
        print(f"Project Code: {project_code}")
      
        # Process uploaded files
        rawfile_list = gcs_utils.list_blobs_with_prefix(bucket_name, prefix=raw_prefix)

        for path in rawfile_list:
            name = os.path.basename(path).split(".")[0]
            data_prefix = f"{analysis_prefix}/{name}"
            
            # No need to check for folder existence in GCS

            file_ext = os.path.splitext(path)[1].lower()

            if file_ext == ".zip":
                akta_df, frac_df, phase_df, akta_fig = get_akta_data(bucket_name, path)
                gcs_utils.dataframe_to_gcs_csv(akta_df, bucket_name, f"{data_prefix}/all_data.csv")
                gcs_utils.dataframe_to_gcs_csv(frac_df, bucket_name, f"{data_prefix}/fraction.csv")
                gcs_utils.dataframe_to_gcs_csv(phase_df, bucket_name, f"{data_prefix}/phase.csv")

                # Save figure to GCS
                img_bytes = akta_fig.to_image(format="png", engine="kaleido")
                gcs_utils.upload_blob_from_string(bucket_name, img_bytes, f"{data_prefix}/icon.png", 'image/png')

                run = Run(experiment_id=new_experiment_rec.id, name=name, type="AKTA")
                db.session.add(run)
                db.session.commit()

                config = {"run_id": run.id}
                json_save(bucket_name, config, f"{data_prefix}/config.json")

            elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]:
                page_fig = get_page_image(bucket_name, path)

                # Save figure to GCS
                img_bytes = page_fig.to_image(format="png", engine="kaleido")
                gcs_utils.upload_blob_from_string(bucket_name, img_bytes, f"{data_prefix}/icon.png", 'image/png')
                
                run = Run(experiment_id=new_experiment_rec.id, name=name, type="PAGE")
                db.session.add(run)
                db.session.commit()
                
                config = {"ext": file_ext, "run_id": run.id}
                json_save(bucket_name, config, f"{data_prefix}/config.json")

                
            
            
                

    
        return redirect(url_for(f"main.experiment",experiment_name=experiment_name))#select(experiment_name)

    return render_template('new_experiment.html', error=None,user_name=current_user.name) #エラーメッセージをクリア



@main.route("/experiment/<experiment_name>/upload", methods=["POST"])
def upload(experiment_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    experiment_id = Experiment.query.filter_by(name=experiment_name).first().id

    raw_prefix = exppath.raw_prefix
    analysis_prefix = exppath.analysis_prefix

    file = request.files.get('file')
    uploaded_blob_path = ""

    if file and file.filename:
        uploaded_blob_path = f"{raw_prefix}/{file.filename}"
        gcs_utils.upload_blob_from_file_object(bucket_name, file.stream, uploaded_blob_path)
        print(f"Uploaded file: {uploaded_blob_path}")
    else:
        # Handle case where no file is uploaded or filename is empty
        flash("No file selected for upload.")
        return redirect(url_for("main.experiment", experiment_name=experiment_name))

    # Process the single uploaded file
    path = uploaded_blob_path
    name = os.path.basename(path).split(".")[0]
    data_prefix = f"{analysis_prefix}/{name}"

    # Check if analysis for this run already exists
    if gcs_utils.list_blobs_with_prefix(bucket_name, prefix=f"{data_prefix}/"):
        flash(f"Error: Analysis for '{name}' already exists.")
        return redirect(url_for("main.experiment", experiment_name=experiment_name))

    file_ext = os.path.splitext(path)[1].lower()

    if file_ext == ".zip":
        akta_df, frac_df, phase_df, akta_fig = get_akta_data(bucket_name, path)
        gcs_utils.dataframe_to_gcs_csv(akta_df, bucket_name, f"{data_prefix}/all_data.csv")
        gcs_utils.dataframe_to_gcs_csv(frac_df, bucket_name, f"{data_prefix}/fraction.csv")
        gcs_utils.dataframe_to_gcs_csv(phase_df, bucket_name, f"{data_prefix}/phase.csv")

        img_bytes = akta_fig.to_image(format="png", engine="kaleido")
        gcs_utils.upload_blob_from_string(bucket_name, img_bytes, f"{data_prefix}/icon.png", 'image/png')

        run = Run(experiment_id=experiment_id, name=name, type="AKTA")
        db.session.add(run)
        db.session.commit()

        config = {"run_id": run.id}
        json_save(bucket_name, config, f"{data_prefix}/config.json")

    elif file_ext in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]:
        page_fig = get_page_image(bucket_name, path)
        img_bytes = page_fig.to_image(format="png", engine="kaleido")
        gcs_utils.upload_blob_from_string(bucket_name, img_bytes, f"{data_prefix}/icon.png", 'image/png')

        run = Run(experiment_id=experiment_id, name=name, type="PAGE")
        db.session.add(run)
        db.session.commit()

        config = {"ext": file_ext, "run_id": run.id}
        json_save(bucket_name, config, f"{data_prefix}/config.json")


    return redirect(url_for(f"main.experiment",experiment_name=experiment_name))#select(experiment_name)


@main.route('/open_experiment', methods=['GET'])
def open_experiment():
    experiments = Experiment.query.all()
    exp_dic = {}

    for exp in experiments:
        # The data about runs is in the database, so we don't need to check GCS here.
        # This simplifies the logic significantly compared to the old glob-based version.
        data = [run.name for run in Run.query.filter_by(experiment_id=exp.id).all()]
        exp_dic[exp.name] = ", ".join(data)

    return render_template('open_experiment.html', experiments=exp_dic)


@main.route(f"/experiment/<experiment_name>/delete")
def delete_experiment(experiment_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']

    # First, delete the files from GCS
    gcs_utils.delete_folder(bucket_name, folder_prefix=experiment_name)

    # Then, delete the records from the database
    exp_to_delete = Experiment.query.filter_by(name=experiment_name).first()
    if exp_to_delete:
        # This will cascade delete runs, fractions etc. if configured in the model.
        # Assuming cascading is set up correctly. If not, would need to delete children explicitly.
        db.session.delete(exp_to_delete)
        db.session.commit()
        flash(f"Experiment '{experiment_name}' and all associated data have been deleted.")
    else:
        flash(f"Experiment '{experiment_name}' not found in the database.")

    return redirect(url_for("main.open_experiment"))



@main.route("/experiment/<experiment_name>/worksheet4akta/<worksheet_name>", methods=["GET", "POST"])
def worksheet4akta(experiment_name, worksheet_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    experiment_id = Experiment.query.filter_by(name=experiment_name).first().id

    worksheet_prefix = exppath.worksheet_prefix
    worksheet_path = f"{worksheet_prefix}/{worksheet_name}.json"

    default_data_rows = [
        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
        {"rate": 1, "length": 1, "percentB": 0, "slopeType": "step", "path": "sample loop", "fractionVol": 0},
        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
        {"rate": 1, "length": 10, "percentB": 50, "slopeType": "gradient", "path": "", "fractionVol": 0},
        {"rate": 1, "length": 5, "percentB": 100, "slopeType": "step", "path": "", "fractionVol": 0},
        {"rate": 1, "length": 3, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
    ]

    if request.method == "GET":
        data = {}
        if gcs_utils.blob_exists(bucket_name, worksheet_path):
            json_string = gcs_utils.download_blob_as_string(bucket_name, worksheet_path)
            json_data = json.loads(json_string)
            data["rows"] = list(json_data.get("program", {}).values()) if json_data.get("program") else default_data_rows
            data["cv"] = json_data.get("column_cv", 1)
        else:
            data["rows"] = default_data_rows
            data["cv"] = 1

        data_json_string = json.dumps(data)
        return render_template("worksheet4akta.html", data=data_json_string)

    elif request.method == "POST":
        # Buffer data processing logic (remains the same)
        key_list = list(request.form.keys())
        buf_data = {"a1":[], "a2":[], "b1":[], "b2":[]}
        for key in key_list:
            if key[1:3] in list(buf_data.keys()):
                raw_text = request.form.get(key)
                buffer_name, buffer_conc = raw_text.replace(")", "").split(" (")
                buf_data[key[1:3]].append(f"{buffer_name}:{buffer_conc} mM")
        
        buf_data_input = {"a1":"", "a2":"", "b1":"", "b2":""}
        for ke, va in buf_data.items():
            buf_data_input[ke] = ", ".join(va)

        # Form data extraction (remains mostly the same)
        data = {
            "worksheet_name": request.form.get("worksheet-name"),
            "column_name": request.form.get("column-name"),
            "column_cv": request.form.get("column-cv"),
            "sample_loop_name": request.form.get("sample-loop-name"),
            "sample_loop_volume": request.form.get("sample-loop-volume"),
            "buffer_a1": buf_data_input["a1"], "number_a1": request.form.get("number-a1"), "a1_ph": request.form.get("a1-ph"),
            "buffer_a2": buf_data_input["a2"], "number_a2": request.form.get("number-a2"), "a2_ph": request.form.get("a2-ph"),
            "buffer_b1": buf_data_input["b1"], "number_b1": request.form.get("number-b1"), "b1_ph": request.form.get("b1-ph"),
            "buffer_b2": buf_data_input["b2"], "number_b2": request.form.get("number-b2"), "b2_ph": request.form.get("b2-ph"),
            "sample_pump_s1": request.form.get("sample-pump-s1"),
            "sample_pump_buffer": request.form.get("sample-pump-buffer"),
        }

        for k, v in data.items():
            try: data[k] = float(v)
            except (ValueError, TypeError): continue

        # Program table data extraction (remains the same)
        program_df = pd.DataFrame(data=dict(
            rate=np.array(request.form.getlist('rate[]')).astype(float),
            length=np.array(request.form.getlist('length[]')).astype(float),
            percentB=np.array(request.form.getlist('percentB[]')).astype(float),
            slopeType=request.form.getlist('slopeType[]'),
            path=request.form.getlist('path[]'),
            fractionVol=np.array(request.form.getlist('fractionVol[]')).astype(float)
        ))
        data["program"] = program_df.to_dict(orient="index")
        
        # Save to GCS
        json_save(bucket_name, data, worksheet_path)

        # Database logic (remains the same)
        worksheet = Worksheet.query.filter_by(experiment_id=experiment_id, name=worksheet_name, type="AKTA").first()
        if not worksheet:
            worksheet = Worksheet(experiment_id=experiment_id, name=worksheet_name, type="AKTA")
            db.session.add(worksheet)
        db.session.commit()

        return redirect(url_for("main.worksheet4aktaview", experiment_name=experiment_name, worksheet_name=worksheet_name))


@main.route("/experiment/<experiment_name>/worksheet4akta/<worksheet_name>/view", methods=["GET"])
def worksheet4aktaview(experiment_name, worksheet_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)

    worksheet_path = f"{exppath.worksheet_prefix}/{worksheet_name}.json"

    json_string = gcs_utils.download_blob_as_string(bucket_name, worksheet_path)
    data = json.loads(json_string)
    data_json_string = json.dumps(data)

    chart_data = {
        "rows": list(data.get("program", {}).values()),
        "cv": data.get("column_cv", 1)
    }
    chart_data_json_string = json.dumps(chart_data)

    return render_template("worksheet4aktaview.html",
                           data=data_json_string,
                           chart_data=chart_data_json_string)



@main.route(f"/experiment/<experiment_name>")
def experiment(experiment_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    sample_list = get_samples(exppath)
    return render_template('template4input.html', experiment_name=experiment_name, sample_list=sample_list)


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/show", methods=["GET"])
def show_akta(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    
    sample_list = get_samples(exppath)
    fig_html = get_akta_fig(bucket_name, datapath.analysis_prefix)
    info = sampling_data(datapath)

    return render_template('show_akta.html',
                           experiment_name=experiment_name,
                           sample_list=sample_list,
                           akta_fig=fig_html,
                           info=info)


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/phase", methods=['GET', 'POST'])
def akta(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    analysis_prefix = datapath.analysis_prefix

    if request.method == 'GET':
        sample_list = get_samples(exppath)
        fig_html = get_akta_fig(bucket_name, analysis_prefix)
        phase_list = get_phase_data(bucket_name, analysis_prefix)
        return render_template('phase.html', sample_list=sample_list, akta_fig=fig_html, phase_list=phase_list)

    else: # POST
        df = get_phase_df(bucket_name, analysis_prefix)
        for i in df.index:
            df.loc[i, "Phase"] = request.form.get(f'phase_{i}')
            df.loc[i, "Color_code"] = request.form.get(f'color_{i}')
        
        gcs_utils.dataframe_to_gcs_csv(df, bucket_name, f"{analysis_prefix}/phase.csv")
        return redirect(url_for(f"main.akta_pooling", experiment_name=experiment_name, run_name=run_name))


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/pooling", methods=['GET', 'POST'])
def akta_pooling(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    analysis_prefix = datapath.analysis_prefix
    
    if request.method == 'GET':
        sample_list = get_samples(exppath)
        fig_html = get_akta_fig(bucket_name, analysis_prefix, origin=True)
        phase_list = get_phase_data(bucket_name, analysis_prefix)
        fraction_list = get_frac_data(bucket_name, analysis_prefix)

        return render_template('pool.html',
                                sample_list=sample_list,
                                akta_fig=fig_html,
                                phase_list=phase_list,
                                fraction_list=fraction_list)

    else: # POST
        frac_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.fraction)
        frac_df["Pool"] = frac_df["Fraction_Start"].copy()

        pool_names = request.form.getlist("poolname")
        region_list = request.form.getlist("fractionRegion")

        pool_dict = {}
        for region, pool_name in zip(region_list, pool_names):
            names = region.split(" - ")
            pool_dict[pool_name] = (names[0], names[1])

        json_save(bucket_name, pool_dict, datapath.pool)
        return redirect(url_for(f"main.akta_fraction", experiment_name=experiment_name, run_name=run_name))


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/fraction", methods=['GET', 'POST'])
def akta_fraction(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    analysis_prefix = datapath.analysis_prefix

    session["experiment_name"] = experiment_name
    session["run_name"] = run_name

    if request.method == 'GET':
        sample_list = get_samples(exppath)
        fig_html = get_akta_fig(bucket_name, analysis_prefix)

        if gcs_utils.blob_exists(bucket_name, datapath.show):
            show_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.show)
        else:
            fraction_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.fraction)
            show_df = fraction_df.copy()
            if gcs_utils.blob_exists(bucket_name, datapath.pool):
                pool_json_str = gcs_utils.download_blob_as_string(bucket_name, datapath.pool)
                pool_dict = json.loads(pool_json_str)
                for name, (start, end) in pool_dict.items():
                    show_df = pv.pycorn.utils.pooling_fraction(fraction_df, start=start, end=end, name=name)
            else:
                show_df["Pool"] = ""
            show_df["Name"] = show_df["Fraction_Start"]
            show_df["Show"] = True
        
        gcs_utils.dataframe_to_gcs_csv(show_df, bucket_name, datapath.show)

        fraction_list = []
        for i, row in show_df.iterrows():
            fraction_list.append({"index": i,
                                  "name": row["Name"],
                                  "pool": row["Pool"],
                                  "show": row["Show"],
                                  "color": row["Color_code"]})
            
        return render_template('fraction.html',
                                sample_list=sample_list,
                                akta_fig=fig_html, 
                                fraction_list=fraction_list)

    if request.method == 'POST':
        colors = request.form.getlist("color")
        names = request.form.getlist("fraction_name")
        shows = [int(s) for s in request.form.getlist("show")]

        show_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.show)
        show_df["Color_code"] = colors
        show_df["Name"] = names
        show_df["Show"] = False
        show_df.loc[shows, "Show"] = True
        show_df = show_df.fillna("")
        gcs_utils.dataframe_to_gcs_csv(show_df, bucket_name, datapath.show)

        config_str = gcs_utils.download_blob_as_string(bucket_name, datapath.config)
        config = json.loads(config_str)

        Fraction.query.filter_by(run_id=config["run_id"]).delete()
        db.session.commit()

        for id, row in show_df.iterrows():
            fraction = Fraction(run_id=config["run_id"],
                                fraction_id=id,
                                name=row["Name"])
            db.session.add(fraction)
            db.session.commit()

    return redirect(url_for("main.show_akta", experiment_name=experiment_name, run_name=run_name))


@main.route("/reload_pool", methods=["GET"])
def reload_pool():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    bucket_name = current_app.config['GCS_BUCKET_NAME']

    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]

    if gcs_utils.blob_exists(bucket_name, datapath.show):
        gcs_utils.delete_blob(bucket_name, datapath.show)

    return redirect(url_for(f"main.akta_fraction", experiment_name=experiment_name, run_name=run_name))



@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/check", methods=["GET", "POST"])
def page_check(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    image_path = datapath.raw
    config_path = datapath.config

    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"

    sample_list = get_samples(exppath)
    config = {}

    if gcs_utils.blob_exists(bucket_name, config_path):
        config_str = gcs_utils.download_blob_as_string(bucket_name, config_path)
        config = json.loads(config_str)

    if request.method == 'GET':
        lane_width = config.get("lane_width", 45)
        margin = config.get("margin", 0.2)
    else: # POST
        lane_width = request.form.get('width-slider', 45)
        margin = request.form.get('margin-slider', 0.2)

    config["lane_width"] = lane_width
    config["margin"] = margin

    json_save(bucket_name, config, config_path)

    fig_html = get_page_fig(bucket_name, image_path, lane_width=lane_width, margin=margin)
        
    return render_template('check.html',
                           sample_list=sample_list,
                           page_fig=fig_html,
                           lane_width=lane_width,
                           margin=margin)


@main.route(f"/save_page", methods=["GET"])
def save_page():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    type = session["type"]
    return redirect(url_for(f"main.page_annotate",experiment_name=experiment_name,run_name=run_name))




@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/annotate", methods=["GET","POST"])
def page_annotate(experiment_name,run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]
    image_path = datapath.raw
    config_path = datapath.config
    analysis_prefix = exppath.analysis_prefix

    sample_list = get_samples(exppath)
    config_str = gcs_utils.download_blob_as_string(bucket_name, config_path)
    config = json.loads(config_str)

    # Helper function to find a file by suffix in a "directory"
    def find_first_blob_with_suffix(prefix, suffix):
        all_blobs = gcs_utils.list_blobs_with_prefix(bucket_name, prefix)
        for blob in all_blobs:
            if blob.endswith(suffix):
                return blob
        return None

    pool_path = find_first_blob_with_suffix(analysis_prefix, "pool.json")
    fraction_path = find_first_blob_with_suffix(analysis_prefix, "fraction.csv")

    if fraction_path:
        fraction_prefix = os.path.dirname(fraction_path)
        fraction_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, fraction_path)
        fraction_df["pool_name"] = fraction_df["Fraction_Start"].copy()
        if pool_path:
            pool_str = gcs_utils.download_blob_as_string(bucket_name, pool_path)
            pool_dict = json.loads(pool_str)
            for name, values in pool_dict.items():
                start_index = fraction_df[fraction_df['Fraction_Start'] == values[0]].index[0]
                end_index = fraction_df[fraction_df['Fraction_Start'] == values[1]].index[0]
                fraction_df.loc[start_index:end_index, 'pool_name'] = name
            suggest_list = list(set(fraction_df["pool_name"].to_list()))
        else:
            suggest_list = list(set(fraction_df["Fraction_Start"].to_list()))
    else:
        suggest_list = [str(n) for n in range(1, 16)]

    if gcs_utils.blob_exists(bucket_name, datapath.annotation):
        df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.annotation)
    else:
        df = make_page_df(bucket_name, datapath.analysis_prefix, datapath.raw)

    df = df.fillna("")

    lane_list = []
    for i, row in df.iterrows():
        lane_list.append({"index": row["Lane"],
                          "name": row["Name"],
                          "group": row["Group"],
                          "subgroup": row["SubGroup"],
                          "color": row["Color_code"]})
        
    fig_html = get_page_fig4annotate(bucket_name, image_path, config, df)

    if request.method == 'POST':
        colors = request.form.getlist("color")
        names = request.form.getlist("lane_name")
        groups = request.form.getlist("lane_group")
        subgroups = request.form.getlist("lane_subgroup")

        if gcs_utils.blob_exists(bucket_name, datapath.annotation):
            df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.annotation, index_col=0)
        else:
            df = make_page_df(bucket_name, datapath.analysis_prefix, datapath.raw)

        df["Color_code"] = colors
        df["Name"] = names
        df["Group"] = groups
        df["SubGroups"] = subgroups
        df = df.fillna("")

        gcs_utils.dataframe_to_gcs_csv(df, bucket_name, datapath.annotation)
        return redirect(url_for("main.page_marker", experiment_name=experiment_name, run_name=run_name))

    elif request.method == 'GET':
        return render_template('annotate.html',
                               experiment_name=experiment_name,
                               sample_list=sample_list,
                               page_fig=fig_html,
                               lane_list=lane_list,
                               suggest_list=suggest_list)


@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/marker", methods=["GET", "POST"])
def page_marker(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]

    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"
    
    sample_list = get_samples(exppath)
    config = get_page_config(bucket_name, datapath.analysis_prefix)

    lane_width = config.get("lane_width", 45)
    margin = config.get("margin", 0.2)

    fig_html = get_page_fig(bucket_name, datapath.raw, lane_width=lane_width, margin=margin)
    marker_ids = get_page_lane_ids(bucket_name, datapath.raw, lane_width=lane_width, margin=margin)
    
    if request.method == 'GET':
        lane_id = config.get("marker", {}).get("id", 0)
    else: # POST
        lane_id = request.form.get('marker_id', 0)

    # Ensure marker key exists
    if "marker" not in config:
        config["marker"] = {}
    config["marker"]["id"] = lane_id
    
    json_save(bucket_name, config, datapath.config)
    
    marker_html, peak_n = marker_check(bucket_name, datapath.analysis_prefix, datapath.raw, lane_id=int(lane_id))

    peak_list = []
    annotations = config["marker"].get("annotate", [])
    for i in range(len(peak_n)):
        peak_list.append({"id": i, "kDa": annotations[i] if i < len(annotations) else ""})

    return render_template('marker.html',
                           experiment_name=experiment_name,
                           sample_list=sample_list,
                           page_fig=fig_html,
                           marker_fig=marker_html,
                           peak_list=peak_list,
                           lane_id=int(lane_id),
                           marker_ids=marker_ids)


@main.route(f"/save_marker", methods=["POST"])
def save_marker():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    bucket_name = current_app.config['GCS_BUCKET_NAME']

    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    datapath = exppath.data[run_name]

    config = get_page_config(bucket_name, datapath.analysis_prefix)
    config["marker"]["annotate"] = request.form.getlist("peak")
    json_save(bucket_name, config, datapath.config)

    return redirect(url_for(f"main.show_page", experiment_name=experiment_name, run_name=run_name))


@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/show", methods=["GET", "POST"])
def show_page(experiment_name, run_name):
    bucket_name = current_app.config['GCS_BUCKET_NAME']
    exppath = ExperimentPath(bucket_name=bucket_name, experiment_name=experiment_name)
    sample_list = get_samples(exppath)
    datapath = exppath.data[run_name]

    config = get_page_config(bucket_name, datapath.analysis_prefix)

    if gcs_utils.blob_exists(bucket_name, datapath.annotation):
        df = gcs_utils.gcs_csv_to_dataframe(bucket_name, datapath.annotation, index_col=0)
        fig_html = show_page_full(bucket_name, datapath.raw, config, df)
    elif config.get("lane_width"):
        fig_html = get_page_fig(bucket_name, datapath.raw, lane_width=int(config["lane_width"]), margin=float(config["margin"]))
    else:
        fig_html = get_page_fig(bucket_name, datapath.raw, lane_width=44, margin=0.2)

    info = sampling_data(datapath)

    return render_template(f"show_page.html",
                           experiment_name=experiment_name,
                           sample_list=sample_list,
                           page_fig=fig_html,
                           info=info)



