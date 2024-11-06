import os
from glob import glob
import proteovis as pv
import plotly.io as pio
import pandas as pd
import json


def get_akta_data(path):

        akta_data = pv.pycorn.load_uni_zip(path)
        
        akta_columns = list(akta_data.keys())

        use_akta_columns = [c for c in akta_columns if "UV" in c] + \
                           [ 'Cond', 'Conc B', 'pH'] + \
                           ['System flow', 'Sample flow'] + \
                           ['PreC pressure', 'System pressure', 'Sample pressure']
        
        hidden_columns =  ["Run Log",'Fractions','Injection']
        
        akta_df = pv.pycorn.utils.get_series_from_data(akta_data,use_akta_columns+hidden_columns)
        frac_df = pv.pycorn.utils.get_fraction_rectangle(akta_df)
        phase_df = pv.pycorn.utils.find_phase(akta_df)

        akta_fig = pv.graph.unicorn_ploty_graph(akta_df)


        return akta_df,frac_df,phase_df,akta_fig


def get_page_image(path,lane_width=44,margin=0.2):
        page = pv.pypage.PageImage(path,lane_width=lane_width,margin=margin)
        page_fig = page.check_image()
        return page_fig


def get_page_lane_ids(path,lane_width=44,margin=0.2):
        page = pv.pypage.PageImage(path,lane_width=lane_width,margin=margin)
        return list(range(len(page.lanes)))


def sampling_data(dir):
        name = os.path.basename(dir)

        image_path = os.path.join(dir[1:],"icon.png").replace("\\","/")
        file_type_binary = os.path.exists(os.path.join(dir,"all_data.csv"))
        if file_type_binary:
                file_type = "AKTA"
        else:
                file_type = "PAGE"

        return {"image_path":image_path,"name":name,"file_type":file_type}


def get_samples(dir):
    analysis_dirs = glob(os.path.join(dir,"*"))

    sample_list = []

    for dir in analysis_dirs:
        sample_dic = sampling_data(dir)
        sample_list.append(sample_dic)

    return sample_list


def get_akta_fig(dir,first="UV 1_280",second="Cond",third=None,forth=None):
    akta_path = os.path.join(dir, f"all_data.csv")
    frac_path = os.path.join(dir, f"fraction.csv")
    phase_path = os.path.join(dir, f"phase.csv")

    akta_df = pd.read_csv(akta_path,index_col=0)
    frac_df = pd.read_csv(frac_path,index_col=0)
    phase_df = pd.read_csv(phase_path,index_col=0).fillna("")

    fig = pv.graph.unicorn_ploty_graph(akta_df,first=first)

    fig,use_color_palette = pv.graph.annotate_fraction(fig,frac_df,phase_df)

    fig.update_layout(
           width=900,
           height=600,
           autosize=False
    )


    fig_html = pio.to_html(fig,full_html=False)
    

    return fig_html


def get_page_fig(image_path,lane_width=50,margin=0.2):
    fig = get_page_image(image_path,lane_width=lane_width,margin=margin)

    fig.update_layout(
           width=900,
           height=600
    )

    fig_html = pio.to_html(fig,full_html=False)

    return fig_html



def get_phase_data(dir):
        phase_path = os.path.join(dir, f"phase.csv")
        phase_df = pd.read_csv(phase_path,index_col=0)
        phase_df = phase_df.fillna("")

        phase_data = []

        for index, row in phase_df.iterrows():
                phase_data.append(
                        {"index": index,
                        "phase": row["Phase"],
                        "color": row["Color_code"]}
                )

        return phase_data

def get_phase_df(dir):
        phase_path = os.path.join(dir, f"phase.csv")
        return pd.read_csv(phase_path,index_col=0)


def get_frac_data(dir):
        frac_path = os.path.join(dir, f"fraction.csv")
        frac_df = pd.read_csv(frac_path,index_col=0)
        fraction_list = frac_df["Fraction_Start"].to_list()

        return fraction_list

