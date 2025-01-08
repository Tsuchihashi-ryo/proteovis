import cv2
import numpy as np
from scipy.signal import find_peaks
from scipy import signal
from scipy.ndimage import gaussian_filter1d
import seaborn as sns
from copy import copy
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from proteovis import graph
from proteovis.pyspectrum.spectrum import CorrectSpec


def detect_and_correct_tilt(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
    if lines is not None:
        for rho, theta in lines[0]:
            if np.pi/4 < theta < 3*np.pi/4:
                angle = theta - np.pi/2
                break
        else:
            angle = 0
    else:
        angle = 0

    center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle * 180 / np.pi, 1.0)

    # 回転後の画像サイズを計算
    cos = np.abs(rot_mat[0, 0])
    sin = np.abs(rot_mat[0, 1])
    new_w = int((image.shape[0] * sin) + (image.shape[1] * cos)) +50
    new_h = int((image.shape[0] * cos) + (image.shape[1] * sin))

    # 平行移動を調整
    rot_mat[0, 2] += (new_w / 2) - center[0]
    rot_mat[1, 2] += (new_h / 2) - center[1]

    

    # 白背景で回転
    warp_image =  cv2.warpAffine(image, rot_mat, (new_w, new_h), borderValue=(255,255,255))
    image = np.full((100,new_w,3),255)
    image = np.concatenate([image,warp_image]).astype(np.uint8)
    return image

def detect_lanes(image, expected_lane_width=30,margin=0.2):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # エッジ検出
    edges = get_edges(gray)

    # 垂直方向のエッジプロファイルを計算
    edge_profile = np.sum(edges, axis=0)

    # エッジプロファイルをスムージング
    smoothed_profile = gaussian_filter1d(edge_profile, sigma=5)

    # ピーク（エッジ）検出
    peaks, _ = find_peaks(255-smoothed_profile, distance=expected_lane_width*0.8, prominence=1,)

    # レーンの境界ペアを形成
    lane_boundaries = []
    for i in range(0, len(peaks) - 1, 2):
        if peaks[i+1] - peaks[i] < expected_lane_width * 1.5:
            lane_boundaries.append((peaks[i], peaks[i+1]))

    # レーンの中心を計算
    lane_centers = [(start + end) // 2 for start, end in lane_boundaries]

    # レーンの連続性を考慮した後処理
    final_lanes = []
    for i, center in enumerate(lane_centers):
        if i == 0 or abs(center - final_lanes[-1]) > expected_lane_width * (1-margin):
            final_lanes.append(center)
        else:
            # 近接したレーンは平均化
            final_lanes[-1] = (final_lanes[-1] + center) // 2

    final_lanes =insert_mean(np.array(final_lanes),expected_lane_width,image.shape[1]).astype(int)

    return final_lanes


class Lane:
  def __init__(self,x0,y0,x1,y1):
    self.x0 = x0
    self.y0 = y0
    self.x1 = x1
    self.y1 = y1



def get_lane(image,lane_x,lane_width=50,mergin=0,start=100):
  height, width = image.shape[:2]

  x0 = lane_x-lane_width//2 -mergin
  y0=start 
  x1=lane_x+lane_width//2 +mergin
  y1=height
  return Lane(x0,y0,x1,y1)


def get_edges(image):
  # ノイズ除去（メディアンフィルタ）
  image = cv2.medianBlur(image, 5)
  # Sobelフィルタを適用
  sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=5)               # 垂直方向の勾配

  # 勾配の絶対値を計算
  sobel_y = cv2.convertScaleAbs(sobel_y)
  return sobel_y

  

def insert_mean(arr,lane_width,maximum,minimum=0,mergin=1.1):
    """各数字の間に平均を挿入し、最小値と最大値まで平均差分で埋める"""
    n = len(arr)
    append_arr = []
    for i in range(n-1):
      if arr[i] + lane_width*1.1 > arr[i+1]:
        continue
      
      else:
        non_arr_n = (arr[i+1] - arr[i])//(lane_width*mergin)
        for k in range(1,int(non_arr_n)):
          append_arr.append( arr[i] + k * (arr[i+1] - arr[i]) / non_arr_n)


    #if n <= 1:  # 1要素以下の配列の場合はそのまま返す
    #    return arr
    #means = (arr[:-1] + arr[1:]) / 2
    #new_arr = np.concatenate((arr, means)) # concatenateで連結
    new_arr = np.concatenate((arr, append_arr))
    new_arr = np.sort(new_arr)

    mean_size = np.median(np.diff(new_arr))

    low_arr = np.arange(new_arr[0], minimum, -mean_size)
    high_arr = np.arange(new_arr[-1], maximum, mean_size)

    new_arr = np.sort(np.concatenate((low_arr[1:], new_arr[:-1], high_arr)))

    if new_arr[0] - (lane_width/2)*0.9 < 0:
      new_arr = new_arr[1:]
    
    if new_arr[-1] + (lane_width/2)*0.9 > maximum:
      new_arr = new_arr[:-1]

    return np.sort(new_arr)



