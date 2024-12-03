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


def sampling_data(datapath):

        return {"experiment":datapath.experiment_name,
               "icon":datapath.icon,
                "name":datapath.name,
                "data_type":datapath.data_type}


def get_samples(exppath):
    sample_list = []

    for _,datapath in exppath.data.items():
        sample_dic = sampling_data(datapath)
        sample_list.append(sample_dic)

    return sample_list


def get_akta_fig(dir,first="UV 1_280",origin=False):
    akta_path = os.path.join(dir, f"all_data.csv")
    frac_path = os.path.join(dir, f"fraction.csv")
    show_path = os.path.join(dir, f"show.csv")
    phase_path = os.path.join(dir, f"phase.csv")

    akta_df = pd.read_csv(akta_path,index_col=0)
    if os.path.exists(show_path) & (not origin):
           frac_df = pd.read_csv(show_path,index_col=0)
           frac_df["Fraction_Start"] = frac_df["Name"]
           annotations = frac_df[frac_df["Show"]]["Fraction_Start"].values.tolist()
    else:
           frac_df = pd.read_csv(frac_path,index_col=0)
           annotations = frac_df["Fraction_Start"].values.tolist()

    phase_df = pd.read_csv(phase_path,index_col=0).fillna("")

    fig = pv.graph.unicorn_ploty_graph(akta_df,first=first)

    fig,use_color_palette = pv.graph.annotate_fraction(fig,frac_df,phase_df,annotations=annotations)

    return fig2html(fig,name="akta")


def get_page_fig(image_path,lane_width=50,margin=0.2):
    fig = get_page_image(image_path,lane_width=int(lane_width),margin=float(margin))

    return fig2html(fig,name="page")



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
        frac_df = get_frac_df(dir)
        fraction_list = frac_df["Fraction_Start"].to_list()

        return fraction_list

def get_frac_df(dir,data=None):
        if not data:
                frac_path = os.path.join(dir, f"fraction.csv")
        elif data=="show":
                frac_path = os.path.join(dir, f"show.csv")
        else:NameError
        frac_df = pd.read_csv(frac_path,index_col=0).fillna("")
        return frac_df



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
            self.experiment_name = experiment
            self.analysis = os.path.join(self.experiment, "analysis")
            self.raw = os.path.join(self.experiment, "raw_data")
            self.worksheet = os.path.join(self.experiment, "worksheet")
            self.data = {}
            self.worksheets = {}


            data_folders = glob(f"{self.analysis}/*")
            worksheet_datas = glob(f"{self.worksheet}/*")

            for folder in data_folders:
                name = os.path.basename(folder.replace("\\","/"))
                
                file_type_binary = os.path.exists(os.path.join(folder,"all_data.csv"))
                if file_type_binary:
                        data_type = "AKTA"
                else:
                        data_type = "PAGE"
                
                self.data[name] = DataPath(self.experiment,self.experiment_name,name,data_type=data_type)
            
            for worksheet in worksheet_datas:
                name = os.path.basename(worksheet)[:-5]
                print(name)
                self.worksheets[name] = os.path.join(self.worksheet,
                                                     f"{name}.json"
                                                     ).replace("\\","/")



class DataPath:
        def __init__(self,experiment,experiment_name,name,data_type):
                self.experiment = experiment
                self.experiment_name = experiment_name
                self.analysis = os.path.join(experiment, "analysis", name)
                self.name = name
                self.data_type = data_type

                if data_type == "AKTA":
                        self.file_type = "zip"
                        self.fraction = os.path.join(self.analysis, "fraction.csv")
                        self.all_data = os.path.join(self.analysis, "all_data.csv")
                        self.phase = os.path.join(self.analysis, "phase.csv")
                        self.pool = os.path.join(self.analysis, "pool.json").replace("\\","/")
                        self.show = os.path.join(self.analysis, "show.csv")
                        self.config = os.path.join(self.analysis, "config.json").replace("\\","/")
                else:
                        self.file_type = "PAGE"
                        self.config = os.path.join(self.analysis, "config.json").replace("\\","/")
                        self.annotation = os.path.join(self.analysis, "annotation.csv")
                        
                        config = json.load(open(self.config))
                        ext = config['ext']
                        self.raw = os.path.join(self.experiment, "raw_data",f"{name}{ext}")
                self.icon = "/".join(os.path.join(self.analysis, "icon.png").replace("\\","/").split("/")[2:])


def json_save(dict,path):
       with open(path, 'wt') as f:
        json.dump(dict, f, indent=2, ensure_ascii=False)


def show_page_full(image_path,config,df=None):
        df = df.fillna("")

        lane_width = int(config["lane_width"])
        margin = float(config["margin"])

        page = pv.pypage.PageImage(image_path,lane_width=lane_width,margin=margin)

        page.annotate_lanes(df["Name"].values.tolist())
        page.palette = df["Color_code"].values.tolist()

        palette = {}

        

        marker = page.get_lane(index=int(config["marker"]["id"]),start=0).astype(float)
        marker = pv.pypage.Marker(marker)
        marker.annotate(config["marker"]["annotate"])
        

        if df is df:
               fig = page.annotated_imshow(palette,rectangle=True)
        
        else:
               fig = page.check_image()

        fig = pv.pypage.write_marker(fig,marker)



        return fig2html(fig,name="page")


def fig2html(fig,name="image"):
        fig.update_layout(
                width=900,
                height=600
        )

        config = {
                'toImageButtonOptions': {
                'format': 'svg', # one of png, svg, jpeg, webp
                'filename': name,
                'width': 900,
                'height': 600,
                'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
                }
                }

        fig_html = pio.to_html(fig,full_html=False,config=config)

        return fig_html


def get_page_fig4annotate(image_path,config,df):
        lane_width = int(config["lane_width"])
        margin = float(config["margin"])

        page = pv.pypage.PageImage(image_path,lane_width=lane_width,margin=margin)

        page.annotate_lanes(df["Name"].values.tolist())
        page.palette = df["Color_code"].values.tolist()

        palette = {}

        fig = page.annotated_imshow(palette,rectangle=True)

        return fig2html(fig,name="page")


def fraction_pooling(df):
       pool_df = df.copy()

       pool_df['From'] = pool_df.groupby('Pool')['Name'].transform(lambda x: ';'.join(x))
       pool_df = pool_df.drop_duplicates(subset=['Pool', 'From'])
       pool_df = pool_df.drop("Name",axis=1)

       pool_df = pool_df.rename(columns={"Pool":"Name"})
       
       return pool_df

