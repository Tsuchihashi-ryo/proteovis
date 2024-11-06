from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
from glob import glob
import proteovis as pv
import plotly.io as pio
import pandas as pd
import seaborn as sns
from utils import *
import json
import pandas as pd

pio.orca.config.executable = 'C:/Users/jb60764/AppData/Local/Programs/orca/orca.exe'
app = Flask(__name__,static_folder='./static', static_url_path='/static')
app.secret_key = b'fewgagaehrae'
app.jinja_env.auto_reload = True

UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        experiment_name = request.form.get('experiment-name')
        user_name = request.form.get('user-name')
        project_code = request.form.get('project-code')

        #today_str = datetime.now().strftime('%Y%m%d')
        exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{experiment_name}")
        raw_dir = os.path.join(exp_dir, "raw_data")
        analysis_dir = os.path.join(exp_dir, "analysis")

        try:
            os.makedirs(raw_dir, exist_ok=False) # exist_ok=Falseでエラーを発生させる
            os.makedirs(analysis_dir, exist_ok=False)
        except FileExistsError:
            return render_template('index.html', error="Error: A folder with that name already exists for today. Please choose a different experiment name.")


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


            elif path[-3:] in ["png","jpg","iff"]:
                page_fig = get_page_image(path)
                page_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")

    
        return redirect(url_for(f"experiment",experiment_name=experiment_name))#select(experiment_name)

    return render_template('index.html', error=None) #エラーメッセージをクリア


@app.route(f"/experiment/<experiment_name>")
def experiment(experiment_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis

    sample_html = get_samples(analysis_dir)


    return render_template('template.html',files=sample_html)

@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/phase", methods=['GET', 'POST'])
def akta(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    data_dir = exppath.data[run_name].analysis

    if request.method == 'GET':
        sample_list = get_samples(analysis_dir)

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
        
        return redirect(url_for(f"akta_pooling",experiment_name=experiment_name, run_name=run_name))


@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/pooling", methods=['GET', 'POST'])
def akta_pooling(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    data_dir = exppath.data[run_name].analysis
    

    if request.method == 'GET':
        sample_list = get_samples(analysis_dir)
        fig_html = get_akta_fig(data_dir)
        phase_list = get_phase_data(data_dir)
        #right pannel 
        fraction_list = get_frac_data(data_dir)

        return render_template('pool.html',
                               sample_list=sample_list,
                               akta_fig=fig_html, 
                               phase_list=phase_list,
                               fraction_list=fraction_list) #add right pannel data
        #return render_template('pool.html')
        
        
@app.route(f"/experiment/<experiment_name>/PAGE/<run_name>/check", methods=["GET","POST"])
def page_check(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    data_dir = exppath.data[run_name].analysis
    raw_dir = exppath.raw

    image_path = exppath.data[run_name].raw
    config_file = exppath.data[run_name].config


    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"

    sample_list = get_samples(analysis_dir)


    if request.method == 'GET':
        fig_html = get_page_fig(image_path)

        if os.path.exists(config_file):
            config = json.load(open(config_file))
            
            lane_width = config["lane_width"]
            margin = config["margin"]
        
        else:
            lane_width = 45
            margin = 0.2
    
    else:
        lane_width = request.form.get('width-slider')
        margin = request.form.get('margin-slider')
        fig_html = get_page_fig(image_path,lane_width=int(lane_width),margin=float(margin))


    config = {"lane_width":lane_width,
            "margin":margin}
        
    with open(config_file, 'wt') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        
    return render_template('check.html',sample_list=sample_list,page_fig=fig_html,lane_width=lane_width,margin=margin)


@app.route(f"/save_page", methods=["GET"])
def save_page():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    type = session["type"]
    return redirect(url_for(f"page_annotate",experiment_name=experiment_name,run_name=run_name))


@app.route(f"/experiment/<experiment_name>/PAGE/<run_name>/annotate", methods=["GET","POST"])
def page_annotate(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis
    datapath = exppath.data[run_name]

    image_path = exppath.data[run_name].raw
    config_file = exppath.data[run_name].config

    sample_list = get_samples(analysis_dir)
    
    config = json.load(open(config_file))
    

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
 
    return render_template('annotate.html',sample_list=sample_list,page_fig=fig_html,lane_list=lane_list)


@app.route(f"/experiment/<experiment_name>/PAGE/<run_name>/marker", methods=["GET","POST"])
def page_marker(experiment_name,run_name):

    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    session["experiment_name"] = experiment_name
    session["run_name"] = run_name
    session["type"] = "PAGE"
    
    datapath = exppath.data[run_name]

    sample_list = get_samples(exppath.analysis)


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
        for id,peak in enumerate(config["marker"]["annotate"]):
            peak_list.append({"id":id,"kDa":peak})
    
    else:
        for id in range(len(peak_n)):
            peak_list.append({"id":id,"kDa":""})


    return render_template('marker.html',
                           sample_list=sample_list,
                           page_fig=fig_html,
                           marker_fig=marker_html,
                           peak_list=peak_list,
                           lane_id=int(lane_id),
                           marker_ids=marker_ids)


@app.route(f"/save_marker", methods=["POST"])
def save_marker():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]
    type = session["type"]

    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    datapath = exppath.data[run_name]

    config = json.load(open(datapath.config))

    config["marker"]["annotate"] = request.form.getlist("peak")

    json_save(config,datapath.config)


    return redirect(url_for(f"show_page",experiment_name=experiment_name,run_name=run_name))



@app.route(f"/experiment/<experiment_name>/PAGE/<run_name>/show", methods=["GET","POST"])
def show_page(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'].replace("/","\\"),
                             experiment=experiment_name)
    
    sample_list = get_samples(exppath.analysis)
    
    datapath = exppath.data[run_name]

    config = json.load(open(datapath.config))

    fig_html = show_page_full(datapath.raw,config)



    return render_template(f"show_page.html",
                           sample_list=sample_list,
                           page_fig=fig_html)



if __name__ == '__main__':
    app.run(port=8000,debug=True)