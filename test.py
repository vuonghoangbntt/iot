from http import client
import paho.mqtt.client as mqtt 
import os
from db import *

buff=[]
imgready = False

saved_folder = os.path.join(app.root_path, UPLOAD_FOLDER+'/'+id+'/'+now.strftime("%d_%m_%Y"))