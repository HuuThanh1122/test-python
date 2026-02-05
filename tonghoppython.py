import paho.mqtt.client as mqtt
import json
import time
import os
import random
#thông tin kết nối
HOST = "thingsboard.cloud"
PORT = 1883
ACCESSTOKEN = "hwG5wXeIuanRB51zhhZt"
CLIENT_ID = f"device-{random.randint(1000,9999)}"

TELEMETRY_TOPIC = "v1/devices/me/telemetry"
ATTR_REQUEST_TOPIC = "v1/devices/me/attributes/request/1"
ATTR_RESPONSE_TOPIC = "v1/devices/me/attributes/response/+"
RPC_SUBSCRIBE_TOPIC = "v1/devices/me/rpc/request/+"
RPC_PUBLISH_TOPIC =  "v1/devices/me/rpc/response/"

BUFFER_FILE = "buffer2.txt"
connected = False

def on_connect(client,userdata,flags,reasonCode,properties = None):
    global connected
    if reasonCode == 0:
        connected = True
        print("Kết nối thành công tới thingsboard")
        client.subscribe(ATTR_RESPONSE_TOPIC)
        request = {
            "sharedKeys":"uploadInterval,threshold"
        }
        client.publish(ATTR_REQUEST_TOPIC,json.dumps(request),qos=1)
        send_client_attributes(client)
    else:
        connected = False
        print("Kết nối thất bại,rc")

def on_disconnect(client,userdata,reasonCode,properties = None):
    global connected
    connected = False
    print("Mất kết nối")
#hàm lưu giữ liệu khi bị mất mạng
def save_buffer_file(data):
    with open(BUFFER_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(data)+"\n")
    print("Lưu telemetry vào file tạm")

def send_buffer_file(client):
    if not os.path.exists(BUFFER_FILE):
        return
    print("Đang gửi file buffer")
    with open(BUFFER_FILE,"r",encoding="utf-8") as f:
        lines = f.readlines()
    remain = []
    for line in lines:
        if not connected:
            remain.append(line)
            break
        try:
            client.publish(TELEMETRY_TOPIC,line.strip(),qos = 1)
            print("Đã gửi buffer file:",line.strip())
            time.sleep(0.2)
        except Exception as e:
            print("Lỗi gửi buffer:",e)
            remain.append(line)
            break
    if remain:
        with open(BUFFER_FILE,"w",encoding="utf-8") as f:
            f.writelines(remain)
            print("còn",len(remain),"dòng chưa gửi")
    else:
        os.remove(BUFFER_FILE)
        print("Xoá buffer xong")

def send_client_attributes(client):
    attributes = {
        "firmware_version": "2.1.0",
        "ip_address": "192.168.1.100",
        "device_model": "ESP32-Industrial",
        "installation_date": "2026-02-03"
    }
    client.publish("v1/devices/me/attributes",json.dumps(attributes),qos = 1)
    print("Đã gửi client attributes lên sever")

def on_message(client, userdata, msg):
    if "attributes/response" in msg.topic:
        payload = json.loads(msg.payload.decode())
        print("Attributes nhận từ server:", payload)
        if "shared" in payload:
            interval = payload["shared"].get("uploadInterval")
            if interval:
                print("Chu kỳ gửi mới:", interval)


client = mqtt.Client(client_id=CLIENT_ID,callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.max_queued_messages_set(0)
client.username_pw_set(ACCESSTOKEN)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message  
client.connect(HOST,PORT,keepalive=10)
client.loop_start()

try:
    while True:
        telemetry = {
            "temperature":random.randint(20,40),
            "humidity":random.randint(40,90)
        }
        if connected == True:
            result =  client.publish(TELEMETRY_TOPIC,json.dumps(telemetry),qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Gửi thành công")
                send_buffer_file(client)
            else:
                print("publish lỗi")
                save_buffer_file(telemetry)
        else:
            save_buffer_file(telemetry)
        time.sleep(5)
except KeyboardInterrupt:
    print("Dừng chương trình")
    client.loop_stop()
    client.disconnect()

    

            

