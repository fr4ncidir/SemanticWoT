#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  smart_clock.py
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

from dataschemas import ds_datetime, ds_lambda, YSAPEngine
from time import sleep, time
from datetime import datetime
from uuid import uuid4
from temperature import simulate

import sys

ClockURI = "<http://SmartClock.swot>"
ClockTD = "<http://SmartClock.swot/TD>"
TimeAction = "<http://SmartClock.swot/TimeAction>"
TemperatureAction = "<http://SmartClock.swot/TemperatureAction>"

def main(args):
    engine = YSAPEngine("./cocktail_sap.ysap")
    if "clear" in args:
        engine.clear()
    
    #
    # IDENTIFICATION AND DESCRIPTION OF INTERACTION PATTERNS
    # DEFINITION OF ACTIONS' BEHAVIOUR
    #
    def timeActionHandler(added, removed):
        print(added)
        if added != []:
            whatTimeIsIt.post_output(
                {"instance": added[0]["aInstance"]["value"], 
                 "oData": "<http://SmartClock.swot/TimeAction/Data_{}>".format(uuid4()),
                 "oValue": datetime.fromtimestamp(time()).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                 "oDS": ds_datetime})
        
    # Setup the Hot/Cold Action
    whatTimeIsIt = Action(
        engine,
        {"td": ClockTD,
         "action": TimeAction,
         "newName": "WhatTimeIsIt",
         "ods": ds_datetime},
         timeActionHandler)
    
    def temperatureActionHandler(added, removed):
        print(added)
        if added != []:
            whatTimeIsIt.post_output(
                {"instance": added[0]["aInstance"]["value"], 
                 "oData": "<http://SmartClock.swot/TemperatureAction/Data_{}>".format(uuid4()),
                 "oValue": str(simulate()),
                 "oDS": ds_lambda})
        
    whatsTheTemperature = Action(
        engine,
        {"td": ClockTD,
         "action": TemperatureAction,
         "newName": "WhatsTheTemperature",
         "ods": ds_lambda},
         temperatureActionHandler)
    
    #
    # POSTING THE TRIPLES TO THE SWTE
    #
    # Setup and post the WebThing
    smartClock = Thing(
        engine,
        {"thing": ClockURI,
         "newName": "SmartClock",
         "newTD": ClockTD}).post(interaction_patterns=[whatTimeIsIt, whatsTheTemperature])
         
    whatTimeIsIt.enable()
    whatsTheTemperature.enable()
    
    local_engine = YSAPEngine("./example.ysap")
    # adding context triples
    local_engine.update("ADD_THERMOSTAT_CONTEXT_TRIPLES", forcedBindings={"th": ClockURI})
    
    #
    # DEVICE LOOP
    #
    while True:
        try:
            sleep(10)
        except KeyboardInterrupt:
            print("Got KeyboardInterrupt!")
            whatTimeIsIt.disable()
            whatsTheTemperature.disable()
            break
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
