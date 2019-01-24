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

from sepy.SAPObject import SAPObject
from sepy.tablaze import tablify
from .utils import generate_cocktail_sap

import logging
import yaml

logger = logging.getLogger("cocktail_log")


class DataSchema:
    """
    wot:DataSchema python implementation
    """
    def __init__(self, sepa, bindings):
        self._sepa = sepa
        self._bindings = bindings
        
    @property
    def bindings(self):
        return self._bindings
        
    @property
    def uri(self):
        return self._bindings["ds_uri"]

    def post(self):
        """
        Post to the SEPA a new dataschema
        """
        self._sepa.update("NEW_DATASCHEMA", forcedBindings=self._bindings)
        return self
        
    @staticmethod
    def getBindingList(sap_object=None):
        """
        Give as input to this function a SAPObject containing the Cocktail
        sap, (or None, if you want to generate it on-the-go), to see the
        bindings necessary to build up a DataSchema.
        """
        if sap_object is None:
            sap = SAPObject(yaml.load(generate_cocktail_sap(None)), log=logging.ERROR)
            result = sap.updates["NEW_DATASCHEMA"]["forcedBindings"].keys()
        else:
            result = sap_object.updates["NEW_DATASCHEMA"]["forcedBindings"].keys()
        return result
        
    
    @staticmethod
    def discover(sepa, ds="UNDEF", nice_output=False):
        """
        Discovers dataschemas in the knowedge base. Can be more selective
        by defining 'ds' field, and print nice output setting to True the
        'nice_output' flag.
        """
        d_output = sepa.query("GET_DATASCHEMAS", forcedBindings={"ds_force": ds})
        if nice_output:
            d_output = tablify(d_output, prefix_file=sepa.sap.get_namespaces(stringList=True), destination=None)
        return d_output

    def delete(self):
        raise NotImplementedError
