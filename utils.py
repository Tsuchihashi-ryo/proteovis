import os
from glob import glob
import proteovis as pv
import plotly.io as pio
import pandas as pd
import json
import gcs_utils
from flask import current_app
from io import BytesIO


def get_akta_data(bucket_name, path):
        file_obj = gcs_utils.download_blob_to_file_object(bucket_name, path)
        akta_data = pv.pycorn.load_uni_zip(file_obj)
        
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


def get_page_image(bucket_name, path, lane_width=44, margin=0.2):
        image_obj = gcs_utils.download_blob_to_file_object(bucket_name, path)
        page = pv.pypage.PageImage(image_obj, lane_width=lane_width, margin=margin)
        page_fig = page.check_image()
        return page_fig


def get_page_lane_ids(bucket_name, path, lane_width=44, margin=0.2):
        image_obj = gcs_utils.download_blob_to_file_object(bucket_name, path)
        page = pv.pypage.PageImage(image_obj, lane_width=lane_width, margin=margin)
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


def get_akta_fig(bucket_name, dir_prefix, first="UV 1_280", origin=False):
    akta_path = f"{dir_prefix}/all_data.csv"
    frac_path = f"{dir_prefix}/fraction.csv"
    show_path = f"{dir_prefix}/show.csv"
    phase_path = f"{dir_prefix}/phase.csv"

    akta_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, akta_path)
    if gcs_utils.blob_exists(bucket_name, show_path) and not origin:
        frac_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, show_path)
        frac_df["Fraction_Start"] = frac_df["Name"]
        annotations = frac_df[frac_df["Show"]]["Fraction_Start"].values.tolist()
    else:
        frac_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, frac_path)
        annotations = frac_df["Fraction_Start"].values.tolist()

    phase_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, phase_path).fillna("")

    fig = pv.graph.unicorn_ploty_graph(akta_df, first=first)
    fig, use_color_palette = pv.graph.annotate_fraction(fig, frac_df, phase_df, annotations=annotations)

    return fig2html(fig, name="akta")


def get_page_fig(bucket_name, image_path, lane_width=50, margin=0.2):
    fig = get_page_image(bucket_name, image_path, lane_width=int(lane_width), margin=float(margin))
    return fig2html(fig, name="page")


def get_phase_data(bucket_name, dir_prefix):
    phase_path = f"{dir_prefix}/phase.csv"
    phase_df = gcs_utils.gcs_csv_to_dataframe(bucket_name, phase_path).fillna("")
    phase_data = []
    for index, row in phase_df.iterrows():
        phase_data.append({
            "index": index,
            "phase": row["Phase"],
            "color": row["Color_code"]
        })
    return phase_data

def get_phase_df(bucket_name, dir_prefix):
    phase_path = f"{dir_prefix}/phase.csv"
    return gcs_utils.gcs_csv_to_dataframe(bucket_name, phase_path)


def get_frac_data(bucket_name, dir_prefix):
    frac_df = get_frac_df(bucket_name, dir_prefix)
    return frac_df["Fraction_Start"].to_list()

def get_frac_df(bucket_name, dir_prefix, data=None):
    if not data:
        frac_path = f"{dir_prefix}/fraction.csv"
    elif data == "show":
        frac_path = f"{dir_prefix}/show.csv"
    else:
        raise NameError("Invalid data type for get_frac_df")
    return gcs_utils.gcs_csv_to_dataframe(bucket_name, frac_path).fillna("")


def get_page_config(bucket_name, dir_prefix):
    config_file = f"{dir_prefix}/config.json"
    json_string = gcs_utils.download_blob_as_string(bucket_name, config_file)
    return json.loads(json_string)



def marker_check(bucket_name, dir_prefix, image_path, lane_id):
    config = get_page_config(bucket_name, dir_prefix)
    image_obj = gcs_utils.download_blob_to_file_object(bucket_name, image_path)
    page = pv.pypage.PageImage(image_obj,
                              lane_width=int(config["lane_width"]),
                              margin=float(config["margin"]))

    marker = page.get_lane(index=lane_id, start=0).astype(float)
    marker = pv.pypage.Marker(marker)

    fig = marker.check()
    fig.update_layout(width=200, height=500)
    fig_html = pio.to_html(fig, full_html=False)

    return fig_html, marker.peak_index


def make_page_df(bucket_name, dir_prefix, image_path):
    config = get_page_config(bucket_name, dir_prefix)
    image_obj = gcs_utils.download_blob_to_file_object(bucket_name, image_path)
    page = pv.pypage.PageImage(image_obj,
                              lane_width=int(config["lane_width"]),
                              margin=float(config["margin"]))
    return page.get_df()


