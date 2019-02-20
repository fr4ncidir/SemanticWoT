#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  thermostat.py
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

import sys
from temperature import simulate

from cocktail.Thing import Thing
from cocktail.Action import *
from cocktail.Event import *

from time import sleep
from uuid import uuid4
from threading import Lock

from dataschemas import ds_threshold, ds_lambda, ds_psi, YSAPEngine


ThermostatURI = "<http://MyThermostat.swot>"
ThermostatTD = "<http://MyThermostat.swot/TD>"
T_low = 15
T_high = 27

thresholdLock = Lock()
actuatorListLock = Lock()
actuatorList = []
engine = None


def main(args):
    global engine
    # opening the sap file, and creating the SEPA instance
    engine = YSAPEngine("./cocktail_sap.ysap")
    if "clear" in args:
        engine.clear()
    
    #
    # IDENTIFICATION OF INTERACTION PATTERNS
    #
    # Setup the Threshold Action
    threshold_Action = Action(
        engine,
        {"td": ThermostatTD,
         "action": "<http://MyThermostat.swot/ThresholdAction>",
         "newName": "ThresholdAction",
         "ids": ds_threshold},
         threshold_update)
    
    # Setup the Event
    temperature_Event = Event(
        engine,
        {"td": ThermostatTD,
         "event": "<http://MyThermostat.swot/TemperatureEvent>",
         "eName": "TemperatureEvent",
         "ods": ds_lambda})
    
    #
    # POSTING TRIPLES TO THE SWTE
    #
    # Setup and post the WebThing
    thermostat = Thing(
        engine,
        {"thing": ThermostatURI,
         "newName": "SmartThermostat",
         "newTD": ThermostatTD}).post(
            interaction_patterns=[threshold_Action, temperature_Event])
    
    local_engine = YSAPEngine("./example.ysap")
    
    #
    # OPTIONAL THING DESCRIPTION JSON-LD
    #
    thermostat.tdServer_start("localhost",8321)
    
    # adding context triples
    local_engine.update("ADD_THERMOSTAT_CONTEXT_TRIPLES", forcedBindings={"th": ThermostatURI})
    
    # enabling threshold Action
    threshold_Action.enable()
    
    # main thermostat triggering logic
    local_engine.subscribe(
        "THERMOSTAT_SMART_DISCOVERY", 
        "thermostat_subscription", 
        forcedBindings={"ds": ds_psi}, 
        handler=available_actuators)
    
    #
    # DEVICE LOOP
    #
    # temperature Event triggering logic
    event_bindings = {"event": temperature_Event.uri, "newDS": ds_lambda}
    try:
        while True:
            sleep(2)
            unique_id = uuid4()
            event_bindings["newEInstance"] = "<http://MyThermostat.swot/TemperatureEvent/Instance_{}>".format(unique_id)
            event_bindings["newOData"] = "<http://MyThermostat.swot/TemperatureEvent/Data_{}>".format(unique_id)
            # in the real world this simulate() call would be a read to a temperature sensor!
            event_bindings["newValue"] = str(simulate())
            temperature_Event.notify(event_bindings)
            with thresholdLock:
                if float(event_bindings["newValue"]) < T_low:
                    message = '{{"target": {}, "now": "warming"}}'.format(T_low)
                    trigger_action(message)
                elif float(event_bindings["newValue"]) > T_high:
                    message = '{{"target": {}, "now": "cooling"}}'.format(T_high)
                    trigger_action(message)
    except KeyboardInterrupt:
        print("Got KeyboardInterrupt!")
    except Exception as ex:
        print("Temperature simulation failed! Check the simulation server: {}".format(ex))
    threshold_Action.disable()
    thermostat.tdServer_stop()
    return 0


def threshold_update(added, removed):
    #
    # DEFINITION OF ACTION'S BEHAVIOUR
    #
    with thresholdLock:
        print("threshold_update added: {}".format(added))
        print("threshold_update removed: {}".format(removed))
    
def available_actuators(added, removed):
    with actuatorListLock:
        for item in added:
            print("Available actuator found: {}".format(item["action"]["value"]))
            actuatorList.append(item["action"]["value"])
        for item in removed:
            actuatorList.remove(item["action"]["value"])
    
def trigger_action(message):
    with actuatorListLock:
        if actuatorList == []:
            print("No trigger targets!")
        else: 
            print("Triggering {} - {}".format(actuatorList, message))
            bindings = {"newAuthor": ThermostatURI, "newIValue": message, "newIDS": ds_psi}
            for action in actuatorList:
                action_object = Action.buildFromQuery(engine, action)
                unique_id = uuid4()
                bindings["action"] = action
                bindings["newAInstance"] = "<http://MyThermostat.swot/Request/Instance_{}>".format(unique_id)
                bindings["newIData"] = "<http://MyThermostat.swot/Request/Data_{}>".format(unique_id)
                instance, subids = action_object.newRequest(bindings)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