class PageImage:
  def __init__(self,image_path,lane_width=50,margin=0.2):
    self.image_ = cv2.imread(image_path)
    
    self.lane_width = lane_width
    self.margin = margin
    self.image = detect_and_correct_tilt(self.image_)
    self.lanes = detect_lanes(self.image, self.lane_width,self.margin)
    self.lane_ids = list(range(len(self.lanes)))
    self.palette = sns.color_palette(n_colors=len(self.lanes))
    self.annotations = None

  def annotate_lanes(self,annotations):
    self.annotations = annotations
    assert len(self.lanes) == len(self.annotations)

  def imshow(self):
    fig = px.imshow(self.image_)
    return fig
  
  def check_image(self):
    fig = graph.annotate_page(self.image, self.lanes, self.lane_width)
    return fig

  def annotated_imshow(self,palette_dict=None,rectangle=True,text=True):
    if len(self.annotations):
       palette_dict = {id:color for id,color in zip(self.annotations,self.palette)}
    
    else:
       palette_dict = None
    fig = graph.annotate_page(self.image, self.lanes, self.lane_width,rectangle=rectangle,text=text,palette_dict=palette_dict,annotations=self.annotations)
    return fig

  def get_lane(self,index=None,name=None,mergin=0,start=0):
    if type(index)==int:
      lane = index
    elif name:
      lane =self.annotations.index(name)

    lane_x = self.lanes[lane]
    lane_coord = get_lane(self.image,lane_x,self.lane_width,mergin=mergin,start=start)
    return self.image[lane_coord.y0:lane_coord.y1,lane_coord.x0:lane_coord.x1,]
  
  def get_df(self):
    df = pd.DataFrame(columns=["Lane", "Name","Group","SubGroup","Color_code"],index=range(len(self.lanes)))

    for i in range(len(self.lanes)):
      color = palette2hex(self.palette[i])
      if self.annotations:
         df.loc[i] = i,self.annotations[i],"","",color
        
      else:
         df.loc[i] = i,str(i),"","",color
    
    return df


class Marker:
  def __init__(self, marker_image,standard_n=13):
    self.marker_image = marker_image
    self.peak_index = self.get_marker(standard_n)
    self.peak_annotation = []


  def get_marker(self, standard_n=13):
    marker_sum = self.marker_image.sum(axis=1).sum(axis=1)*-1
    corrector = CorrectSpec(lam=10**5,p=0.001,dn=20,poly=5)
    marker_sum  = corrector.clean_spec(marker_sum)

    for i in range(1,100,1):
      peak_index = signal.argrelmax(marker_sum, order=i)[0]
      if len(peak_index) <= standard_n:break

    return peak_index


  def check(self):
    fig = px.imshow(self.marker_image)
    for i,y in enumerate(self.peak_index):
      fig.add_annotation(go.layout.Annotation(
                        x=0, y=y,
                        xref="x",
                        yref="y",
                        text=f"{i}",
                        align='right',
                        xanchor="right",
                        showarrow=False,
                        font=dict(
                        size=12,
                        ),
                        ))
    fig.update_shapes(dict(xref='x', yref='y'))
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig

  def annotate(self,annotation):
    self.annotation = annotation
    assert len(self.annotation) == len(self.peak_index)


def write_marker(fig,marker):

  fig = copy(fig)

  for index,text in zip(marker.peak_index,marker.annotation):
    fig.add_annotation(go.layout.Annotation(
                      x=-0, y=index,
                      xref="x",
                      yref="y",
                      text=f"{text}",
                      align='right',
                      xanchor="right",
                      showarrow=False,
                      font=dict(
                      size=18,
                      ),
                      ))
  
  fig.add_annotation(go.layout.Annotation(
                      x=-0, y=100,
                      xref="x",
                      yref="y",
                      text="(kDa)",
                      align='right',
                      xanchor="right",
                      yanchor="bottom",
                      showarrow=False,
                      font=dict(
                      size=18,
                      ),
                      ))

  return fig



def palette2hex(palette_color):
  r = int(palette_color[0]*255)
  g = int(palette_color[1]*255)
  b = int(palette_color[2]*255)

  color_code = f'#{r:02x}{g:02x}{b:02x}'
  color_code = color_code.replace('0x', '')
  return color_code
  



















