from numpy import shape
from numpy.core import shape_base
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
from copy import copy
from proteovis.pypage import pypage



def unicorn_ploty_graph(df, first="UV 1_280", second="Cond", third="pH", forth="Conc B", dropdowns=None):
    uv_color = "#1f77b4"
    ph_color = "#2ca772"
    cond_color = "#f29d5f"
    concb_color = "#b5b5b5"

    UV = [c for c in df.columns if c[:2]=="UV"]

    axis_label = {
        UV[0]:f"UV {UV[0].split('_')[-1]}nm (mAU)",
        UV[1]:f"UV {UV[1].split('_')[-1]}nm (mAU)",
        UV[2]:f"UV {UV[2].split('_')[-1]}nm (mAU)",
        'Cond':"Conductivity (mS/cm)",
        'Conc B':"B Concentration (%)",
        'pH':"pH",
        'System flow':"System flow (mL/min)",
        'Sample flow':"System flow (mL/min)",
        'PreC pressure':"PreC pressure (MPa)",
        'System pressure':"System pressure (MPa)",
        'Sample pressure':"Sample pressure (MPa)",
    }

    if not dropdowns:
        dropdowns = list(axis_label.keys())

    fig = go.Figure()

    # 初期トレースの追加
    fig.add_trace(go.Scatter(
        x=df["mL"],
        y=df[first],
        yaxis="y",
        line=dict(color=uv_color),
        fill="tozeroy",
        name=axis_label[first]
    ))

    fig.update_layout(
        xaxis=dict(
            domain=[0.05, 0.85],
            title="mL",
        ),
        yaxis=dict(
            title=axis_label[first],
            titlefont=dict(color=uv_color),
            tickfont=dict(color=uv_color)
        )
    )

    if second:
        fig.add_trace(go.Scatter(
            x=df["mL"],
            y=df[second],
            yaxis="y2",
            line=dict(color=cond_color),
            name=axis_label[second]
        ))

        fig.update_layout(
            yaxis2=dict(
                title=axis_label[second],
                titlefont=dict(color=cond_color),
                tickfont=dict(color=cond_color),
                anchor="x",
                side="right",
                overlaying="y"
            )
        )

    if third:
        fig.add_trace(go.Scatter(
            x=df["mL"],
            y=df[third],
            yaxis="y3",
            line=dict(color=ph_color),
            name=axis_label[third]
        ))

        fig.update_layout(
            yaxis3=dict(
                title=axis_label[third],
                titlefont=dict(color=ph_color),
                tickfont=dict(color=ph_color),
                anchor="free",
                side="right",
                overlaying="y",
                autoshift=True
            )
        )

    if forth:
        fig.add_trace(go.Scatter(
            x=df["mL"],
            y=df[forth],
            yaxis="y4",
            name=axis_label[forth],
            line=dict(color=concb_color),
        ))

        fig.update_layout(
            yaxis4=dict(
                title=axis_label[forth],
                titlefont=dict(color=concb_color),
                tickfont=dict(color=concb_color),
                anchor="free",
                side="right",
                overlaying="y",
                autoshift=True
            ),
        )

    # ドロップダウンメニューの作成
    updatemenus = []

    def none_button(i):
      return [dict(
        label="None",
        method="update",
        args=[{"y":[[]]},{f"yaxis{i+1}": {"visible": False}},[i],],
    )]


    # Y1軸のドロップダウン
    updatemenus.append(dict(
        buttons=[dict(
            args=[{
                'y': [df[col].tolist()],
                'name': [axis_label[col]]
            },
                  {"yaxis":dict(
            title=axis_label[col],
            titlefont=dict(color=uv_color),
            tickfont=dict(color=uv_color)
        )},
                  [0]],  # トレースのインデックスを指定
            label=axis_label[col],
            method='update',
        ) for col in dropdowns],
        direction="down",
        showactive=True,
        x=0.1,
        xanchor="center",
        y=1.05,
        yanchor="bottom",
        font=dict(size=12)
    ))

    # Y2軸のドロップダウン
    updatemenus.append(dict(
        buttons=[dict(
            args=[{
                'y': [df[col].tolist()],
                'name': [axis_label[col]]
            },
              {'yaxis2': dict(
            title=axis_label[col],
            titlefont=dict(color=cond_color),
            tickfont=dict(color=cond_color),
            anchor="x",
            side="right",
            overlaying="y"
        )},
              [1]], # トレースのインデックスを指定
            label=axis_label[col],
            method='update'
        ) for col in dropdowns] + none_button(1),
        direction="down",
        showactive=True,
        x=0.35,
        xanchor="center",
        y=1.05,
        yanchor="bottom",
        font=dict(size=12)
    ))

    # Y3軸のドロップダウン

    updatemenus.append(dict(
        buttons=[dict(
            args=[{
                'y': [df[col].tolist()],
                'name': [axis_label[col]]},
                {'yaxis3':dict(
            title=axis_label[col],
            titlefont=dict(color=ph_color),
            tickfont=dict(color=ph_color),
            anchor="free",
            side="right",
            overlaying="y",
            autoshift=True
        )},
              [2],],  # トレースのインデックスを指定
            label=axis_label[col],
            method='update'
        ) for col in dropdowns] + none_button(2)
        ,
        direction="down",
        showactive=True,
        x=0.6,
        xanchor="center",
        y=1.05,
        yanchor="bottom",
        font=dict(size=12)
    ))

    # Y4軸のドロップダウン
    updatemenus.append(dict(
        buttons=[dict(
            args=[{
                'y': [df[col].tolist()],
                'name': [axis_label[col]]
            },
                  {"yaxis4":dict(
            title=axis_label[col],
            titlefont=dict(color=concb_color),
            tickfont=dict(color=concb_color),
            anchor="free",
            side="right",
            overlaying="y",
            autoshift=True
        )},
                    [3]],  # トレースのインデックスを指定
            label=axis_label[col],
            method='update'
        ) for col in dropdowns] + none_button(3),
        direction="down",
        showactive=True,
        x=0.85,
        xanchor="center",
        y=1.05,
        yanchor="bottom",
        font=dict(size=12)
    ))

    axis_texts = []
    for i,y in enumerate(["y","y2","y3","y4"]):
      fig.add_annotation(dict(
                        x= 0.1 + i*0.25,
                        y=1.2,
                        xref="paper",
                        yref="paper",
                        text=y,
                        align='center',
                        showarrow=False,
                        yanchor='top',
                        font=dict(
                        size=12
                        ),
                        opacity=1))
    



    # レイアウトの更新
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        width=850,
        height=600,
        updatemenus=updatemenus,
        legend=dict(
            yanchor="top",
            y=-0.2,
            xanchor="right",
            x=1,
            font=dict(size=12),
        ),
        margin=dict(t=80, b=5, l=5, r=5)  # ドロップダウン用に上部マージンを調整
    )

    return fig


