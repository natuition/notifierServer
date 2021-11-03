from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os 
import json

app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)

@socketio.on('data', namespace='/map')
def on_socket_get_data_map(data):
    emit('updatePoints',get_path(data["sn"],data["session"]))

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
                path.append((eval(line.replace("\n","")),None))
    return path

def getWorkingTime():
    path = os.path.abspath(os.getcwd())
    all_session_resume = dict()
    lst = [name for name in os.listdir(path) if "SN" in name]
    for sn in lst:
        all_session_resume[sn] = [sn+"/"+name+"/session_resume.txt" for name in os.listdir(path+"/"+sn)]
    data = dict();
    for sn,resumes in all_session_resume.items():
        if sn not in data: data[sn] = list()
        for resume in resumes:
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
    return data

@app.route('/map/<sn>/<session>')
def maps(sn,session):
    return render_template('map.html')

@app.route('/')
def index():
    return render_template('index.html', tree=make_tree(os.path.abspath(os.getcwd())))

@app.route('/resume')
def resume():
    return render_template('resume.html')

if __name__ == "__main__":
    app.run(host="172.16.0.9",port=80,debug=True, use_reloader=False)