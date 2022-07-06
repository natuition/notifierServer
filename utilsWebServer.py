from cv2 import PROJ_SPHERICAL_ORTHO
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os 
import statistics
import json
from urllib.parse import quote
from haversine import haversine
from engineio.payload import Payload
import re

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

Payload.max_decode_packets = 500

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)

def getConfig():
    with open('./config.json') as json_file:
        config = json.load(json_file)
    return config

config = getConfig()

def get_field_feature(field):
    field.append(field[0])
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [field]
        },
        'properties':{
            'stroke': '#0620fb',
            'stroke-width': 4,
            'stroke-opacity': 1,
            'fill': '#0620fb',
            'fill-opacity': 0.4,
            "name":"field"
        }
    }

def get_path_feature(path):
    return {
        "type": "Feature",
        "properties": {
            "stroke": "#ff0000",
            "stroke-width": 4,
            "stroke-opacity": 1,
            "name":"path"
        },
        "geometry": {
            "type": "LineString",
            "coordinates": path
        }
    } 

def get_formated_path(path):
    points = list()
    coordsPoints = list()
    for point in path:
        coords_with_quality = point[0]
        coords = [round(coords_with_quality[1], 6),round(coords_with_quality[0],6)]
        ext = point[1]
        if ext is None:
            points.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': coords
                }
            })
        else:
            points.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': coords
                },
                "properties":{
                    'Type' : ext
                }
            })
        coordsPoints.append(coords)
    return [points,coordsPoints]

@socketio.on('data', namespace='/map')
def on_socket_get_data_map(data):
    path = get_path(data["sn"],data["session"])
    emit('updatePoints',get_formated_path(path))

@socketio.on('data', namespace='/resume')
def on_socket_get_data_resume():
    emit('sendData',getWorkingTime())

def make_tree(path,getFiles=False):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn) or getFiles:
                dictt = make_tree(fn,getFiles)
                dictt['father'] = path.split("/")[-1]
                tree['children'].append(dictt)
    return tree

def get_path(sn,session):
    path = list()
    with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/path_gps_with_extract.txt", 'r') as file:
        for line in file.readlines(): 
            if ":" in line:
                path.append((eval(line.replace("\n","").split(":")[0]),eval(line.replace("\n","").split(":",maxsplit=1)[1])))
            else:
                line = line.split("]")[0]+"]"
                path.append((eval(line.replace("\n","")),None))
    return path

def getWorkingTime():
    path = os.path.abspath(os.getcwd())
    all_session_resume = dict()
    lst = [name for name in os.listdir(path) if "SN" in name]
    for sn in lst:
        all_session_resume[sn] = [sn+"/"+name+"/session_resume.txt" for name in os.listdir(path+"/"+sn)]
    data = dict()
    for sn,resumes in all_session_resume.items():
        if sn not in data: data[sn] = list()
        for resume in resumes:
            try:
                with open(resume, 'r') as file:
                    lines = file.readlines()
                    start = lines[0].replace("\n","").split(":")[1].split(" ")
                    start_format =  start[1].split("-")[2].replace(" ","")+"-"+\
                                    start[1].split("-")[1].replace(" ","")+"-"+\
                                    start[1].split("-")[0].replace(" ","")+"T"+\
                                    start[2].split("-")[0].replace(" ","")+":"+\
                                    start[2].split("-")[1].replace(" ","")+":"+\
                                    start[2].split("-")[2].replace(" ","")+"."+\
                                    start[3]
                    end = lines[4].replace("\n","").split(":")[1].split(" ")
                    end_format =  end[1].split("-")[2].replace(" ","")+"-"+\
                                    end[1].split("-")[1].replace(" ","")+"-"+\
                                    end[1].split("-")[0].replace(" ","")+"T"+\
                                    end[2].split("-")[0].replace(" ","")+":"+\
                                    end[2].split("-")[1].replace(" ","")+":"+\
                                    end[2].split("-")[2].replace(" ","")+"."+\
                                    end[3]
                    data[sn].append({"start":start_format,"end":end_format})
            except:
                pass
    return data

