#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dataschemas.py
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
import yaml

from cocktail.DataSchema import DataSchema

from sepy.SEPA import SEPA
from sepy.SAPObject import SAPObject
from time import sleep


ds_threshold = "<http://ThresholdJSON-DS>"
ds_psi = "<http://HotColdJSON-DS>"
ds_lambda = "<http://FloatDataSchema>"
ds_datetime = "<http://DateTimeDataSchema>"


def YSAPEngine(path_to_ysap):
    with open(path_to_ysap, "r") as sap_file:
        ysap = SAPObject(yaml.load(sap_file))
    return SEPA(sapObject=ysap)


def main(args):
    # opening the sap file, and creating the SEPA instance
    engine = YSAPEngine("./cocktail_sap.ysap")
    if "clear" in args:
        engine.clear()
    
    threshold_dataschema = DataSchema(
        engine,
        {"ds_uri": ds_threshold,
         "fs_uri": "<http://localhost:9876/threshold>",
         "fs_types": "swot:FieldSchema, xsd:Literal"}).post()
    threshold_dataschema.dsServer_start("localhost", 8322)
         
    hotcold_dataschema = DataSchema(
        engine,
        {"ds_uri": ds_psi,
         "fs_uri": "<http://localhost:9876/hotcold>",
         "fs_types": "swot:FieldSchema, xsd:Literal"}).post()
    hotcold_dataschema.dsServer_start("localhost", 8323)
         
    temperature_dataschema = DataSchema(
        engine,
        {"ds_uri": ds_lambda,
         "fs_uri": "_:FloatFS-BlankNode",
         "fs_types": "swot:FieldSchema, xsd:float"}).post()
    temperature_dataschema.dsServer_start("localhost", 8324)
         
    datetime_dataschema = DataSchema(
        engine,
        {"ds_uri": ds_datetime,
         "fs_uri": "_:DatetuneFS-BlankNode",
         "fs_types": "swot:FieldSchema, xsd:dateTime"}).post()
    datetime_dataschema.dsServer_start("localhost", 8325)
    
    print("Ctrl-C to stop servers...")
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        print("Ctrl-C caught, stopping servers...")
    
    threshold_dataschema.dsServer_stop()
    hotcold_dataschema.dsServer_stop()
    temperature_dataschema.dsServer_stop()
    datetime_dataschema.dsServer_stop()
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
