#!/usr/bin/env python3

from pprint import pprint
from optparse import OptionParser
import sys
import time
import socket
import json
import re
import telnetlib

class Tectectec:
    def __init__(self):
        self.tcp_connect()
        self.token = 0
        self.params = {}
        # get a token thanks to this message
        self.send_message(id=257)
        # get camera config
        self.send_message(id=3, buffer=2048)
        # this message is sent by android app
        self.send_message(id=259,param="none_force")
        # setting up camera clock
        self.send_message(id=2, type="camera_clock", param=time.strftime("%Y-%m-%d %H:%M:%S"))

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
            self.last_data = data
            if "rval" in data and data["rval"] != 0:
                print("returned value error: ", data["rval"])
                sys.exit(5)

            if id == 3:
                for param in data["param"]:
                    for key in param:
                        self.params[key] = param[key]
            if id == 257:
                self.token = data["param"]

        except ValueError:
            print(data_string)
            print('JSON error')


    def get_config(self):
        self.send_message(id=3, buffer=2048)
        pprint(self.params)

    def switch_mode(self, mode):
        self.send_message(id=260)
        self.send_message(id=3, buffer=2048)
        if self.params['sys_mode'] != mode:
            self.send_message(id=2, type="Switch_mode", param=mode)

    def photo_size(self, size):
        self.send_message(id=260)

        # get supported photo sizes
        # XPRO4+ supported photo sizes
        # "16M (4608x3456 4:3)","14M (4352x3264 4:3)","12M (4000x3000 4:3)","8.3M (3840x2160 16:9)","5M (2560x1920 4:3)","3M (2048x1536 4:3)"
        self.send_message(id=9, param="photo_size")
        regex=re.compile("^" + size  + ".*")
        matching_supported_sizes = [m.group(0) for l in self.last_data['options'] for m in [regex.search(l)] if m]
        if len(matching_supported_sizes) != 0:
            self.send_message(id=2, type="photo_size", param=matching_supported_sizes[0])
        else:
            print('Not supported photo size matching', size)
            sys.exit(4)

    def video_resolution(self, resolution):
        self.send_message(id=260)

        # supported video resolutions
        # XPRO4+ supported videos resolutions
        # "3840x2160 30P 16:9","3840x2160 25P SuperView","2880x2160 30P 4:3","2704x2028 30P 4:3","2704x1520 30P SuperView","2704x1520 30P 16:9","2560x1440 60P 16:9","2560x1440 30P 16:9","1920x1440 60P 4:3","1920x1440 30P 4:3","1920x1080 120P 16:9","1920x1080 100P 16:9","1920x1080 60P 16:9","1920x1080 30P 16:9","1920x1080 60P SuperView","1920x1080 30P SuperView","1280x960 120P 4:3","1280x960 60P 4:3","1280x960 30P 4:3","1280x720 240P 16:9","1280x720 200P 16:9","1280x720 120P 16:9","1280x720 60P 16:9","1280x720 30P 16:9","1280x720 120P SuperView","1280x720  30P SuperView"
        self.send_message(id=9, param="video_resolution")
        if resolution not in self.last_data['options']:
            print(resolution, 'is not in supported video resolutions')
            sys.exit(4)

        self.send_message(id=2, type="video_resolution", param=resolution)

    def start_video_recording(self):
        if self.params["switch_mode"] != "record":
            self.send_message(id=2, type="Switch_mode", param="video")
        self.send_message(id=513)

    def stop_video_recording(self):
        self.send_message(id=514)

    def video_timelapse(self, time):
        self.send_message(id=260)
        self.send_message(id=9, param="video_timelapse")
        self.send_message(id=2, type="video_timelapse", param=time)


def stop_wifi():
    telnet = telnetlib.Telnet('192.168.42.1')
    telnet.set_debuglevel(0)
    telnet.read_until(b'a12 login:')
    telnet.write(b'root\n')
    telnet.read_until(b'#')
    telnet.write(b"/usr/local/share/script/wifi_stop.sh & /usr/local/share/script/unload.sh & /usr/bin/SendToRTOS net_off\n")
    telnet.read_until(b'#')
    telnet.close()
    print("Wifi stopped")

def set_options():
    parser = OptionParser()
    parser.add_option("--config", dest="get_config",
                      action="store_true",
                      help="show camera config",
                      default=False)
    parser.add_option("--mode", dest="switch_mode",
                      help="Mode : record (video) or capture (photo)",
                      default="record")
    parser.add_option("--videoresolution", dest="video_resolution",
                      help="video resolution and frame per second",
                      default="1920x1440 30P 4:3")
    parser.add_option("--videotimelapse", dest="video_timelapse",
                      help="active video timelapse",
                      default="off")
    parser.add_option("--photosize", dest="photo_size",
                      help="photo resolution",
                      default="16M")
    parser.add_option("--videostart", dest="videostart",
                      action="store_true",
                      help="start recording",
                      default=False)
    parser.add_option("--videostop", dest="videostop",
                      action="store_true",
                      help="stop recording",
                      default=False)
    parser.add_option("--mapillary", dest="mapillary",
                      action="store_true",
                      help="configure camera for Mapillary : 2880x2160 30P 4:3 + timelapse 2s",
                      default=False)
#    parser.add_option("--stopwifi", dest="wifistop",
#                      action="store_false",
#                      help="stop WiFi",
#                      default=True)

    (options, args) = parser.parse_args()

    if options.mapillary:
        options.video_resolution = '2880x2160 30P 4:3'
        options.video_timelapse = '2s'
        options.switch_mode = 'record'

    return(options)


def main():

    options = set_options()

    camera = Tectectec()
    camera.photo_size(options.photo_size)
    camera.video_resolution(options.video_resolution)
    camera.video_timelapse(options.video_timelapse)
    camera.switch_mode(options.switch_mode)

    if options.get_config:
        camera.get_config()
    elif options.videostart:
        camera.start_video_recording()
    elif options.videostop:
        camera.stop_video_recording()

if __name__ == "__main__":
    main()

# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