@app.route('/map/<sn>/<session>')
def maps(sn,session):
    data = []
    path_robot = []
    with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/session_resume.txt", 'r') as file:
        data=file.readlines()
    with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/field.txt", 'r') as file:
        points = file.readlines()
    last_gps_quality = "-"
    try:
        with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/path_gps_with_extract.txt", 'r') as file:
            path_robot = file.readlines() 
            last_line = path_robot[-1]
            if isinstance(last_line,list):
                last_line_list = last_line
            else:
                last_line = last_line.split("]")[0]+"]"
                last_line_list = eval(last_line)
            if len(last_line_list) > 2:
                last_gps_quality = last_line_list[2]
            path_robot.append(last_line_list[0:2])
    except:
        pass

    data.append(f"Last gps quality : {last_gps_quality}")

    if sn in config["Robot_Language"]:
        language = config["Robot_Language"][sn]
        data.append(f"Language : {language}")
    else:
        data.append(f"Language : en")

    traveled_distance = 0

    before = None
    for point_str in path_robot:
        if isinstance(point_str,list):
            point_list = point_str
        else:
            point_str = point_str.split("]")[0]+"]"
            point_list = eval(point_str)
        if before is not None:
            traveled_distance += haversine(before,point_list[0:2])
        before = point_list[0:2]

    traveled_distance *= 1000

    traveled_distance = round(traveled_distance, 2)
                
    coords_field = list()
    for coord in points:
        coord = coord.replace("[","").replace("]","").replace("\n","").split(",")
        coords_field.append([float(coord[1]),float(coord[0])])
    return render_template('map.html',data=data,coords_field=coords_field,traveled_distance=traveled_distance)

@app.route('/map_static/<sn>/<session>')
def map_static(sn,session):
    data = []
    path_robot = []
    with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/session_resume.txt", 'r') as file:
        data=file.readlines()
    with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/field.txt", 'r') as file:
        points = file.readlines()
    last_gps_quality = "-"
    try:
        with open(os.path.abspath(os.getcwd())+f"/{sn}/{session}/path_gps_with_extract.txt", 'r') as file:
            path_robot = file.readlines() 
            last_line = path_robot[-1]
            if isinstance(last_line,list):
                last_line_list = last_line
            else:
                last_line = last_line.split("]")[0]+"]"
                last_line_list = eval(last_line)
            if len(last_line_list) > 2:
                last_gps_quality = last_line_list[2]
            path_robot.append(last_line_list[0:2])
    except:
        pass

    data.append(f"Last gps quality : {last_gps_quality}")

    traveled_distance = 0

    before = None
    for point_str in path_robot:
        if isinstance(point_str,list):
            point_list = point_str
        else:
            point_str = point_str.split("]")[0]+"]"
            point_list = eval(point_str)
        if before is not None:
            traveled_distance += haversine(before,point_list[0:2])
        before = point_list[0:2]

    traveled_distance *= 1000

    traveled_distance = round(traveled_distance, 2)
                
    coords_field = list()
    for coord in points:
        coord = coord.replace("[","").replace("]","").replace("\n","").split(",")
        coords_field.append([float(coord[1]),float(coord[0])])

    path = get_path(sn,session)

    #coords_center = [statistics.mean([coords[0] for coords in coords_field]),statistics.mean([coords[1] for coords in coords_field])]
    
    field_feature = get_field_feature(coords_field)
    path_feature = get_path_feature(get_formated_path(path)[1])

    feature_collection = {"type": "FeatureCollection","features": [field_feature, path_feature]}

    with open('map.geojson', 'w') as outfile:
        json.dump(feature_collection, outfile)

    #geojson-renderer --dimensions 1920x1080 --tile-url-template "{tile}" map.geojson
    os.system("/root/.config/jlauncher/bin/geojson-renderer --dimensions 1920x1080 --tile-url-template 'load_balancing={1-4} tile={tile}' map.geojson")

    #http://mt1.google.com/vt/lyrs=s&x={x}&y={Y}&z={z}
    #{tile} = {z}/{x}/{Y}
    with open("map.svg", 'r+') as f:
        svg = f.read()
        svg = re.sub(r'load_balancing=([0-9]) tile=([0-9]*)\/([0-9]*)\/([0-9]*)', r'http://mt\1.google.com/vt/lyrs=s&x=\3&y=\4&z=\2', svg)
        svg = svg.replace("mt4","mt0")
        #f.seek(0)
        #f.write(svg)
        #f.truncate()

    return render_template('map_static.html', svg=svg)

@app.route('/')
def index():
    return render_template('index.html', tree=make_tree(os.path.abspath(os.getcwd())))

@app.route('/resume')
def resume():
    return render_template('resume.html')

if __name__ == "__main__":
    #host="172.16.0.9"
    app.run(host="0.0.0.0",port=80,debug=True, use_reloader=False)