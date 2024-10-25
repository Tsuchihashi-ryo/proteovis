from flask import Flask, render_template, request, redirect, url_for, session
import os
from datetime import datetime
from glob import glob
import proteovis as pv
import plotly.io as pio
import pandas as pd
import seaborn as sns
from utils import *

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
    exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{experiment_name}")
    analysis_dir = os.path.join(exp_dir, "analysis")

    sample_html = get_samples(analysis_dir)


    return render_template('template.html',files=sample_html)

@app.route(f"/experiment/<experiment_name>/AKTA/<run_name>")
def akta(experiment_name,run_name):
    exp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"{experiment_name}")
    analysis_dir = os.path.join(exp_dir, "analysis")
    data_dir = os.path.join(analysis_dir, f"{run_name}")

    sample_html = get_samples(analysis_dir)

    fig_html = get_akta_fig(data_dir)

    return render_template('template.html',files=sample_html,data=fig_html)





if __name__ == '__main__':
    app.run(port=8000,debug=True)