class ExperimentPath:
    def __init__(self, bucket_name, experiment_name):
        self.bucket_name = bucket_name
        self.experiment_name = experiment_name
        self.experiment_prefix = experiment_name
        self.analysis_prefix = f"{self.experiment_prefix}/analysis"
        self.raw_prefix = f"{self.experiment_prefix}/raw_data"
        self.worksheet_prefix = f"{self.experiment_prefix}/worksheet"
        self.data = {}
        self.worksheets = {}

        # In GCS, "folders" are just prefixes. We list the "subdirectories" of analysis.
        data_folders = gcs_utils.list_directories(self.bucket_name, self.analysis_prefix)

        # List json files in the worksheet directory
        worksheet_files = gcs_utils.list_blobs_with_prefix(self.bucket_name, prefix=self.worksheet_prefix)
        worksheet_datas = [w for w in worksheet_files if w.endswith('.json')]


        for name in data_folders:
            # The name is just the subdirectory name, not the full path
            run_analysis_prefix = f"{self.analysis_prefix}/{name}"
            
            # Check if a specific file exists to determine the type
            is_akta = gcs_utils.blob_exists(self.bucket_name, f"{run_analysis_prefix}/all_data.csv")
            data_type = "AKTA" if is_akta else "PAGE"

            self.data[name] = DataPath(self, name, data_type)

        for worksheet_path in worksheet_datas:
            name = os.path.basename(worksheet_path).replace('.json', '')
            self.worksheets[name] = worksheet_path


class DataPath:
    def __init__(self, experiment_path, run_name, data_type):
        self.exp_path = experiment_path
        self.run_name = run_name
        self.data_type = data_type
        
        self.analysis_prefix = f"{self.exp_path.analysis_prefix}/{self.run_name}"

        if data_type == "AKTA":
            self.file_type = "zip"
            self.fraction = f"{self.analysis_prefix}/fraction.csv"
            self.all_data = f"{self.analysis_prefix}/all_data.csv"
            self.phase = f"{self.analysis_prefix}/phase.csv"
            self.pool = f"{self.analysis_prefix}/pool.json"
            self.show = f"{self.analysis_prefix}/show.csv"
            self.config = f"{self.analysis_prefix}/config.json"
        else: # PAGE
            self.file_type = "PAGE"
            self.config = f"{self.analysis_prefix}/config.json"
            self.annotation = f"{self.analysis_prefix}/annotation.csv"

            config_str = gcs_utils.download_blob_as_string(self.exp_path.bucket_name, self.config)
            config = json.loads(config_str)
            ext = config.get('ext', '') # Use .get for safety
            self.raw = f"{self.exp_path.raw_prefix}/{self.run_name}{ext}"

        # The icon path is relative to the bucket root
        self.icon = f"{self.analysis_prefix}/icon.png"


def json_save(bucket_name, data_dict, blob_path):
    json_string = json.dumps(data_dict, indent=2, ensure_ascii=False)
    gcs_utils.upload_blob_from_string(bucket_name, json_string, blob_path, 'application/json')


def show_page_full(bucket_name, image_path, config, df=None):
    df = df.fillna("")
    lane_width = int(config["lane_width"])
    margin = float(config["margin"])

    image_obj = gcs_utils.download_blob_to_file_object(bucket_name, image_path)
    page = pv.pypage.PageImage(image_obj, lane_width=lane_width, margin=margin)

    page.annotate_lanes(df["Name"].values.tolist())
    page.palette = df["Color_code"].values.tolist()

    palette = {}

    marker_lane_index = int(config["marker"]["id"])
    marker_lane = page.get_lane(index=marker_lane_index, start=0).astype(float)
    marker = pv.pypage.Marker(marker_lane)
    marker.annotate(config["marker"]["annotate"])

    if df is not None:
        fig = page.annotated_imshow(palette, rectangle=True)
    else:
        fig = page.check_image()

    fig = pv.pypage.write_marker(fig, marker)
    return fig2html(fig, name="page")


def fig2html(fig, name="image"):
    fig.update_layout(width=900, height=600)
    config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': name,
            'width': 900,
            'height': 600,
            'scale': 1
        }
    }
    return pio.to_html(fig, full_html=False, config=config)


def get_page_fig4annotate(bucket_name, image_path, config, df):
    lane_width = int(config["lane_width"])
    margin = float(config["margin"])

    image_obj = gcs_utils.download_blob_to_file_object(bucket_name, image_path)
    page = pv.pypage.PageImage(image_obj, lane_width=lane_width, margin=margin)

    page.annotate_lanes(df["Name"].values.tolist())
    page.palette = df["Color_code"].values.tolist()

    palette = {}
    fig = page.annotated_imshow(palette, rectangle=True)
    return fig2html(fig, name="page")


def fraction_pooling(df):
       pool_df = df.copy()

       pool_df['From'] = pool_df.groupby('Pool')['Name'].transform(lambda x: ';'.join(x))
       pool_df = pool_df.drop_duplicates(subset=['Pool', 'From'])
       pool_df = pool_df.drop("Name",axis=1)

       pool_df = pool_df.rename(columns={"Pool":"Name"})
       
       return pool_df

