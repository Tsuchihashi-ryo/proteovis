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

import proteovis as pv
from utils import *
from models import *
from forms import *

pio.orca.config.executable = 'C:/Users/jb60386/AppData/Local/Programs/orca/orca.exe'

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

        new_experiment=Experiment(name=experiment_name,
                                  user_id=user_name,
                                  project_code=project_code)

        db.session.add(new_experiment)
        db.session.commit()

        #today_str = datetime.now().strftime('%Y%m%d')
        exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
        analysis_dir = exppath.analysis
        raw_dir = exppath.raw
        analysis_dir = exppath.analysis
        worksheet_dir = exppath.worksheet

        try:
            os.makedirs(raw_dir, exist_ok=False) # exist_ok=Falseでエラーを発生させる
            os.makedirs(analysis_dir, exist_ok=False)
            os.makedirs(worksheet_dir, exist_ok=False)
        except FileExistsError:
            return render_template('new_experiment.html', error="Error: A folder with that name already exists for today. Please choose a different experiment name.")


        files = request.files.getlist('files[]')
 
        if files:
            for file in files:
                print(file.filename)
                if file.filename:
                    filename = os.path.join(raw_dir, file.filename)
                    file.save(filename)
                    print(f"Uploaded file: {filename}")

        print(f"Experiment Name: {experiment_name}")
        print(f"User Name: {user_name}")
        print(f"Project Code: {project_code}")
      
        rawfile_list = glob(os.path.join(raw_dir,"*"))


        for path in rawfile_list:
            name = os.path.basename(path).split(".")[0]
            data_dir = os.path.join(analysis_dir,name)
            
            try:
                os.makedirs(data_dir,exist_ok=False)
            except FileExistsError:
                return render_template('index.html', error="Error: A folder with that name already exists for today. Please choose a different file.")

            if path[-3:] == "zip":
                akta_df,frac_df,phase_df,akta_fig = get_akta_data(path)
                akta_df.to_csv(os.path.join(data_dir,"all_data.csv"))
                frac_df.to_csv(os.path.join(data_dir,"fraction.csv"))
                phase_df.to_csv(os.path.join(data_dir,"phase.csv"))
                test = akta_fig.to_html(full_html=False)
                #return render_template('chromatography.html',chromatogram=test)
                akta_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")

                run = Run(experiment_id=new_experiment.id,
                          name=name,
                          type="AKTA")
                
                db.session.add(run)
                db.session.commit()

                config = {"run_id":run.id}
                json_save(config,os.path.join(data_dir,"config.json"))


            elif path[-3:] in ["png","jpg","iff","tif"]:
                page_fig = get_page_image(path)
                ext = os.path.splitext(path)[-1]
                page_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")
                run = Run(experiment_id=new_experiment.id,
                          name=name,
                          type="PAGE")
                
                db.session.add(run)
                db.session.commit()
                
                config = {"ext":ext,"run_id":run.id}
                json_save(config,os.path.join(data_dir,"config.json"))

                
            
            
                

    
        return redirect(url_for(f"main.experiment",experiment_name=experiment_name))#select(experiment_name)

    return render_template('new_experiment.html', error=None,user_name=current_user.name) #エラーメッセージをクリア



@main.route("/experiment/<experiment_name>/upload", methods=["POST"])
def upload(experiment_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                        experiment=experiment_name)
    experiment_id = Experiment.query.filter_by(name=experiment_name).first().id


    raw_dir = exppath.raw
    analysis_dir = exppath.analysis
    worksheet_dir = exppath.worksheet

    file = request.files.get('file')

    print(file.filename)
    if file.filename:
        filename = os.path.join(raw_dir, file.filename)
        file.save(filename)
        print(f"Uploaded file: {filename}")


    rawfile = filename


    for path in [rawfile]:
        name = os.path.basename(path).split(".")[0]
        data_dir = os.path.join(analysis_dir,name)
        
        try:
            os.makedirs(data_dir,exist_ok=False)
        except FileExistsError:
            return render_template('index.html', error="Error: A folder with that name already exists for today. Please choose a different file.")

        if path[-3:] == "zip":
            akta_df,frac_df,phase_df,akta_fig = get_akta_data(path)
            akta_df.to_csv(os.path.join(data_dir,"all_data.csv"))
            frac_df.to_csv(os.path.join(data_dir,"fraction.csv"))
            phase_df.to_csv(os.path.join(data_dir,"phase.csv"))
            test = akta_fig.to_html(full_html=False)
            #return render_template('chromatography.html',chromatogram=test)
            akta_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")

            run = Run(experiment_id=experiment_id,
                        name=name,
                        type="AKTA")
            
            db.session.add(run)
            db.session.commit()

            config = {"run_id":run.id}
            json_save(config,os.path.join(data_dir,"config.json"))


        elif path[-3:] in ["png","jpg","iff","tif"]:
            page_fig = get_page_image(path)
            ext = os.path.splitext(path)[-1]
            page_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")
            run = Run(experiment_id=experiment_id,
                        name=name,
                        type="PAGE")
            
            db.session.add(run)
            db.session.commit()
            
            config = {"ext":ext,"run_id":run.id}
            json_save(config,os.path.join(data_dir,"config.json"))


    return redirect(url_for(f"main.experiment",experiment_name=experiment_name))#select(experiment_name)


