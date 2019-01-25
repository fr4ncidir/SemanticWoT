#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  hotcold.py
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

from cocktail.Thing import Thing
from cocktail.Action import *
from cocktail.Event import *
from cocktail.Property import *

from dataschemas import ds_psi, ds_lambda, YSAPEngine
from time import sleep
from threading import Lock

import json
import sys


HotColdURI = "<http://HotCold.swot>"
HotColdTD = "<http://HotCold.swot/TD>"
HotColdActionURI = "<http://HotCold.swot/MainHotColdAction>"
HotColdPropertyURI = "<http://HotCold.swot/MainHotColdProperty>"
temperatureSensorsList = {}
engine = None

HC_Property_lock = Lock()
HC_Property = None
HC_Property_bindings = {}

def main(args):
    global engine
    global HC_Property_bindings
    global HC_Property
    # opening the sap file, and creating the SEPA instance
    engine = YSAPEngine("./cocktail_sap.ysap")
    if "clear" in args:
        engine.clear()
        
    # Setup the Hot/Cold Action
    mainHC_Action = Action(
        engine,
        {"td": HotColdTD,
         "action": HotColdActionURI,
         "newName": "MainHotColdAction",
         "ids": ds_psi},
         mainHotColdActionLogic)
    
    HC_Property_bindings = {"td": HotColdTD,
         "property": HotColdPropertyURI,
         "newName": "InternalStatusHotColdProperty",
         "newStability": "0",
         "newWritability": "false",
         "newDS": ds_psi,
         "newPD": "<http://HotCold.swot/MainHotColdProperty/Data>",
         "newValue": '{"now": "off", "target": "15"}'}
    HC_Property = Property(engine, HC_Property_bindings)
    
    # Setup and post the WebThing
    thermostat = Thing(
        engine,
        {"thing": HotColdURI,
         "newName": "HotCold",
         "newTD": HotColdTD}).post(interaction_patterns=[mainHC_Action, HC_Property])
         
    mainHC_Action.enable()
    
    local_engine = YSAPEngine("./example.ysap")
    # adding context triples
    local_engine.update("ADD_HOTCOLD_CONTEXT_TRIPLES", forcedBindings={"hc": HotColdURI})

    # main hotcold event search logic
    local_engine.subscribe(
        "HOTCOLD_SMART_DISCOVERY", 
        "hotcold_subscription", 
        forcedBindings={"ds": ds_lambda}, 
        handler=available_sensors)
    
    try:
        while True:
            sleep(10)
            print("Device status is currently {}".format(HC_Property.value))
    except KeyboardInterrupt:
        print("Got KeyboardInterrupt!")
    mainHC_Action.disable()
    return 0
    

def updatePropertyValWithLock(newVal):
    global HC_Property_lock
    global HC_Property_bindings
    global HC_Property
    with HC_Property_lock:
        HC_Property_bindings["newValue"] = newVal
        HC_Property = Property(engine, HC_Property_bindings).post()

def mainHotColdActionLogic(added, removed):
    for item in added:
        parameter = json.loads(item["iValue"]["value"])
        author = item["author"]["value"]
        if parameter["now"] == json.loads(HC_Property.value)["now"]:
            print("Ignoring {}'s request: already doing it".format(author))
        else:
            print("{} requested execution of {} at {} with parameter {}".format(
                author, HotColdActionURI, item["aTS"]["value"], parameter))
            updatePropertyValWithLock(item["iValue"]["value"])
    

def available_sensors(added, removed):
    # elaborate the list
    for item in added:
        event = item["event"]["value"]
        if event not in temperatureSensorsList.keys():
            sensorEvent = Event.buildFromQuery(engine, event)
            temperatureSensorsList[event] = sensorEvent
        print("Available sensor found: {}".format(event))
        temperatureSensorsList[event].observe(temperature_handler)
    for item in removed:
        temperatureSensorsList[item["event"]["value"]].stop_observing()
    
    
def temperature_handler(added, removed):
    global HC_Property
    property_json_value = json.loads(HC_Property.value)
    CurrentStatus = property_json_value["now"]
    CurrentTarget = property_json_value["target"]
    for item in added:
        temperature = float(item["oValue"]["value"])
        print("Received new temperature: {}°C".format(temperature))
        if ((CurrentStatus=="warming") and (temperature > CurrentTarget)) or ((CurrentStatus=="cooling") and (temperature < CurrentTarget)):
            print("Switching off the heating/cooling device")
            property_json_value["now"] = "off"
            updatePropertyValWithLock(str(property_json_value).replace("'",'"'))
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
