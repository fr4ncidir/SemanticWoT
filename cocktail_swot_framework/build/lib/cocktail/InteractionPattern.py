#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  InteractionPattern.py
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

from abc import abstractmethod
from sepy.tablaze import tablify

import logging

logger = logging.getLogger("cocktail_log")


class InteractionPattern:
    """
    Interface implementing the wot:InteractionPattern
    """
    
    def __init__(self, sepa, bindings):
        self._sepa = sepa
        self._bindings = bindings

    @property
    def bindings(self):
        return self._bindings
    
    @property
    def td(self):
        return self._bindings["td"]
        
    @property
    def thing(self):
        return self._bindings["thing"] if "thing" in self._bindings.keys() else None    
    
    @thing.setter
    def thing(self, thingURI):
        self._bindings["thing"] = thingURI
    
    def setSepa(self, new_sepa):
        self._sepa = new_sepa
        
    def delete(self):
        """
        InteractionPattern deletion is the same for every possible case
        """
        if "property" in self._bindings.keys():
            tag = "property"
        elif "event" in self._bindings.keys():
            tag = "event"
        elif "action" in self._bindings.keys():
            tag = "action"
        else:
            raise ValueError("Bad bindings!")
        self._sepa.update("DELETE_INTERACTION_PATTERN",
                          forcedBindings={"ip": self._bindings[tag]})
        
    @abstractmethod
    def post(self):
        pass
    
    @classmethod
    @abstractmethod
    def getBindingList(self):
        pass
    
    @staticmethod
    @abstractmethod
    def discover(sepa, td_uri="UNDEF", ip_type="UNDEF", nice_output=False):
        """
        Generic InteractionPattern discovery. Can be more selective by giving
        'td_uri' and 'ip_type' params.
        'nice_output' prints to console a table with the result.
        """
        d_output = sepa.query(
            "DISCOVER_INTERACTION_PATTERNS",
            forcedBindings={"td_uri": td_uri, "ipattern_type_specific": ip_type})
        if nice_output:
            tablify(d_output, prefix_file=sepa.get_namespaces(stringList=True))
        return d_output
        
    def deleteInstance(self, instance):
        pass