@main.route('/open_experiment', methods=['GET'])
def open_experiment():
    #experiments = glob(os.path.join(current_app.config['UPLOAD_FOLDER'],"*"))
    experiments = Experiment.query.all()

    exp_dic = {}

    for exp in experiments:
        exp_name = exp.name
        exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                                experiment=exp_name)
        #data = list(exppath.data.keys())
        data = [run.name for run in Run.query.filter_by(experiment_id=exp.id).all()]

        exp_dic[exp_name] = ", ".join(data)



    return render_template('open_experiment.html', experiments=exp_dic)


@main.route(f"/experiment/<experiment_name>/delete")
def delete_experiment(experiment_name):
    shutil.rmtree(os.path.join(current_app.config['UPLOAD_FOLDER'],experiment_name))

    return redirect(url_for("main.open_experiment"))



@main.route("/experiment/<experiment_name>/worksheet4akta/<worksheet_name>", methods=["GET", "POST"])
def worksheet4akta(experiment_name,worksheet_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                                experiment=experiment_name)
    experiment_id = Experiment.query.filter_by(name=experiment_name).first().id

    worksheet_dir = exppath.worksheet
    worksheet_path = exppath.worksheets.get(worksheet_name)
    print(worksheet_path)


    if request.method == "GET":
        if worksheet_path:
            json_data = json.load(open(worksheet_path,),)
            data = {
            }
            if json_data.get("program"):
                data["rows"] = list(json_data["program"].values())
            else:
                data["rows"] = [
                        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 1, "percentB": 0, "slopeType": "step", "path": "sample loop", "fractionVol": 0},
                        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 10, "percentB": 50, "slopeType": "gradient", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 5, "percentB": 100, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 3, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        ]
            
            if json_data.get("column_cv"):
                data["cv"] = json_data["column_cv"]
            else:
                data["cv"] = 1

        else: 
            data = {
                "rows":[
                        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 1, "percentB": 0, "slopeType": "step", "path": "sample loop", "fractionVol": 0},
                        {"rate": 1, "length": 5, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 10, "percentB": 50, "slopeType": "gradient", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 5, "percentB": 100, "slopeType": "step", "path": "", "fractionVol": 0},
                        {"rate": 1, "length": 3, "percentB": 0, "slopeType": "step", "path": "", "fractionVol": 0},
                        ],
                "cv":1
            }
        data_json_string = json.dumps(data,)
        return render_template("worksheet4akta.html",data=data_json_string) # index.htmlをレンダリング
    
    
    elif request.method == "POST":
        data = {
            "worksheet_name":request.form.get("worksheet-name"),
            "column_name": request.form.get("column-name"),
            "column_cv": request.form.get("column-cv"),
            "sample_loop_name": request.form.get("sample-loop-name"),
            "sample_loop_volume": request.form.get("sample-loop-volume"),
            "buffer_a1": request.form.get("buffer-a1"),
            "number_a1": request.form.get("number-a1"),
            "a1_ph": request.form.get("a1-ph"),
            "buffer_a2": request.form.get("buffer-a2"),
            "number_a2": request.form.get("number-a2"),
            "a2_ph": request.form.get("a2-ph"),
            "buffer_b1": request.form.get("buffer-b1"),
            "number_b1": request.form.get("number-b1"),
            "b1_ph": request.form.get("b1-ph"),
            "buffer_b2": request.form.get("buffer-b2"),
            "number_b2": request.form.get("number-b2"),
            "b2_ph": request.form.get("b2-ph"),
            "sample_pump_s1": request.form.get("sample-pump-s1"),
            "sample_pump_buffer": request.form.get("sample-pump-buffer"),
        }

        for k,v in data.items():
            try:
                data[k] = float(v)
            except:
                continue

        worksheet_dir = exppath.worksheet

        # プログラムテーブルのデータ抽出 (これは動的なので、少し複雑です)
        rates = np.array(request.form.getlist('rate[]')).astype(float)
        lengths = np.array(request.form.getlist('length[]')).astype(float)
        percentBs = np.array(request.form.getlist('percentB[]')).astype(float)
        slopeTypes = request.form.getlist('slopeType[]')
        paths = request.form.getlist('path[]')
        fractionVols = np.array(request.form.getlist('fractionVol[]')).astype(float)

        program_df = pd.DataFrame(data=dict(
            rate=rates,
            length=lengths,
            percentB=percentBs,
            slopeType=slopeTypes,
            path=paths,
            fractionVol=fractionVols
        ))

        data["program"] = program_df.to_dict(orient="index")
        worksheet_path = os.path.join(os.path.join(worksheet_dir,f"{worksheet_name}.json"))
        json_save(data,worksheet_path)
        data = json.load(open(worksheet_path))
        data_json_string = json.dumps(data,)


        chart_data = {}
        chart_data["rows"] = list(data["program"].values())
        chart_data["cv"] = data["column_cv"]

        chart_data_json_string = json.dumps(chart_data,)

        worksheet = Worksheet(experiment_id=experiment_id,
                              name=worksheet_name,
                              type="AKTA")
        
        db.session.add(worksheet)
        db.session.commit()

        return render_template("worksheet4aktaview.html",
                               data=data_json_string,
                               chart_data=chart_data_json_string)




