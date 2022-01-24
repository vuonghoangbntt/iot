from flask import Flask, request, flash, redirect, url_for, render_template
import numpy as np
import os
from multiprocessing import Value
from datetime import datetime
import logging
import time
import paho.mqtt.client as paho
from paho import mqtt

app = Flask("Flask Image Gallery")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

UPLOAD_FOLDER = 'assets' 

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    logging.info("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    logging.info("mid: " + str(mid))

# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    logging.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
# declare counter variable
counter = Value('i', 0)
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set("vuonghoang", "Vxh12345678")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("ac439a62c4cc439ca14d605265033264.s1.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("gate/#", qos=1)

# a single publish, this can also be done in loops, etc.
client.publish("encyclopedia/temperature", payload="hot", qos=1)

@app.route('/')
@app.route('/index', methods=['GET'])
def index():
	#return "ESP32-CAM Flask Server", 200
    flash("hello world", category="error")
    return render_template('index.html')
@app.route('/gallery', defaults={'req_path': ''})
@app.route('/gallery/<path:req_path>')
def dir_listing(req_path):
    # Joining the base and the requested path
    abs_path = os.path.join(UPLOAD_FOLDER, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return 404

    # Show directory contents
    files = os.listdir(abs_path)
    return render_template('gallery.html', files=files)
@app.route('/upload', methods=['POST','GET'])
def upload():
	now = datetime.now()
	dt_string = now.strftime("%H_%M_%S")
	saved_folder = os.path.join(app.root_path, UPLOAD_FOLDER+'/'+now.strftime("%d_%m_%Y"))
	if not os.path.isdir(saved_folder):
		os.mkdir(saved_folder)
	if request.method == 'POST':
		logging.info("POST method")
		image_raw_bytes = request.get_data()
		#file = request.files['file']
		filename = str(dt_string+'.jpg')
		filename = os.path.join(saved_folder, filename)
		f = open(filename, 'wb')
		#file.save(os.path.join(UPLOAD_FOLDER, filename))
		f.write(image_raw_bytes)
		f.close()
		logging.info('Successful upload files')
		return 'Successful upload files!!!'
	
	else:
		logging.info('Get method')
		if not os.path.isdir(UPLOAD_FOLDER):
			os.mkdir(UPLOAD_FOLDER)
		return dt_string
if __name__=="__main__":
    client.loop_start()
    app.run(host='0.0.0.0', port=8080, debug=True)