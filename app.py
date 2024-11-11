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
from pathlib import Path

pio.orca.config.executable = 'C:/Users/jb60386/AppData/Local/Programs/orca/orca.exe'
app = Flask(__name__,static_folder='./static', static_url_path='/static')
app.secret_key = b'fewgagaehrae'
app.jinja_env.auto_reload = True

UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/new_experiment', methods=['GET', 'POST'])
def new_experiment():
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


            elif path[-3:] in ["png","jpg","iff","tif"]:
                page_fig = get_page_image(path)
                ext = os.path.splitext(path)[-1]
                page_fig.write_image(os.path.join(data_dir,"icon.png"),engine="orca")
                config = {"ext":ext}
                json_save(config,os.path.join(data_dir,"config.json"))
                

    
        return redirect(url_for(f"experiment",experiment_name=experiment_name))#select(experiment_name)

    return render_template('new_experiment.html', error=None) #エラーメッセージをクリア


@app.route('/open_experiment', methods=['GET'])
def open_experiment():
    experiments = glob(os.path.join(app.config['UPLOAD_FOLDER'],"*"))

    exp_dic = {}

    for exp in experiments:
        exp_name = os.path.basename(exp)
        exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                                experiment=exp_name)
        data = list(exppath.data.keys())

        exp_dic[exp_name] = data



    return render_template('open_experiment.html', experiments=exp_dic)



@app.route(f"/experiment/<experiment_name>")
def experiment(experiment_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    analysis_dir = exppath.analysis

    sample_list = get_samples(exppath)


    return render_template('template4input.html',sample_list=sample_list)


@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/show", methods=["GET"])
def show_akta(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                             experiment=experiment_name)
    
    datapath = exppath.data[run_name]
    
    data_dir = datapath.analysis

    if request.method == 'GET':
        sample_list = get_samples(exppath)

        fig_html = get_akta_fig(data_dir)

    info = sampling_data(datapath)


    return render_template('show_akta.html',
                           sample_list=sample_list,
                           akta_fig=fig_html,
                           info=info)


@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/phase", methods=['GET', 'POST'])
def akta(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
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
        
        return redirect(url_for(f"akta_pooling",experiment_name=experiment_name, run_name=run_name))


@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/pooling", methods=['GET', 'POST'])
def akta_pooling(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
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

        return redirect(url_for(f"akta_fraction",experiment_name=experiment_name, run_name=run_name))


@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>/fraction", methods=['GET', 'POST'])
def akta_fraction(experiment_name,run_name):
    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
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

    return redirect(url_for("show_akta", experiment_name=experiment_name,run_name=run_name))


@app.route("/reload_pool",methods=["GET"])
def reload_pool():
    experiment_name = session["experiment_name"]
    run_name = session["run_name"]

    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'],
                            experiment=experiment_name) 
    datapath = exppath.data[run_name]

    os.remove(datapath.show)

    return redirect(url_for(f"akta_fraction",experiment_name=experiment_name, run_name=run_name))



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

        return redirect(url_for("page_marker",experiment_name=experiment_name,run_name=run_name))

    elif request.method == 'GET':
        return render_template('annotate.html',sample_list=sample_list,page_fig=fig_html,lane_list=lane_list, suggest_list=suggest_list)


@app.route(f"/experiment/<experiment_name>/PAGE/<run_name>/marker", methods=["GET","POST"])
def page_marker(experiment_name,run_name):

    exppath = ExperimentPath(header=app.config['UPLOAD_FOLDER'].replace("/","\\"),
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
    
    sample_list = get_samples(exppath)
    
    datapath = exppath.data[run_name]

    config = json.load(open(datapath.config))

    df = pd.read_csv(datapath.annotation,index_col=0)

    fig_html = show_page_full(datapath.raw,config,df)

    info = sampling_data(datapath)


    return render_template(f"show_page.html",
                           sample_list=sample_list,
                           page_fig=fig_html,
                           info=info)



if __name__ == '__main__':
    app.run(port=8000,debug=True)