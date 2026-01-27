import paho.mqtt.client as mqtt
import json
import time
import os

HOST = "thingsboard.cloud"
PORT = 8883
ACCESS_TOKEN = "QtQPpZuSBaSPmiRQzSDa"
TOPIC = "v1/devices/me/telemetry"
BUFFER_FILE = "testpy.txt"


connected = False


def save_to_file(data_json):
    with open(BUFFER_FILE, "a", encoding="utf-8") as f:
        f.write(data_json + "\n")
    print("Đã lưu vào file tạm")

def send_buffer_file():
    if not os.path.exists(BUFFER_FILE):
        return

    with open(BUFFER_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return

    print("Đang gửi lại dữ liệu tồn...")

    for line in lines:
        line = line.strip()
        if line:
            result = client.publish(TOPIC, line)
            result.wait_for_publish(timeout=2)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Đã gửi lại dữ liệu:", line)
                time.sleep(0.2)
            else:
                print("Gửi lại thất bại, giữ file lại")
                return  


    os.remove(BUFFER_FILE)
    print("Đã gửi xong dữ liệu tồn, xoá file buffer_file")


def on_connect(client, userdata, flags, reasonCode, properties=None):
    global connected
    if reasonCode == 0:
        connected = True
        print("Kết nối thành công")
        send_buffer_file()   
    else:
        connected = False
        print("Kết nối thất bại, code =", reasonCode)


def on_disconnect(client, userdata, reasonCode, properties=None):
    global connected
    connected = False
    print("Mất kết nối, code =", reasonCode)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.reconnect_delay_set(min_delay=1, max_delay=10)

client.username_pw_set(ACCESS_TOKEN)
client.on_connect = on_connect
client.on_disconnect = on_disconnect

print("Đang kết nối MQTT...")

try:
    client.tls_set()
    client.tls_insecure_set(True)  
    client.connect(HOST, PORT, 60)
    client.loop_start()
except Exception as e:
    print("Không kết nối được MQTT:", e)
    connected = False

time.sleep(2)


while True:


    if not connected:
        try:
            print("Thử reconnect MQTT...")
            client.reconnect()
        except Exception as e:
            print("Reconnect thất bại:", e)

    if connected:
        send_buffer_file()

    data = {
        "temperature": 155,
        "ts": int(time.time() * 1000)
    }

    data_json = json.dumps(data)

    try:
        try:
            result = client.publish(TOPIC, data_json)
            result.wait_for_publish(timeout=2)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Gửi temperature thành công:", data_json)
            else:
                print("Publish lỗi (rc=%s) -> lưu file" % result.rc)
                save_to_file(data_json)

        except Exception as e:
            print("Exception khi publish:", e)
            save_to_file(data_json)


    except Exception as e:
        print("Exception khi publish:", e)
        save_to_file(data_json)

    time.sleep(5)
