#!/usr/bin/env python3

from pprint import pprint
import time
import socket
#import simplejson as json
import json

class Tectectec:
    def __init__(self):
        self.tcp_connect()
        self.token = 0
        self.params = {}
        self.send_message(id=257)
        self.send_message(id=2, type="camera_clock", param=time.strftime("%Y-%m-%d %H:%M:%S"))
        self.send_message(id=3, buffer=2048)

    def tcp_connect(self):
        ip = '192.168.42.1'
        port = 7878
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))

    def send_message(self, id, param="", type="", buffer=1024):
        message = {'msg_id': id, 'token': self.token, 'type': type, 'param': param}
        print(message)

        self.socket.send(json.dumps(message, separators=(',', ':')).encode())
        data_string = self.socket.recv(buffer).decode()

        try:
            data = json.loads(data_string)
            print(data_string)

            if id == 3:
                for param in data["param"]:
                    pprint(param)
                    for key in param:
                        self.params[key] = param[key]
            if id == 257:
                self.token = data["param"]

        except ValueError:
            print('JSON error')

    def start_video_recording(self):
        if self.params["sys_mode"] != "record":
            self.send_message(id=2, type="Switch_mode", param="video")
        self.send_message(id=513)

    def stop_video_recording(self):
        self.send_message(id=514)


def main():
    camera = Tectectec()
    print(camera.params['video_resolution'])
    #camera.start_video_recording()
    #time.sleep(5)
    #camera.stop_video_recording()
    #camera.send_message(id=3, buffer=2048)

main()