@main.route(f"/experiment/<experiment_name>")
def experiment(experiment_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis

    sample_list = get_samples(exppath)


    return render_template('template4input.html',experiment_name=experiment_name,sample_list=sample_list)


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/show", methods=["GET"])
def show_akta(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    datapath = exppath.data[run_name]
    
    data_dir = datapath.analysis

    if request.method == 'GET':
        sample_list = get_samples(exppath)

        fig_html = get_akta_fig(data_dir)

    info = sampling_data(datapath)


    return render_template('show_akta.html',
                           experiment_name=experiment_name,
                           sample_list=sample_list,
                           akta_fig=fig_html,
                           info=info)


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/phase", methods=['GET', 'POST'])
def akta(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    data_dir = exppath.data[run_name].analysis

    if request.method == 'GET':
        sample_list = get_samples(exppath)

        fig_html = get_akta_fig(data_dir)

        phase_list = get_phase_data(data_dir)
        #right pannel 

        return render_template('phase.html',sample_list=sample_list,akta_fig=fig_html, phase_list=phase_list) #add right pannel data

    else:
        #df read
        df = get_phase_df(data_dir)

        for i in df.index:
            df.loc[i, "Phase"] = request.form.get(f'phase_{i}')
            df.loc[i,"Color_code"] = request.form.get(f'color_{i}')

        df.to_csv(os.path.join(data_dir,"phase.csv"),na_rep="A")
        
        return redirect(url_for(f"main.akta_pooling",experiment_name=experiment_name, run_name=run_name))


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/pooling", methods=['GET', 'POST'])
def akta_pooling(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                                experiment=experiment_name)
    
    datapath = exppath.data[run_name]
    data_dir = datapath.analysis
    

    if request.method == 'GET':
        sample_list = get_samples(exppath)
        fig_html = get_akta_fig(data_dir, origin=True)
        phase_list = get_phase_data(data_dir)
        #right pannel 
        fraction_list = get_frac_data(data_dir)

        return render_template('pool.html',
                                sample_list=sample_list,
                                akta_fig=fig_html, 
                                phase_list=phase_list,
                                fraction_list=fraction_list) #add right pannel data
        #return render_template('pool.html')


    else: #pattern of POST
        frac_path = os.path.join(data_dir, "fraction.csv")
        frac_df = pd.read_csv(frac_path,index_col=0)
        frac_df["Pool"] = frac_df["Fraction_Start"].copy()

        pool_names = request.form.getlist("poolname",)
        region_list = request.form.getlist("fractionRegion")

        pool_dict = {}
        
        for region, pool_name in zip(region_list,pool_names):
            names= region.split(" - ")
            pool_dict[pool_name]=(names[0],names[1])

        json_save(pool_dict,datapath.pool)

        return redirect(url_for(f"main.akta_fraction",experiment_name=experiment_name, run_name=run_name))


@main.route(f"/experiment/<experiment_name>/AKTA/<run_name>/fraction", methods=['GET', 'POST'])
def akta_fraction(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                            experiment=experiment_name) 
    datapath = exppath.data[run_name]
    data_dir = datapath.analysis

    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    

    if request.method == 'GET':
        sample_list = get_samples(exppath)
        fig_html = get_akta_fig(data_dir)
        fraction_df = get_frac_df(data_dir)


        if os.path.exists(datapath.show):
            show_df = get_frac_df(data_dir,"show")


        else:
            show_df = get_frac_df(data_dir)
            if os.path.exists(datapath.pool):
                pool_dict = json.load(open(datapath.pool))

                for name,(start,end) in pool_dict.items():
                    show_df = pv.pycorn.utils.pooling_fraction(fraction_df,start=start,end=end,name=name)
            
            else:
                show_df["Pool"] = ""

            show_df["Name"] = show_df["Fraction_Start"]
            show_df["Show"] = True
        

        show_df.to_csv(datapath.show)


        fraction_list = []
        for i,row in show_df.iterrows():
            fraction_list.append({"index":i,
                            "name":row["Name"],
                            "pool":row["Pool"],
                            "show":row["Show"],
                            "color":row["Color_code"]})
            
        return render_template('fraction.html',
                                sample_list=sample_list,
                                akta_fig=fig_html, 
                                fraction_list=fraction_list)
        

    if request.method == 'POST':
        colors = request.form.getlist("color")
        names = request.form.getlist("fraction_name")
        shows = [int(s) for s in request.form.getlist("show")]

        show_df = get_frac_df(data_dir,"show")

        show_df["Color_code"] = colors
        show_df["Name"] = names
        show_df["Show"] = False
        show_df.loc[shows,"Show"] = True

        show_df = show_df.fillna("")

        show_df.to_csv(datapath.show)

        config = json.load(open(datapath.config))


        Fraction.query.filter_by(run_id=config["run_id"]).delete()
        db.session.commit()

        for id,row in show_df.iterrows():

            fraction = Fraction(run_id=config["run_id"],
                                fraction_id=id,
                                name=row["Name"],)
            
            db.session.add(fraction)
            db.session.commit()

    return redirect(url_for("main.show_akta", experiment_name=experiment_name,run_name=run_name))


@main.route("/reload_pool",methods=["GET"])
def reload_pool():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]

    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                            experiment=experiment_name) 
    datapath = exppath.data[run_name]

    os.remove(datapath.show)

    return redirect(url_for(f"main.akta_fraction",experiment_name=experiment_name, run_name=run_name))



@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/check", methods=["GET","POST"])
def page_check(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                            experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    data_dir = exppath.data[run_name].analysis
    raw_dir = exppath.raw

    image_path = exppath.data[run_name].raw
    config_file = exppath.data[run_name].config


    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"

    sample_list = get_samples(exppath)


    if request.method == 'GET':
        

        if os.path.exists(config_file):
            config = json.load(open(config_file))
            
            if config.get("lane_width"):
                lane_width = config["lane_width"]
                margin = config["margin"]
            else:
                lane_width = 45
                margin = 0.2

        else:
            lane_width = 45
            margin = 0.2


    else:
        lane_width = request.form.get('width-slider')
        margin = request.form.get('margin-slider')
        fig_html = get_page_fig(image_path,lane_width=int(lane_width),margin=float(margin))

    if os.path.exists(config_file):
        config = json.load(open(config_file))
    
    else:
        config = []

    config["lane_width"] = lane_width
    config["margin"] = margin

    fig_html = get_page_fig(image_path,lane_width=lane_width,margin=margin)
        
    with open(config_file, 'wt') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        
    return render_template('check.html',sample_list=sample_list,page_fig=fig_html,lane_width=lane_width,margin=margin)


@main.route(f"/save_page", methods=["GET"])
def save_page():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    type = session["type"]
    return redirect(url_for(f"main.page_annotate",experiment_name=experiment_name,run_name=run_name))




@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/annotate", methods=["GET","POST"])
def page_annotate(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'],
                            experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    datapath = exppath.data[run_name]
    image_path = datapath.raw
    config_file = datapath.config
    sample_list = get_samples(exppath)
    config = json.load(open(config_file))

    def find_data(parent_directory, target_data):
        dir_path = Path(parent_directory)
        for file_path in dir_path.rglob(target_data):
            return True, str(file_path)
        return False, ""

    bool_pool = find_data(analysis_dir, "pool.json")
    bool_fraction = find_data(analysis_dir, "fraction.csv")
    print (bool_pool, bool_fraction)

    if bool_fraction[0]:
        fraction_df = get_frac_df(bool_fraction[1].replace("fraction.csv",""))
        fraction_df["pool_name"] = fraction_df["Fraction_Start"].copy()
        if bool_pool[0]:
            with open(bool_pool[1], 'r') as f:
                pool_dict = json.load(f)
            
            for name, values in zip(list(pool_dict.keys()), pool_dict.values()):

                start_index = fraction_df[fraction_df['Fraction_Start'] == values[0]].index[0]
                end_index = fraction_df[fraction_df['Fraction_Start'] == values[1]].index[0]

                # 'start'から'end'までの範囲に'test'を入力
                fraction_df.loc[start_index:end_index, 'pool_name'] = name

            suggest_list = list(set(fraction_df["pool_name"].to_list()))
        else:
            suggest_list = list(set(fraction_df["Fraction_Start"].to_list()))
    
    else:
        suggest_list = [str(n) for n in range(1,16)]




    if os.path.exists(datapath.annotation):
        df = pd.read_csv(datapath.annotation)
        
    
    else:
        df = make_page_df(datapath.analysis,datapath.raw)

    df = df.fillna("")

    lane_list = []
    for i,row in df.iterrows():
        lane_list.append({"index":row["Lane"],
                        "name":row["Name"],
                        "group":row["Group"],
                        "subgroup":row["SubGroup"],
                        "color":row["Color_code"]})
        
    fig_html = get_page_fig4annotate(image_path,config,df)


    if request.method == 'POST':
        colors = request.form.getlist("color")
        names = request.form.getlist("lane_name")
        groups = request.form.getlist("lane_group")
        subgroups = request.form.getlist("lane_subgroup")

        if os.path.exists(datapath.annotation):
            df = pd.read_csv(datapath.annotation,index_col=0)
        else:
            df = make_page_df(datapath.analysis,datapath.raw)

        df["Color_code"] = colors
        df["Name"] = names
        df["Group"] = groups
        df["SubGroups"] = subgroups

        df = df.fillna("")

        df.to_csv(datapath.annotation)

        return redirect(url_for("main.page_marker",experiment_name=experiment_name,run_name=run_name))

    elif request.method == 'GET':
        return render_template('annotate.html',experiment_name=experiment_name,sample_list=sample_list,page_fig=fig_html,lane_list=lane_list, suggest_list=suggest_list)


@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/marker", methods=["GET","POST"])
def page_marker(experiment_name,run_name):

    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"
    
    datapath = exppath.data[run_name]

    sample_list = get_samples(exppath)


    config = json.load(open(datapath.config))

    lane_width = config["lane_width"]
    margin = config["margin"]

    fig_html = get_page_fig(datapath.raw,lane_width=int(lane_width),margin=float(margin))

    marker_ids = get_page_lane_ids(datapath.raw,lane_width=int(lane_width),margin=float(margin))
    
    config = json.load(open(datapath.config))

    if request.method == 'GET':
        if config.get("marker"):
            lane_id = config["marker"]["id"]
        else:
            lane_id = 0
    
    else:
        lane_id = request.form.get('marker_id')


    if config.get("marker"):
        config["marker"]["id"] = lane_id
    
    else:
        config["marker"] = {"id":lane_id}

    
    json_save(config,datapath.config)
    

    marker_html,peak_n = marker_check(datapath.analysis,datapath.raw,lane_id=int(lane_id))

    peak_list = []


    if config["marker"].get("annotate"):
        for id,(_,peak) in enumerate(zip(peak_n,config["marker"]["annotate"])):
            peak_list.append({"id":id,"kDa":peak})
    
    else:
        for id in range(len(peak_n)):
            peak_list.append({"id":id,"kDa":""})


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
    type = session["type"]

    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    datapath = exppath.data[run_name]

    config = json.load(open(datapath.config))

    config["marker"]["annotate"] = request.form.getlist("peak")

    json_save(config,datapath.config)
    print("gin")


    return redirect(url_for(f"main.show_page",experiment_name=experiment_name,run_name=run_name))



@main.route(f"/experiment/<experiment_name>/PAGE/<run_name>/show", methods=["GET","POST"])
def show_page(experiment_name,run_name):
    exppath = ExperimentPath(header=current_app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    sample_list = get_samples(exppath)
    
    datapath = exppath.data[run_name]

    config = json.load(open(datapath.config))

    if os.path.exists(datapath.annotation):

        df = pd.read_csv(datapath.annotation,index_col=0)

        fig_html = show_page_full(datapath.raw,config,df)

    elif config.get("lane_width"):
        fig_html = get_page_fig(datapath.raw,lane_width=int(config["lane_width"]),margin=float(config["margin"]))
    
    else:
        fig_html = get_page_fig(datapath.raw,lane_width=44,margin=0.2)

    info = sampling_data(datapath)


    return render_template(f"show_page.html",
                           experiment_name=experiment_name,
                           sample_list=sample_list,
                           page_fig=fig_html,
                           info=info)