def get_page_config(dir):
    config_file = os.path.join(dir,"config.json").replace("\\","/")
    config = json.load(open(config_file))

    return config



def marker_check(dir,image_path,lane_id):
        
        config = get_page_config(dir)
        page = pv.pypage.PageImage(image_path,
                                        lane_width=int(config["lane_width"]),
                                        margin=float(config["margin"]))

        marker = page.get_lane(index=lane_id,start=0).astype(float)
        marker = pv.pypage.Marker(marker)

        fig = marker.check()

        fig.update_layout(
        width=200,
        height=500
        )

        fig_html = pio.to_html(fig,full_html=False)

        return fig_html,marker.peak_index


def make_page_df(dir,image_path):
        config = get_page_config(dir)
        page = pv.pypage.PageImage(image_path,
                                        lane_width=int(config["lane_width"]),
                                        margin=float(config["margin"]))
        return page.get_df()



class ExperimentPath:
      def __init__(self,header,experiment):
            self.experiment = os.path.join(header, experiment)
            self.analysis = os.path.join(self.experiment, "analysis")
            self.raw = os.path.join(self.experiment, "raw_data")
            self.data = {}


            data_folders = glob(f"{self.analysis}/*")

            for folder in data_folders:
                name = os.path.basename(folder)
                file_type_binary = os.path.exists(os.path.join(folder,"all_data.csv"))
                if file_type_binary:
                        data_type = "AKTA"
                else:
                        data_type = "PAGE"
                
                self.data[name] = DataPath(self.experiment,name,data_type=data_type)



class DataPath:
        def __init__(self,experiment,name,data_type):
                self.analysis = os.path.join(experiment, "analysis", name)
                self.experiment = experiment
                self.name = name
                self.data_type = data_type

                if data_type == "AKTA":
                        self.file_type = "zip"
                        self.fraction = os.path.join(self.analysis, "fraction.csv")
                        self.all_data = os.path.join(self.analysis, "all_data.csv")
                        self.phase = os.path.join(self.analysis, "phase.csv")
                else:
                        self.file_type = "PAGE"
                        self.config = os.path.join(self.analysis, "config.json").replace("\\","/")
                        self.annotation = os.path.join(self.analysis, "annotation.csv")
                
                self.raw = os.path.join(self.experiment, "raw_data",f"{name}.jpg")
                self.icon = os.path.join(self.analysis, "icon.png")


def json_save(dict,path):
       with open(path, 'wt') as f:
        json.dump(dict, f, indent=2, ensure_ascii=False)


def show_page_full(image_path,config,lane_path=None):
        lane_width = int(config["lane_width"])
        margin = float(config["margin"])

        page = pv.pypage.PageImage(image_path,lane_width=lane_width,margin=margin)

        marker = page.get_lane(index=int(config["marker"]["id"]),start=0).astype(float)
        marker = pv.pypage.Marker(marker)
        marker.annotate(config["marker"]["annotate"])
        

        if lane_path:
                fig = page.annotated_imshow(use_color_palette,rectangle=True)
        
        else:
               fig = page.check_image()

        fig = pv.pypage.write_marker(fig,marker)

        fig.update_layout(
                width=900,
                height=600
        )

        fig_html = pio.to_html(fig,full_html=False)

        return fig_html


def get_page_fig4annotate(image_path,config,df):
        lane_width = int(config["lane_width"])
        margin = float(config["margin"])

        page = pv.pypage.PageImage(image_path,lane_width=lane_width,margin=margin)

        page.annotate_lanes(df["Name"].values.tolist())
        page.palette = df["Color_code"].values.tolist()

        palette = {}

        fig = page.annotated_imshow(palette,rectangle=True)

        fig.update_layout(
                width=900,
                height=600
        )

        fig_html = pio.to_html(fig,full_html=False)

        return fig_html