def annotate_fraction(fig,frac_df,phase=None,rectangle=True,text=True,annotations=None):

  fig =copy(fig)
  
  
  use_color_palette = {}

  shapes = []
  texts = []
  phase_shapes = []
  phase_texts = []
  

  for i,(index, row) in enumerate(frac_df.iterrows()):
    if annotations:
      if not row["Fraction_Start"] in annotations:
        continue

    color = row["Color_code"]#f"rgb({int(palette[i][0]*255)},{int(palette[i][1]*255)},{int(palette[i][2]*255)})"
    use_color_palette[row["Fraction_Start"]] = color#palette[i]

    if rectangle:
      
      shapes.append(dict(type="rect",
                    x0=row["Start_mL"], y0=0, x1=row["End_mL"], y1=row["Max_UV"],
                    xref="x",
                    yref="y",
                    line=dict(color=color,width=2),
                    ))

    if text:
      texts.append(dict(
                        x=(row["Start_mL"]+row["End_mL"])/2,
                        y=0,
                        xref="x",
                        yref="y",
                        text=row["Fraction_Start"],
                        align='center',
                        showarrow=False,
                        yanchor='top',
                        textangle=90,
                        font=dict(
                        size=10
                        ),
                        bgcolor=color,

                        opacity=0.8))

   
    max_mL = frac_df["Max_UV"].max()*1.1
    
  for i,row in phase.iterrows():
      color = row["Color_code"]#f"rgb({int(palette_phase[i][0]*255)},{int(palette_phase[i][1]*255)},{int(palette_phase[i][2]*255)})"
      phase_shapes.append(dict(type="rect",
                      x0=row["Start_mL"], y0=0, x1=row["End_mL"], y1=max_mL,
                      layer="below",
                      line=dict(color=color,width=0),
                      fillcolor=color,
                      opacity=0.1
                      ))
      
      if "Phase" in phase.columns:
          phase_texts.append(dict(
                        x=(row["Start_mL"]+row["End_mL"])/2,
                        y=max_mL,
                        xref="x",
                        yref="y",
                        text=row["Phase"],
                        align='center',
                        showarrow=False,
                        yanchor='top',
                        font=dict(
                        size=12
                        ),
                        opacity=1))


  current_texts = getattr(fig.layout, 'annotations', [])
  current_texts = list(current_texts)  # <--- この行を追加
  all_texts = current_texts + texts + phase_texts

  # shapesとannotationsを追加
  fig.update_layout(
      shapes=shapes+phase_shapes,
      annotations=all_texts
  )                  
  fig.update_shapes(dict(xref='x', yref='y'))

  
  add_updatemenus=[
      dict(
          type="buttons",
          direction="down",
          yanchor="bottom",
          y=-0.3,
          xanchor="left",
          x=0,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"shapes[{k}].visible": True for k in range(len(shapes))}],
                  args2=[{f"shapes[{k}].visible": False for k in range(len(shapes))}],
                  label="fraction box",
                  method="relayout"
              ),
          ]
      ),
      dict(
          type="buttons",
          direction="down",
          yanchor="bottom",
          y=-0.4,
          xanchor="left",
          x=0,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"annotations[{k}].visible": True for k in range(4,4+len(texts))}],
                  args2=[{f"annotations[{k}].visible": False for k in range(4,4+len(texts))}],
                  label="fraction text",
                  method="relayout"
              ),
          ]
      ),
      dict(
          type="buttons",
          direction="down",
          yanchor="bottom",
          y=-0.3,
          xanchor="left",
          x=0.4,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"shapes[{k}].visible": True for k in range(len(shapes),len(shapes+phase_shapes))}],
                  args2=[{f"shapes[{k}].visible": False for k in range(len(shapes),len(shapes+phase_shapes))}],
                  label="phase box",
                  method="relayout"
              ),
          ]
      ),
         dict(
          type="buttons",
          direction="down",
          yanchor="bottom",
          y=-0.4,
          xanchor="left",
          x=0.4,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"annotations[{k}].visible": True for k in range(4+len(texts),4+len(shapes+phase_texts))}],
                  args2=[{f"annotations[{k}].visible": False for k in range(4+len(texts),4+len(shapes+phase_texts))}],
                  label="phase text",
                  method="relayout"
              ),
          ]
      )
  ]
  current_updatemenus = getattr(fig.layout, 'updatemenus', [])
  current_updatemenus = list(current_updatemenus)
  all_updatemenus = current_updatemenus + add_updatemenus
  fig.update_layout(updatemenus=all_updatemenus)

  return fig,use_color_palette



