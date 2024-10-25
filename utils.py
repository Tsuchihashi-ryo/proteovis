import os
from glob import glob
import proteovis as pv
import plotly.io as pio
import pandas as pd


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


def get_page_image(path):
        page = pv.pypage.PageImage(path,lane_width=44)
        page_fig = page.check_image()
        return page_fig


def sampling_data2html(dir):
        name = os.path.basename(dir)

        image_path = os.path.join(dir[1:],"icon.png").replace("\\","/")
        file_type_binary = os.path.exists(os.path.join(dir,"all_data.csv"))
        if file_type_binary:
                file_type = "AKTA"
        else:
                file_type = "PAGE"

        template_html =  f"""
        <div class="bg-blue-100 p-4 rounded-lg">
            <img src="{image_path}">
            <p class="text-sm font-medium">File: {name}</p>
            <p class="text-sm">Type: {file_type}</p>
        </div>
        """

        return template_html


def get_samples(dir):
    analysis_dirs = glob(os.path.join(dir,"*"))

    sample_list = []

    for dir in analysis_dirs:
        sample_html = sampling_data2html(dir)
        sample_list.append(sample_html)

    sample_html = "".join(sample_list)

    return sample_html


def get_akta_fig(dir,first="UV 1_280",second="Cond",third=None,forth=None):
    akta_path = os.path.join(dir, f"all_data.csv")
    frac_path = os.path.join(dir, f"fraction.csv")
    phase_path = os.path.join(dir, f"phase.csv")

    akta_df = pd.read_csv(akta_path,index_col=0)
    frac_df = pd.read_csv(frac_path,index_col=0)
    phase_df = pd.read_csv(phase_path,index_col=0)

    fig = pv.graph.unicorn_ploty_graph(akta_df,first=first,second=second,third=None,forth=None)

    fig,use_color_palette = pv.graph.annotate_fraction(fig,frac_df,phase_df)

    fig.update_layout(
           width=850,
           height=600
    )

    fig_html = pio.to_html(fig,full_html=False)

    return fig_html

