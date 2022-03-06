from pickle import FALSE
from turtle import delay, update
from flask import Flask, request, flash, redirect, url_for, render_template, session
import numpy as np
import os
from multiprocessing import Value
from datetime import datetime
import logging
import time
import paho.mqtt.client as paho
from paho import mqtt
import sqlite3 as sql
from db import *
from waitress import serve
import json

app = Flask("Flask Image Gallery")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
c = Client()
client = c.client
db = DBAcess()

@app.route('/')
@app.route('/index', methods=['GET'])
def index():
	#return "ESP32-CAM Flask Server", 200
    #flash("hello world", category="error")
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    return render_template('index.html')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['txtUserName']
        password = request.form['txtPwd']
        usr = db.login(name, password)
        if usr is not None:
            session['Logedin'] = True
            session['Userid'] = usr.get_id()
            flash('Login Successful', "info")
        else:
            flash('Login Failed', "error")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        if db.create_account(request.form['userName'], request.form['userPwd'], request.form['userEmail'], request.form['userAddress']):
            flash('Account create !!!', 'info')
        else:
            flash("Failed to create account!!",'error')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', methods=['GET'])
def logout():
    session.pop("Logedin",None)
    session.pop("Userid",None)
    return redirect(url_for('index'))
@app.route('/gallery', defaults={'req_path': ''})
@app.route('/gallery/<path:req_path>')
def dir_listing(req_path):
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    # Joining the base and the requested path
    abs_path = UPLOAD_FOLDER + '/' + req_path

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return 404

    # Show directory contents
    files,access = db.get_user_file(session['Userid'], abs_path)
    if not access:
        return 404
    return render_template('gallery.html', files=files,abs_path=UPLOAD_FOLDER+'/'+req_path)
@app.route('/image-gallery/<path:req_path>')
def show_image(req_path):
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    # Joining the base and the requested path
    abs_path = UPLOAD_FOLDER + '/' + req_path

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return 404

    # Show images
    files = os.listdir(abs_path)
    return render_template('image-gallery.html', files=files, abs_path = abs_path)

@app.route('/device')
def setup_device():
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    rows = db.get_camera_by_user_id(session['Userid'])
    return render_template('device.html', rows=rows)

@app.route('/setting/<path:id>', methods=['POST','GET'])
def display_setting(id):
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    device = db.query_db("select * from camera where id = ?", [id], one=True)
    setting = db.query_db("select * from data where gate = ?", [INPUT_GATE[3]+id], one=True)
    setting = json.loads(setting['content'])
    if request.method == 'POST':
        intervalTime = request.form['intervalTime']
        client.publish(PUBLISH_GATE['monitor_setting']+id,payload=f'interval:{intervalTime}')
        status = True if request.form.get('cameraStatus') else False
        if status!=setting['CAM_enabled']:
            payload = 'enable' if request.form.get('cameraStatus') else 'disable'
            client.publish(PUBLISH_GATE['camera_setting']+id,payload=payload)
        status = True if request.form.get('motionSensorStatus') else False
        if status!=setting['PIR_enabled']:
            payload = 'enable' if request.form.get('motionSensorStatus') else 'disable'
            client.publish(PUBLISH_GATE['motion_setting']+id,payload=payload)
        delayTime = request.form['delayTime']

        client.publish(PUBLISH_GATE['motion_setting']+id, payload=f'delay:{delayTime}')
        status = True if request.form.get('saveSDStatus') else False
        if status!=setting['SD_enabled']:
            payload = 'enableSD' if request.form.get('saveSDStatus') else 'disableSD'
            client.publish(PUBLISH_GATE['camera_setting']+id, payload=payload)
        time.sleep(2)
        client.publish(PUBLISH_GATE['monitor_setting']+id,payload='getconfig')
        flash(f'{device["name"]} has updated!!!')
        return render_template('index.html')
    else:
        return render_template('settings.html', device=device, setting=setting)

@app.route('/add_device', methods = ['POST', 'GET'])
def add_device():
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    if request.method == "POST":
        print(request.form)
        if db.add_device(session['Userid'],request.form['deviceID'],request.form['deviceName'],request.form['devicePwd']):
            flash(f'Successful add device {request.form["deviceID"]}','info')
        else:
            flash(f'Not found device {request.form["deviceID"]}', 'error')
        return redirect(url_for('index'))
    return render_template('add_device.html')

@app.route('/delete/<path:id>', methods = ['POST', 'GET'])
def delete_device(id):
    if 'Logedin' not in session:
        return redirect(url_for('login'))
    if not session['Logedin']:
        return redirect(url_for('login'))
    if db.delete_access(session['Userid'], id):
        flash(f'Device {id} has deleted!', 'info')
    else:
        flash(f'Device failed to delete!', 'error')
    return redirect(url_for('index'))
@app.route('/upload/<path:id>', methods=['POST','GET'])
def upload(id):
	now = datetime.utcnow()+ timedelta(hours=7)
	dt_string = now.strftime("%H_%M_%S")
	saved_folder = os.path.join(app.root_path, UPLOAD_FOLDER+'/'+id+'/'+now.strftime("%d_%m_%Y"))
	if not os.path.isdir(saved_folder):
		os.makedirs(saved_folder,mode=0o666)
	if request.method == 'POST':
		logging.info("POST method")
		image_raw_bytes = request.get_data()
		filename = str(dt_string+'.jpg')
		filename = os.path.join(saved_folder, filename)
		f = open(filename, 'wb')
		f.write(image_raw_bytes)
		f.close()
		logging.info('Successful upload files')
		return 'Successful upload files!!!'
	
	else:
		logging.info('Get method')
		if not os.path.isdir(UPLOAD_FOLDER):
			os.mkdir(UPLOAD_FOLDER)
		return dt_string
