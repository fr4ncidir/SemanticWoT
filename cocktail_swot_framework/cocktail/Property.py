#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Property.py
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

from sepy.tablaze import tablify
from .InteractionPattern import InteractionPattern

import logging

logger = logging.getLogger("cocktail_log")


class Property(InteractionPattern):
    """
    swot:Property python implementation
    Extends InteractionPattern
    """
    
    def __init__(self, sepa, bindings):
        super().__init__(sepa, bindings)
        
    def post(self):
        """
        Posts the thing to the rdf store.
        """
        logger.info("Posting property {}: {}".format(self.name, self.uri))
        if (("newValue" in self._bindings) and (self._bindings["newValue"] != "")):
            self._sepa.update("ADD_UPDATE_PROPERTY", forcedBindings=self._bindings)
        else:
            self._sepa.update("ADD_UPDATE_PROPERTY_NOVALUE", forcedBindings=self._bindings)
        return self
        
    def update(self, bindings):
        """
        Updates the thing already present in the rdf store.
        """
        self._bindings = bindings
        self.post()
        
    @property
    def uri(self):
        return self._bindings["property"]
        
    @property
    def name(self):
        return self._bindings["newName"]
        
    @property
    def stability(self):
        return self._bindings["newStability"]
    
    @property
    def writability(self):
        return self._bindings["newWritability"]
        
    @property
    def value(self):
        return self._bindings["newValue"]
    
    @classmethod
    def getBindingList(self):
        return self._sepa.sap.updates["ADD_UPDATE_PROPERTY"]["forcedBindings"].keys()

    @staticmethod
    def discover(sepa, prop="UNDEF", nice_output=False):
        """
        Static method, used to discover properties in the rdf store.
        'prop' by default is 'UNDEF', retrieving every property. Otherwise
        it will be more selective.
        'nice_output' prints a nice table on console, using tablaze.
        """
        d_output = sepa.query(
            "DESCRIBE_PROPERTY", forcedBindings={"property_uri": prop})
        if nice_output:
            tablify(d_output, prefix_file=sepa.get_namespaces(stringList=True))
        if (prop != "UNDEF") and (len(d_output["results"]["bindings"]) > 1):
            raise Exception("Property discovery gave more than one result")
        return d_output
