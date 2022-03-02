import sqlite3 as sql
import time
import paho.mqtt.client as paho
from paho import mqtt
from sympy import arg
from config import *
import logging
from flask import g
import os
from datetime import datetime, timedelta

class DBAcess:
    def get_db(self):
        db = sql.connect(DATABASE)
        db.row_factory = sql.Row
        return db
    def query_db(self, query, args=(), one=False):
        cur = self.get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    def execute(self, query, args=()):
        connection = self.get_db()
        cursor = connection.cursor()
        cursor.execute(query, args)
        connection.commit()
        connection.close()
    def get_camera_by_user_id(self, userid):
        query = "SELECT cam.ID, cam.last_active, acc.name FROM useraccess AS acc, camera AS cam WHERE acc.deviceID = cam.id AND acc.userID = ?"
        return self.query_db(query, [userid])
    def delete_access(self, userid, deviceid):
        query = "DELETE FROM useraccess WHERE userID = ? and deviceID = ?"
        try:
            self.execute(query, args=[userid,deviceid])
            return True
        except:
            return False
    def add_device(self, userid, deviceid, name, key):
        query = "SELECT * FROM camera WHERE id = ? AND private_key = ?"
        row = self.query_db(query, args=[deviceid, key], one=True)
        if row is None:
            return False
        current_time = datetime.utcnow()
        current_time = (current_time + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
        query = "INSERT INTO useraccess (userid, deviceid, createdAt, name) VALUES (?,?,?,?)"
        try:
            self.execute(query, args=[userid, deviceid, current_time, name])
            return True
        except:
            return False
    def create_account(self, username, password, email, address):
        query = "SELECT * FROM user WHERE email = ?"
        row = self.query_db(query, args=[email])
        if len(row)>0:
            return False
        query = "INSERT INTO user (username, password, email, address) VALUES (?,?,?,?)"
        try:
            self.execute(query, args=[username, password, email, address])
            return True
        except:
            return False
    def get_user_file(self, userid, dir):
        query = "SELECT * FROM useraccess WHERE userid=?"
        rows = self.query_db(query, args=[userid])
        files = os.listdir(dir)
        access = False
        userfile = []
        for row in rows:
            if row['deviceid'] in dir:
                access = True
                return files, access
        for row in rows:
            for f in files:
                if row['deviceid'] in f:
                    access = True
                    userfile.append(f)
        return userfile, access
    def login(self, email, pwd):
        user = self.query_db('SELECT * FROM user WHERE email = ? and password = ?',[email,pwd], one=True)
        if user is not None:
            usr = User(user['id'], user['username'], user['password'], user['email'], user['address'])
            return usr
        else:
            return None
class Client:
    def check(self, topic):
        for inp in INPUT_GATE:
            if topic.startswith(inp):
                return True
        return False
    # setting callbacks for different events to see if it works, print the message etc.
    def on_connect(self, client, userdata, flags, rc, properties=None):
        print("CONNACK received with code %s." % rc)

    # with this callback you can see if your publish was successful
    def on_publish(self, client, userdata, mid, properties=None):
        print("mid: " + str(mid))

    # print which topic was subscribed to
    def on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    # print message, useful for checking if it was successful
    def on_message(self, client, userdata, msg):
        if len(msg.topic.split('/'))>3 and self.check(msg.topic):
            device_id = msg.topic.split('/')[-1]
            current_time = datetime.utcnow()
            current_time = (current_time + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
            
            db = DBAcess()
            u = db.query_db("SELECT * FROM camera WHERE id = ?", args=[device_id], one=True)
            if u is None:
                db.execute("INSERT INTO camera (id, name, status, private_key, last_active) VALUES (?,?,?,?,?)", args=[device_id, 'camera'+device_id, 1, '1axwzalu',current_time])
            else:
                db.execute("UPDATE camera SET last_active = ? WHERE id= ?", args=[current_time,device_id])
            gate = msg.topic
            u = db.query_db("SELECT * FROM data WHERE gate = ?", args=[gate], one=True)
            if u is None:
                db.execute("INSERT INTO data (cameraID, gate, content, time) VALUES (?, ?, ?)", args=[device_id, gate, str(msg.payload.decode("utf-8","ignore"), current_time)])
            else:
                db.execute("UPDATE data SET content = ?, time= ? WHERE gate = ?", args=[str(msg.payload.decode("utf-8","ignore")), current_time, gate])
        logging.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload.decode("utf-8","ignore")))

    def __init__(self):
        # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
        # userdata is user defined data of any type, updated by user_data_set()
        # client_id is the given name of the client
        self.container = []
        self.client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
        self.client.on_connect = self.on_connect

        # enable TLS for secure connection
        self.client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        # set username and password
        self.client.username_pw_set(USERNAME_CLOUD, PASSWORD_CLOUD)
        # connect to HiveMQ Cloud on port 8883 (default for MQTT)
        self.client.connect(DOMAIN_CLOUD, PORT_CLOUD)

        # setting callbacks, use separate functions like above for better visibility
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish

        # subscribe to all topics of encyclopedia by using the wildcard "#"
        self.client.subscribe(TOPIC, qos=1)
        self.client.loop_start()
    def get_messages(self):
        return self.container

class User:
    def __init__(self, id, username, password, email, address):
         self.id = id
         self.email = email
         self.password = password
         self.username = username
         self.address = address
         self.authenticated = False
    def is_anonymous(self):
         return False
    def is_authenticated(self):
         return self.authenticated
    def is_active(self):
         return True
    def get_id(self):
         return self.id
    def logout(self):
        self.authenticated = False
    def login(self):
        self.authenticated = True