#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Event.py
#  
#  Copyright 2018 Francesco Antoniazzi <francesco.antoniazzi@unibo.it>
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

from .InteractionPattern import InteractionPattern
from .Thing import Thing
from .utils import forPropertySparqlBuilder

from sepy.tablaze import tablify
from sepy.SAPObject import uriFormat

from enum import Enum
import logging

logger = logging.getLogger("cocktail_log")


class EType(Enum):
    OUTPUT_EVENT = "O"
    EMPTY_EVENT = "EMPTY"


class Event(InteractionPattern):
    """
    swot:Event python implementation
    Extends InteractionPattern
    """
    
    def __init__(self, sepa, bindings, forProperties=[], force_type=None):
        """
        Constructor of Event Item.
        'sepa' is the blazegraph/sepa instance.
        'bindings' is a dictionary formatted as required by the new-event yaml
        'forProperties' is a list containing the Properties that are linked
        to this action
        'force_type' is a flag which you can use to force the type of the
        event into O or EMPTY. To do so, use the EType enum.
        """
        super().__init__(sepa, bindings)
        if ("ods" in bindings.keys()) or (force_type is EType.OUTPUT_EVENT):
            self._type = EType.OUTPUT_EVENT
        else:
            self._type = EType.EMPTY_EVENT
        self._forProperties = forProperties
        self._observation_subid = None
        
    def post(self):
        self._sepa.update("ADD_{}_EVENT".format(self._type.value),
                          forcedBindings=self._bindings)
        logger.debug("Posting event {}: {}".format(self.name, self.uri))
        
        if self._forProperties:
            self._sepa.sparql_update(forPropertySparqlBuilder(
                self._sepa.sap, self.uri, self._forProperties))
        return self
        
    def notify(self, bindings):
        """
        Posts to the rdf store a notification, whose data in 'bindings'
        is formatted as in the new-event-instance yaml.
        """
        if ((self._type is EType.EMPTY_EVENT) or (("newValue" in bindings) and (bindings["newValue"] != ""))):
            self._sepa.update("NEW_{}_EVENT_INSTANCE".format(self._type.value),
                              forcedBindings=bindings)
        else:
            self._sepa.update("NEW_O_EVENT_INSTANCE_NOVALUE", forcedBindings=bindings)
        return bindings["newEInstance"]
    
    @property
    def uri(self):
        """Event URI getter"""
        return self._bindings["event"]
        
    @property
    def name(self):
        """Event name getter"""
        return self._bindings["eName"]
    
    @property
    def type(self):
        """Event EType getter"""
        return self._type
    
    @classmethod
    def getBindingList(self, event_type):
        """
        Utility function to know how you have to format the bindings for
        the constructor.
        """
        if event_type not in EType:
            raise ValueError
        return self._sepa.sap.updates["ADD_{}_EVENT".format(event_type.value)]["forcedBindings"].keys()
        
    def deleteInstance(self, instance):
        """
        Deletes a specific instance from the rdf store
        """
        super().deleteInstance(instance)
        logger.warning("Deleting Event instance "+instance)
        self._sepa.update("DELETE_EVENT_INSTANCE",
                          forcedBindings={"eInstance": instance})
        
    @staticmethod
    def discover(sepa, event="UNDEF", nice_output=False):
        """
        Static method, used to discover events in the rdf store.
        'event' by default is 'UNDEF', retrieving every event available.
        Otherwise it will be more selective
        'nice_output' prints a nice table on console, using tablaze.
        """
        d_output = sepa.query("DESCRIBE_EVENT",
                              forcedBindings={"event_uri": event})
        if nice_output:
            tablify(d_output, prefix_file=sepa.get_namespaces(stringList=True))
        if (event != "UNDEF") and (len(d_output["results"]["bindings"]) > 1):
            raise Exception("Event discovery gave more than one result")
        return d_output
        
    @staticmethod
    def buildFromQuery(sepa, eventURI):
        """
        Static method to build a local copy of an event by querying the
        rdf store.
        'eventURI' is the uri of the event needed.
        """
        query_event = Event.discover(sepa, event=eventURI)
        query_ip = InteractionPattern.discover(
            sepa, ip_type="swot:Event", nice_output=False)
        for binding in query_ip["results"]["bindings"]:
            if binding["ipattern"]["value"] == eventURI.replace("<", "").replace(">", ""):
                td = uriFormat(binding["td"]["value"])
        eBinding = query_event["results"]["bindings"][0]
        out_bindings = {"td": td,
                        "event": uriFormat(eBinding["event"]["value"]),
                        "eName": eBinding["eName"]["value"]}
        if "oDS" in eBinding.keys():
            out_bindings["ods"] = uriFormat(eBinding["oDS"]["value"])
        query_thing = Thing.discover(sepa, bindings={"td_uri": td})
        out_bindings["thing"] = uriFormat(query_thing["results"]["bindings"][0]["thing"]["value"])
        return Event(sepa, out_bindings)
    
    def observe(self, handler):
        """
        Subscribes to event notifications coming from eventURI.
        'handler' deals with the task to be performed in such situation.
        """
        if self._observation_subid is None:
            self._observation_subid = self._sepa.subscribe(
                "SUBSCRIBE_EVENT_INSTANCE", self.uri, 
                forcedBindings=self._bindings, handler=handler)
            logger.info("Started observation of {}: id-{}".format(
                self.uri, self._observation_subid))
        else:
            logger.info("{} already observed".format(self.uri))
        
    def stop_observing(self):
        """
        No more notifications will be received of the event.
        """
        if self._observation_subid is not None:
            logger.info("Stopped observation of {}: id-{}".format(
                self.uri, self._observation_subid))
            self._sepa.unsubscribe(self._observation_subid)
            self._observation_subid = None
        else:
            logger.warning("Observation of {} already stopped".format(self.uri))
