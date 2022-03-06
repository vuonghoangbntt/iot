/**************************************************************************
 * 
 * Network detail and passwords 
 * 
 **************************************************************************/

const char* ssid = "Truong Son";                                           // WLAN WiFi name
const char* password = "12345678";                                   // WiFi password

const char* MQTT_server = "ac439a62c4cc439ca14d605265033264.s1.eu.hivemq.cloud";                        // MQTT Broker IP address
const char* MQTT_user = "vuonghoang";                                      // MQTT Broker user (optional, if required)
const char* MQTT_pwd = "Vxh12345678";                                   // MQTT Broker password (optional, if required)
const int MQTT_port = 8883;

//const char* upload_url = "http://motiondetectionesp32.000webhostapp.com/saveimage.php";       // Location where images are POSTED
const char* upload_url = "http://40.117.86.18:8080/upload/1EAFG";
String serverName = "motiondetectionesp32.000webhostapp.com";   // REPLACE WITH YOUR Raspberry Pi IP ADDRESS
//String serverName = "example.com";   // OR REPLACE WITH YOUR DOMAIN NAME

String serverPath = "/upload.php";     // The default serverPath should be upload.php

const int serverPort = 80;
