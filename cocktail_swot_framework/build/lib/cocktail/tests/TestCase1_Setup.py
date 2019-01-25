#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  TestCase1_Setup.py
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

import unittest
import yaml

from pkg_resources import resource_filename

from sepy.SEPA import SEPA
from sepy.SAPObject import SAPObject

from cocktail.Thing import Thing
from cocktail.DataSchema import DataSchema
from cocktail.Property import Property
from cocktail.Action import *
from cocktail.Event import *
from cocktail.utils import generate_cocktail_sap, compare_queries

ds_string = "<http://XSDstringDataSchema.org>"
ds_integer = "<http://XSDintegerDataSchema.org>"
ds_dateTimeStamp = "<http://XSDdateTimeStampDataSchema.org>"
ds_genericWebResource = "<http://GenericWebResourceDataSchema.org>"
ds_json = "<http://jsonDataSchema.org>"
ds_foaf = "<http://foafDataSchema.org>"


def read_all_file(filename):
    path = resource_filename(__name__, filename)
    with open(path, "r") as myFile:
        content = myFile.read()
    return content


class TestCase1_Setup(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sap_file = generate_cocktail_sap(None)
        self.ysap = SAPObject(yaml.load(sap_file))
        self.engine = SEPA(sapObject=self.ysap, logLevel=logging.ERROR)
        
    def setUp(self):
        self.engine.clear()
        
    def test_0(self):
        """
        This test checks if the sparql insert of Thing1 and the sum of
        cocktail sparqls have the same effect in the rdf store.
        """
        self.engine.sparql_update(read_all_file("insert_dataschemas.sparql"))
        self.engine.sparql_update(read_all_file("insert_thing_1.sparql"))
        
        thing_descriptor = "<http://MyFirstWebThingDescription.com>"
        query_all_sparql = self.engine.query_all()
        self.engine.clear()
        self.engine.sparql_update(read_all_file("insert_dataschemas.sparql"))

        thing1_uri = "<http://MyFirstWebThing.com>"

        property1 = Property(
            self.engine,
            {"td": thing_descriptor,
             "property": "<http://MyFirstWebThing.com/Property1>",
             "newName": "Thing1_Property1",
             "newStability": "1000",
             "newWritability": "true",
             "newDS": ds_string,
             "newPD": "<http://MyFirstWebThing.com/Property1/PropertyData>",
             "newValue": "Hello World!"})
        action1 = Action(
            self.engine,
            {"thing": thing1_uri,
             "td": thing_descriptor,
             "action": "<http://MyFirstWebThing.com/Action1>",
             "newName": "Thing1_Action1",
             "ids": ds_string,
             "ods": ds_genericWebResource},
            lambda: print("ACTION 1 HANDLER RUN"))
        action2 = Action(
            self.engine,
            {"thing": thing1_uri,
             "td": thing_descriptor,
             "action": "<http://MyFirstWebThing.com/Action2>",
             "newName": "Thing1_Action2",
             "ods": ds_integer},
            lambda: print("ACTION 2 HANDLER RUN"),
            forProperties=[property1])
        event1 = Event(
            self.engine,
            {"td": thing_descriptor,
             "event": "<http://MyFirstWebThing.com/Event1>",
             "eName": "Thing1_Event1",
             "ods": ds_dateTimeStamp})
        thing1 = Thing(
            self.engine,
            {"thing": thing1_uri,
             "newName": "Thing1",
             "newTD": thing_descriptor}).post(
                interaction_patterns=[property1, action1, action2, event1])
        
        self.assertTrue(compare_queries(self.engine.query_all(),
                                        query_all_sparql,
                                        show_diff=True))
        
    def test_1(self):
        """
        This test checks if the sparql insert of Thing2 and the sum of
        cocktail sparqls have the same effect in the rdf store.
        """
        thing_descriptor = "<http://MySecondWebThingDescription.com>"
#        self.engine.sap.update_namespaces(
#            "foaf", "http://xmlns.com/foaf/0.1/")
        self.engine.sparql_update(read_all_file("insert_dataschemas.sparql"))
        self.engine.sparql_update(read_all_file("insert_thing_2.sparql"))
        query_all_sparql = self.engine.query_all()
        self.engine.clear()
        self.engine.sparql_update(read_all_file("insert_dataschemas.sparql"))
          
        thing1 = Thing(
            self.engine,
            {"thing": "<http://MySecondWebThing.com>",
             "newName": "Thing2",
             "newTD": thing_descriptor}).post()
        property1 = Property(
            self.engine,
            {"td": thing_descriptor,
             "property": "<http://MySecondWebThing.com/Property1>",
             "newName": "Thing2_Property1",
             "newStability": "0",
             "newWritability": "false",
             "newDS": ds_json,
             "newPD": "<http://MySecondWebThing.com/Property1/PropertyData>",
             "newValue": '{"json":"content"}'}).post()
        property2 = Property(
            self.engine,
            {"td": thing_descriptor,
             "property": "<http://MySecondWebThing.com/Property2>",
             "newName": "Thing2_Property2",
             "newStability": "75",
             "newWritability": "true",
             "newDS": ds_string,
             "newPD": "<http://MySecondWebThing.com/Property2/PropertyData>",
             "newValue": "Whatever kind of binary content"}).post()
        action1 = Action(
            self.engine,
            {"thing": thing1.uri,
             "td": thing_descriptor,
             "action": "<http://MySecondWebThing.com/Action1>",
             "newName": "Thing2_Action1",
             "ids": ds_foaf,
             "ods": ds_string},
            lambda: print("ACTION 1 HANDLER RUN"),
            forProperties=[property1, property2]).post()
        event1 = Event(
            self.engine,
            {"td": thing_descriptor,
             "event": "<http://MySecondWebThing.com/Event1>",
             "eName": "Thing2_Event1",
             "ods": ds_integer},
            forProperties=[property2]).post()
        event2 = Event(
            self.engine,
            {"td": thing_descriptor,
             "event": "<http://MySecondWebThing.com/Event2>",
             "eName": "Thing2_Event2",
             "ods": ds_genericWebResource}).post()
        query_all_cocktail = self.engine.query_all()
        self.assertTrue(compare_queries(
            query_all_cocktail, query_all_sparql, show_diff=True))
        
    def test_2(self):
        """
        This test checks if the sparql insert of Thing3 and the sum of 
        cocktail sparqls have the same effect in the rdf store.
        """
        thing_descriptor = "<http://MyThirdWebThingDescription.com>"
        self.engine.sparql_update(read_all_file("insert_thing_3.sparql"))
        query_all_sparql = self.engine.query_all()
        self.engine.clear()

        thing1 = Thing(
            self.engine,
            {"thing": "<http://MyThirdWebThing.com>",
             "newName": "Thing3",
             "newTD": thing_descriptor}).post()
        action1 = Action(
            self.engine,
            {"thing": thing1.uri,
             "td": thing_descriptor,
             "action": "<http://MyThirdWebThing.com/Action1>",
             "newName": "Thing3_Action1"},
            lambda: print("ACTION 1 HANDLER RUN")).post()
                                
        event1 = Event(
            self.engine,
            {"td": thing_descriptor,
             "event": "<http://MyThirdWebThing.com/Event1>",
             "eName": "Thing3_Event1"}).post()
        query_all_cocktail = self.engine.query_all()
        self.assertTrue(compare_queries(
            query_all_cocktail, query_all_sparql, show_diff=True))

if __name__ == '__main__':
    unittest.main(failfast=True)