def annotate_page(image, lanes, lane_width=30,rectangle=True,text=True,palette_dict=None,annotations=None):

  fig = px.imshow(image)
  height, width = image.shape[:2]
  fig.update_layout(
      template="plotly_white",
      title=dict(text='PAGE image',
                 font=dict(size=24),
                  x=0.5,
                  y=0.95,
                  xanchor='center',
                  #yanchor="bottom"
                ),
      width=width,
      height=height,
      margin=dict(t=80, b=5, l=5, r=5)
  )  

  fig.update_layout(
    # プロットの背景を透明に
    plot_bgcolor='rgba(0,0,0,0)',
    # 図全体の背景を透明に（必要に応じて）
    paper_bgcolor='rgba(0,0,0,0)',
    # x軸の線を消す
    xaxis=dict(
        showline=False,
        showgrid=False,
        zeroline=False,
    ),
    # y軸の線を消す
    yaxis=dict(
        showline=False,
        showgrid=False,
        zeroline=False,
    )
  )

  if not annotations:
      annotations = list(range(len(lanes)))

  if not palette_dict:
      palette = sns.color_palette("Set1", len(lanes))
      #annotations = list(range(len(lanes)))
      palette_dict = {a:p for a,p in zip(annotations,palette)}


  shapes = []
  texts = []
  i=0
  for label,lane in zip(annotations,lanes):
    if not label in palette_dict.keys():
        continue
    
    if label == "":
      continue

    color = f"rgb({int(palette_dict[label][0]*255)},{int(palette_dict[label][1]*255)},{int(palette_dict[label][2]*255)})"

    if rectangle:
      lane_coord = pypage.get_lane(image,lane,lane_width=50)
      
      shapes.append(dict(type="rect",
                    x0=lane_coord.x0, y0=lane_coord.y0, x1=lane_coord.x1, y1=lane_coord.y1,
                    line=dict(color=color,width=2),
                    ))

    if text:
      texts.append(dict(
                            x=lane, y=100,
                            xref="x",
                            yref="y",
                            text=f"{label}",
                            align='center',
                            showarrow=False,
                            yanchor='bottom',
                            textangle=90,
                            font=dict(
                            size=18,
                            ),
                            bgcolor=color,
                            opacity=0.8))

                            
  fig.update_layout(coloraxis_showscale=False)
  fig.update_xaxes(showticklabels=False)
  fig.update_yaxes(showticklabels=False)

    # shapesとannotationsを追加
  fig.update_layout(
      shapes=shapes,
      annotations=texts
  )                  
  fig.update_shapes(dict(xref='x', yref='y'))

  fig.update_layout(
  updatemenus=[
      dict(
          type="buttons",
          direction="down",
          x=-0.05,
          y=0.9,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"shapes[{k}].visible": True for k in range(len(shapes))}],
                  args2=[{f"shapes[{k}].visible": False for k in range(len(shapes))}],
                  label="Rectangle ☑",
                  method="relayout"
              ),
          ]
      ),
      dict(
          type="buttons",
          direction="down",
          x=-0.05,
          y=0.8,
          showactive=True,
          active=0,
          font=dict(size=12),
          buttons=[
              dict(
                  args=[{f"annotations[{k}].visible": True for k in range(len(texts))}],
                  args2=[{f"annotations[{k}].visible": False for k in range(len(texts))}],
                  label="Annotation ☑",
                  method="relayout"
              ),
          ]
      )
  ],
  )

  return fig