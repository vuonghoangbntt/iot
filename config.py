UPLOAD_FOLDER = 'static/assets' 
DATABASE = 'iot.db'
USERNAME_CLOUD = "vuonghoang"
PASSWORD_CLOUD = "Vxh12345678"
DOMAIN_CLOUD = "ac439a62c4cc439ca14d605265033264.s1.eu.hivemq.cloud"
PORT_CLOUD = 8883
TOPIC = "gate/#"
INPUT_GATE = ["gate/temperature/state/","gate/motion/state/","gate/camera/state/","gate/monitor/config/","gate/monitor/state/","gate/monitor/wifi/"]
PUBLISH_GATE = {
    'camera_setting': "gate/camera/cmnd/",
    'motion_setting': "gate/motion/cmnd/",
    'monitor_setting': "gate/monitor/cmnd/"
}