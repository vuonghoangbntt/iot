from sqlalchemy import true
from db import *
import json

DEVICE_ID = 'BX2CD'
DEVICE_SECRET_KEY = '2cdbalm'
DEVICE_SETTINGS = json.loads('{"CAM_enabled":true,"SD_enabled":true,"PIR_enabled":false,"PIR_delay":20000,"ReportState":true,"ReportWiFi":false,"TempInterval":60000,"StateInterval":30000}')
DEVICE_STATE = json.loads('{"IP Address":"192.168.1.14","RSSI (dBm)":-76,"wifi":48,"Core Temperature (°C)":53,"Uptime":"0d6:19:27","Start Reason":"RTCWDT_RTC_RESET","Free Heap Memory":3463524,"Min Free Heap":3444884}')
# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
container = []
# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))
# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))
def on_message(client, userdata, msg):
    topic = msg.topic
    content = str(msg.payload.decode("utf-8","ignore"))
    if topic.startswith("gate/camera/cmnd/"+DEVICE_ID):
        if content == 'enable':
            DEVICE_SETTINGS['CAM_enabled'] = True
        elif content == 'disable':
            DEVICE_SETTINGS['CAM_enabled'] = False
        elif content == 'enableSD':
            DEVICE_SETTINGS['SD_enabled'] = True
        elif content == 'disableSD':
            DEVICE_SETTINGS['SD_enabled'] = False
    if topic.startswith("gate/motion/cmnd/"+DEVICE_ID):
        if content == 'enable':
            DEVICE_SETTINGS['PIR_enabled'] = True
        elif content == 'disable':
            DEVICE_SETTINGS['PIR_enabled'] = False
    if topic.startswith("gate/monitor/cmnd"+DEVICE_ID):
        if content == 'getconfig':
            client.publish('gate/monitor/config/'+DEVICE_ID,payload=json.dumps(DEVICE_SETTINGS))
    print(topic+'-'+content)
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message
client.on_subscribe = on_subscribe
# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(USERNAME_CLOUD, PASSWORD_CLOUD)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect(DOMAIN_CLOUD, PORT_CLOUD)
# subscribe to all topics of encyclopedia by using the wildcard "#
client.subscribe(TOPIC, qos=1)

client.publish('gate/monitor/config/'+DEVICE_ID,payload=json.dumps(DEVICE_SETTINGS))
while(1):
    client.loop_start()
    client.publish('gate/monitor/state/'+DEVICE_ID,payload=json.dumps(DEVICE_STATE).encode("utf-8"))
    time.sleep(30)