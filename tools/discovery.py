#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  discovery.py
#  
#  Copyright 2019 Francesco Antoniazzi <francesco.antoniazzi1991@gmail.com>
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
#  This tool allows easily to make standard discoveries over your SWTE
#  (Semantic WebThing Environment).
#  Use -h parameter to see what you can do with it.

import sys
import argparse
import yaml

from sepy.SEPA import SEPA
from sepy.SAPObject import SAPObject
from cocktail.Thing import Thing
from cocktail.Action import *
from cocktail.Event import *
from cocktail.Property import Property
from cocktail.DataSchema import DataSchema

from time import sleep


def prettySubscriptionPrint(tag, results):
    for index,item in enumerate(results):
        for key in item.keys():
            print("{}{}.\t{}\t({}):\t{}".format(tag, index, key, item[key]["type"], item[key]["value"]))


def subscription_handler(added, removed):
    if arguments["nice"]:
        prettySubscriptionPrint("+", added)
        prettySubscriptionPrint("-", removed)
    else:
        print("Added: {}".format(added))
        print("Removed: {}".format(removed))


def main(args):
    with open(args["ysap_file"], "r") as ysap_file:
        ysap = SAPObject(yaml.load(ysap_file))
    engine = SEPA(sapObject=ysap, logLevel=logging.ERROR)
    try:
        if not args["subscribe"]:
            # Plain queries using the direct cocktail call
            if args["thing"]:
                print("Thing discovery:")
                print(Thing.discover(engine, nice_output=args["nice"]))
            if args["action"]:
                print("Action discovery:")
                print(Action.discover(engine, nice_output=args["nice"]))
            if args["event"]:
                print("Event discovery:")
                print(Event.discover(engine, nice_output=args["nice"]))
            if args["property"]:
                print("Property discovery:")
                print(Property.discover(engine, nice_output=args["nice"]))
            if args["dataschema"]:
                print("DataSchema discovery:")
                print(DataSchema.discover(engine, nice_output=args["nice"]))
        else:
            # subscriptions, using the ysap entries.
            # BTW, the queries call the same entries! They just use a different method
            subids = []
            if args["thing"]:
                subids.append(engine.subscribe(
                    "DISCOVER_THINGS", 
                    "thing_discovery", handler=subscription_handler))
            if args["action"]:
                subids.append(engine.subscribe(
                    "DESCRIBE_ACTION", 
                    "action_discovery", handler=subscription_handler))
            if args["event"]:
                subids.append(engine.subscribe(
                    "DESCRIBE_EVENT", 
                    "event_discovery", handler=subscription_handler))
            if args["property"]:
                subids.append(engine.subscribe(
                    "DESCRIBE_PROPERTY", 
                    "property_discovery", handler=subscription_handler))
            if args["dataschema"]:
                subids.append(engine.subscribe(
                    "GET_DATASCHEMAS", 
                    "dataschema_discovery", handler=subscription_handler))
            if subids != []:
                try:
                    # Waits for subscription notifications
                    while True:
                        sleep(10)
                except KeyboardInterrupt:
                    print("Got Ctrl-C! Bye bye!")
                finally:
                    for subscription in subids:
                        engine.unsubscribe(subscription)
    except Exception as ex:
        print("Got exception while trying to contact SEPA:\n{}".format(ex), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SWoT discovery tool")
    parser.add_argument("-s", "--subscribe", action="store_true", help="Subscription discovery flag")
    parser.add_argument("-t", "--thing", action="store_true", help="Thing discovery")
    parser.add_argument("-a", "--action", action="store_true", help="Action discovery")
    parser.add_argument("-e", "--event", action="store_true", help="Event discovery")
    parser.add_argument("-p", "--property", action="store_true", help="Property discovery")
    parser.add_argument("-d", "--dataschema", action="store_true", help="DataSchema discovery")
    parser.add_argument("-n", "--nice", action="store_true", help="Nicer output flag")
    parser.add_argument("ysap_file", help="Path to cocktail ysap file")
    arguments = vars(parser.parse_args())
    sys.exit(main(arguments))
