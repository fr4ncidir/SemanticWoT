#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  temperature.py
#  
#  Copyright 2018 Francesco Antoniazzi <francesco.antoniazzi1991@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
#
# This is software simulating the temperature in a room. The temperature
# can be queried as we would do with a sensor. It is, therefore, not part
# of cocktail but only of the example.

import sys
import json
import requests
import tkinter as tk

from http.server import HTTPServer, BaseHTTPRequestHandler

from cocktail.Property import *
from dataschemas import YSAPEngine
from threading import Thread, Lock
from time import sleep, asctime

current_temp = -1
now = "off"
tempLock = Lock()


def simulate():
    r = requests.get("http://localhost:8001")
    r.connection.close()
    return float(r.text)


class TempThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.alive = True
        
    def run(self):
        global now
        global tempLock
        global current_temp
        while self.alive:
            sleep(1)
            with tempLock:
                if now != "off":
                    if now == "warming":
                        current_temp += 0.5
                    else:
                        current_temp -= 0.5
        print("Run ended!")
                        
    def stop(self):
        print("Called stop (TempThread)!")
        self.alive = False


class TempSetupThread(Thread):        
    def run(self):
        def update_temp():
            nonlocal content
            global tempLock
            global current_temp
            with tempLock:
                try:
                    current_temp = float(content.get())
                except ValueError:
                    pass
        window = tk.Tk()
        window.title("Cocktail example")
        window.geometry("300x90")
        label = tk.Label(window, text="Insert new temperature")
        label.pack()
        content = tk.Entry(window)
        content.pack()
        button = tk.Button(window, text="OK", command=update_temp)
        button.pack()
        window.mainloop()
        print("Shutting down temperature GUI")
    

class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond()
    
    def handle_http(self, status, content_type):
        global current_temp
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        with tempLock:
            result = current_temp
        return bytes(str(result), "UTF-8")
    
    def respond(self):
        content = self.handle_http(200, "application/integer")
        self.wfile.write(content)


def temperatureHandler(added, removed):
    global tempLock
    global now
    for item in added:
        with tempLock:
            now = json.loads(item["pValue"]["value"])["now"]


def main(args):
    params = {}
    params["HostName"] = "localhost"
    params["PortNumber"] = 8001
    httpd = HTTPServer((params["HostName"], params["PortNumber"]), Server)
        
    tempT = TempThread()
    tempT.daemon = True
    tempT.start()
    guithread = TempSetupThread()
    guithread.daemon = True
    guithread.start()
    engine = YSAPEngine("./cocktail_sap.ysap")
    subid = engine.subscribe("DESCRIBE_PROPERTY", "tempsimulator", 
        forcedBindings={"property_uri": "<http://HotCold.swot/MainHotColdProperty>"}, 
        handler=temperatureHandler)
    print(asctime(), 'Server UP - {}:{}'.format(
        params["HostName"], params["PortNumber"]))
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(" Got KeyboardInterrupt!")
    httpd.server_close()
    print(asctime(), 'Server DOWN - {}:{}'.format(
        params["HostName"], params["PortNumber"]))
    engine.unsubscribe(subid)
    tempT.stop()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
