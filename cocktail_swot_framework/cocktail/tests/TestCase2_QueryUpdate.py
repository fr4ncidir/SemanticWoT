#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  TestCase2_QueryUpdate.py
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

import json

from cocktail.Thing import Thing
from cocktail.DataSchema import DataSchema
from cocktail.Property import Property
from cocktail.Action import *
from cocktail.Event import *
from cocktail.utils import *
from cocktail import __name__ as cName

from sepy.SEPA import SEPA
from sepy.SAPObject import SAPObject

from pkg_resources import resource_filename
from os.path import isfile, splitext
from os import listdir


def read_all_file(filename):
    path = resource_filename(__name__, filename)
    with open(path, "r") as myFile:
        content = myFile.read()
    return content


def switch_handler(added_bindings, result_file, ignore=[]):
    if not added_bindings:
        return True
    else:
        full_added = {}
        full_added["head"] = {}
        full_added["head"]["vars"] = [
            key for item in added_bindings for key in item.keys()]
        full_added["results"] = {}
        full_added["results"]["bindings"] = added_bindings
        return compare_queries(
            resource_filename(__name__, result_file),
            full_added, ignore_val=ignore, strictVars=False, show_diff=True)


class TestCase2_QueryUpdate(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sap_file = generate_cocktail_sap(None)
        self.ysap = SAPObject(yaml.load(sap_file))
        self.engine = SEPA(sapObject=self.ysap, logLevel=logging.INFO)

    def setUp(self):
        self.engine.clear()
        self.engine.sparql_update(read_all_file("insert_dataschemas.sparql"))
        self.engine.sparql_update(read_all_file("insert_thing_1.sparql"))
        self.engine.sparql_update(read_all_file("insert_thing_2.sparql"))
        self.engine.sparql_update(read_all_file("insert_thing_3.sparql"))

    def test_0(self):
        self.assertTrue(compare_queries(
            self.engine.query_all(),
            resource_filename(__name__, "res_query_all.json"),
            show_diff=True))

    def test_1(self):
        """
        This function performs all the queries available in ./queries folder, 
        and checks the corresponding result if there is coincidence. In 
        case of reset==True, results file are rewritten.
        True or False is returned for success or failure.
        """
        dir_path = resource_filename(cName, "queries")
        for fileName in listdir(dir_path):
            filePath = dir_path + "/" + fileName
            if (isfile(filePath) and (splitext(filePath)[1] == ".sparql")):
                sapKey = list(sparqlFolderToSap(
                    dir_path, file_filter=fileName).keys())[0]
                self.assertTrue(
                    compare_queries(
                        self.engine.query(sapKey),
                        resource_filename(
                            __name__,
                            splitext("res_"+fileName)[0]+".json")))

    def test_2(self):
        """
        This function performs checks for adding and removing all is 
        needed for a new web thing. In case reset==True, the specific 
        thing query result file is rebuilt.
        True or False is returned for success or failure.
        """
        SUPERTHING = "<http://MyFirstWebThing.com>"
        THING_URI = "<http://TestThing.com>"

        # Adding new thing within the forced bindings
        dummyThing = Thing(
            self.engine, {"thing": THING_URI,
                          "newName": "TEST-THING",
                          "newTD": "<http://TestTD.com>"},
            superthing=SUPERTHING).post()

        sparql_query = self.ysap.getQuery("DISCOVER_THINGS").replace(
            "(UNDEF UNDEF UNDEF)",
            "({} UNDEF UNDEF) ({} UNDEF UNDEF)".format(THING_URI,
                                                       SUPERTHING))
        query_result = self.engine.sparql_query(sparql_query)
        self.assertTrue(compare_queries(
            query_result,
            resource_filename(__name__, "res_new_thing.json"),
            show_diff=True))

        # Passing through this point also in reset case allows not to
        # refresh the RDF store into the following test.
        # Deleting the thing, and checking if the triples in all the store
        # are the same as if all the test never happened
        dummyThing.delete()

        # With this line, if it outputs True, we certify that the contents
        # of the RDF store are exactly the same as they were at the beginning
        # of this function. So, no need to call reset_testbase
        self.test_0()

    def test_3(self):
        """
        This function performs checks for adding, updating and removing
        a new Property to a web thing. Notice that to do so, it is required
        to test also DataSchema and FieldSchema updates. Those two classes
        are not made to be removed, because they can always be used by
        other things.

        TODO The procedure to remove them is more complex and involves
        some queries before performing the delete.

        In case reset==True, check jsons are updated. However, the plain
        'res_query_all' is not overwritten, because the presence of new
        DataSchema and FieldSchema here requires the existance of a different
        file named 'res_query_all_new_dataschema.json'.

        True or False is returned for success or failure.
        """
        THING_URI = "<http://TestThing.com>"
        PROPERTY_URI = "<http://TestProperty.com>"
        NEW_PROPERTY_VALUE = "HIJKLMNOP"
        TEST_TD = "<http://TestTD.com>"

        # Adding the new thing
        dummyThing = Thing(
            self.engine,
            {"thing": THING_URI,
             "newName": "TEST-THING",
             "newTD": TEST_TD}).post()
        # Adding the property
        p_fBindings = {"td": TEST_TD,
                       "property": PROPERTY_URI,
                       "newName": "TEST-PROPERTY",
                       "newStability": "1",
                       "newWritability": "true",
                       "newDS": "<http://XSDstringDataSchema.org>",
                       "newPD": "<http://TestThing.com/Property1/PropertyData>",
                       "newValue": "ABCDEFG"}
        testProperty = Property(self.engine, p_fBindings).post()

        # Querying the property to check it
        query_result = self.engine.query(
            "DESCRIBE_PROPERTY",
            forcedBindings={"property_uri": PROPERTY_URI})
        res_new_property_create = json.loads(
            read_all_file("res_new_property_create.json"))
        self.assertTrue(compare_queries(
            query_result, res_new_property_create))

        # Updating property with a new writability and a new value
        p_fBindings["newWritability"] = "false"
        p_fBindings["newValue"] = NEW_PROPERTY_VALUE
        testProperty.update(p_fBindings)

        res_new_property_create["results"]["bindings"][0]["pWritability"]["value"] = "false"
        res_new_property_create["results"]["bindings"][0]["pValue"]["value"] = NEW_PROPERTY_VALUE
        res_new_property_update = resource_filename(
            __name__, "res_new_property_update.json")

        self.assertTrue(compare_queries(
            res_new_property_create, res_new_property_update, show_diff=True))
        query_result = self.engine.query(
            "DESCRIBE_PROPERTY",
            forcedBindings={"property_uri": PROPERTY_URI})
        self.assertTrue(compare_queries(
            query_result, res_new_property_update, show_diff=True))

        # Deleting the property
        testProperty.delete()
        # Query all check
        dummyThing.delete()
        self.assertTrue(compare_queries(
            self.engine.query_all(),
            resource_filename(__name__, "res_query_all_new_dataschema.json"),
            show_diff=True))

    def test_4(self):
        """
        This function performs checks for adding, updating and removing
        Actions to a web thing. Notice that to do so, it is required to
        test also DataSchema and FieldSchema updates. Those two classes
        are not made to be removed, because they can always be used by
        other things.

        TODO The procedure to remove them is more complex and involves
        some queries before performing the delete.

        In case reset==True, check jsons are updated. However, the plain
        'res_query_all' is not overwritten, because the presence of new
        DataSchema and FieldSchema here requires the existance of a different
        file named 'res_query_all_new_dataschema.json'.

        True or False is returned for success or failure.
        """
        THING_URI = "<http://TestThing.com>"

        # Adding the new thing
        dummyThing = Thing(self.engine,
                           {"thing": THING_URI,
                            "newName": "TEST-THING",
                            "newTD": "<http://TestTD.com>"}).post()

        # Adding new Actions and then query the output
        actions = []
        for aType in list(AType):
            actions.append(Action(
                self.engine,
                {"td": "<http://TestTD.com>",
                 "action": "<http://TestAction_{}.com>".format(aType.value.lower()),
                 "newName": "TEST-ACTION-{}".format(aType.value.lower()),
                 "ids": "<http://XSDstringDataSchema.org>",
                 "ods": "<http://XSDintegerDataSchema.org>"},
                lambda: None,
                force_type=aType).post())

        sparql_query = self.ysap.getQuery("DESCRIBE_ACTION").replace(
            "(UNDEF)",
            "(<http://TestAction_io.com>) (<http://TestAction_i.com>) (<http://TestAction_o.com>) (<http://TestAction_empty.com>)")
        query_result = self.engine.sparql_query(sparql_query)
        self.assertTrue(compare_queries(
            query_result,
            resource_filename(__name__, "res_new_actions_create.json"),
            show_diff=True))

        # Deleting the actions
        for action in actions:
            action.delete()
        # Query all check
        dummyThing.delete()
        self.assertTrue(compare_queries(
            self.engine.query_all(),
            resource_filename(
                __name__, "res_query_all_new_dataschema_actions.json"),
            show_diff=True))

    def test_5(self):
        """
        This function performs checks for adding, updating and removing
        Events to a web thing. Notice that to do so, it is required to test
        also DataSchema and FieldSchema updates. Those two classes are not
        made to be removed, because they can always be used by other things.

        TODO The procedure to remove them is more complex and involves
        some queries before performing the delete.

        In case reset==True, check jsons are updated. However, the plain
        'res_query_all' is not overwritten, becausen the presence of new
        DataSchema and FieldSchema here requires the existance of a different
        file named 'res_query_all_new_dataschema.json'.

        True or False is returned for success or failure.
        """
        THING_URI = "<http://TestThing.com>"

        # Adding the new thing
        dummyThing = Thing(self.engine,
                           {"thing": THING_URI,
                            "newName": "TEST-THING",
                            "newTD": "<http://TestTD.com>"}).post()

        # Adding new Actions and then query the output
        events = []
        for eType in list(EType):
            events.append(Event(
                self.engine,
                {"td": "<http://TestTD.com>",
                 "event": "<http://TestEvent_{}.com>".format(eType.value.lower()),
                 "eName": "TEST-EVENT-{}".format(eType.value.lower()),
                 "ods": "<http://XSDintegerDataSchema.org>"}, force_type=eType).post())

        # Querying the events
        sparql_query = self.engine.sap.getQuery("DESCRIBE_EVENT").replace(
            "(UNDEF)",
            "(<http://TestEvent_o.com>) (<http://TestEvent_empty.com>)")
        query_result = self.engine.sparql_query(sparql_query)
        self.assertTrue(compare_queries(
            query_result,
            resource_filename(__name__, "res_new_events_create.json")))

        # Deleting the events
        for event in events:
            event.delete()
        # Query all check
        dummyThing.delete()
        self.assertTrue(compare_queries(
            self.engine.query_all(),
            resource_filename(
                __name__, "res_query_all_new_dataschema_events.json"),
            show_diff=True))

    def test_6(self):
        """
        The procedure to test the action request/response sequence is the
        following. Given the standard content of the RDF store, we update
        a new action instance. We then check that the subscription query
        contains all data required. We add also timestamps, that are necessary
        items for the following steps. Outputs, if present, are checked.
        Delete is then performed.

        Consider that the update "new_empty_action_instance.sparql" is
        used also for output actions, and that "new_i_action_instance.sparql"
        is used also for input-output actions.

        The action here tested is Input-Output, which means we test all
        kind i-o-io actions in one. We test also the empty action.
        """
        # retrieving actions from SEPA: those are inferred
        actions = [
            Action.buildFromQuery(
                self.engine, "<http://MyFirstWebThing.com/Action1>"),
            Action.buildFromQuery(
                self.engine, "<http://MyThirdWebThing.com/Action1>")]

        # copying inferred actions, building up real ones. This is to test
        # subscription responsiveness
        actions_copy = [
            Action.buildFromQuery(
                self.engine, "<http://MyFirstWebThing.com/Action1>"),
            Action.buildFromQuery(
                self.engine, "<http://MyThirdWebThing.com/Action1>")]

        # Adding the instances
        for index, action in enumerate(actions):
            # defining the action task testing behavior
            task_iteration = 0
            action_type = action.type.value.lower()

            def deep_action_task(added, removed):
                nonlocal task_iteration
                if added:
                    if task_iteration == 0:
                        self.assertTrue(switch_handler(
                            added,
                            "res_new_{}_action_instance.json".format(action_type),
                            ignore=["aTS"]))
                    else:
                        self.assertTrue(switch_handler(
                            added,
                            "res_new_{}_action_instance_update.json".format(action_type),
                            ignore=["aTS"]))
                    task_iteration += 1
            actions_copy[index].action_task = deep_action_task
            actions_copy[index].enable()  # triggers task_iteration==0

            bindings = {"thing": action.thing,
                        "action": action.uri,
                        "newAInstance": action.uri.replace(">", "/instance1>"),
                        "newAuthor": "<http://MySecondWebThing.com>",
                        "newIData": action.uri.replace(">", "/instance1/InputData>"),
                        "newIValue": "This is an input string",
                        "newIDS": "<http://XSDstringDataSchema.org>"}

            def confirm_handler(added, removed):
                self.assertTrue(switch_handler(
                    added, "res_new_confirmation_ts.json", ignore=["ts"]))
                if added:
                    self.engine.unsubscribe(subids["confirm"])

            def complete_handler(added, removed):
                self.assertTrue(switch_handler(
                    added, "res_new_completion_ts.json", ignore=["ts"]))
                if added:
                    self.engine.unsubscribe(subids["completion"])

            # the following line triggers task_iteration==1,
            # confirm_iteration==0, complete_iteration==0
            instance, subids = action.newRequest(
                bindings, confirm_handler=confirm_handler,
                completion_handler=complete_handler)

            # Adding and checking Confirmation and Completion timestamps
            actions_copy[index].post_confirmation(instance)  # triggers confirm_iteration==1
            actions_copy[index].post_completion(instance)  # triggers complete_iteration==1
            # Update the instances
            bindings["newAInstance"] = action.uri.replace(">", "/instance2>")
            if action.type == AType.INPUT_ACTION:
                bindings["newIData"] = action.uri.replace(">", "/instance2/InputData>")
                bindings["newIValue"] = "This is a modified input string"

            def out_handler(added, removed):
                self.assertTrue(switch_handler(
                    added, "res_new_instance_output.json"))
                if added:
                    self.engine.unsubscribe(subids["output"])

            instance, subids = action.newRequest(
                bindings, confirm_handler=confirm_handler,
                completion_handler=complete_handler,
                output_handler=out_handler)

            # Adding and checking Confirmation and Completion timestamps
            actions_copy[index].post_confirmation(instance)  # triggers confirm_iteration==1
            actions_copy[index].post_completion(instance)  # triggers complete_iteration==1
            if action.type == AType.IO_ACTION or action.type == AType.OUTPUT_ACTION:
                # Post output
                actions_copy[index].post_output(
                    {"instance": instance,
                     "oData": action.uri.replace(">", "/instance2/OutputData>"),
                     "oValue": "my output value",
                     "oDS": "<http://XSDstringDataSchema.org>"})
            # Remove instances and outputs
            actions_copy[index].disable()
            actions_copy[index].deleteInstance(instance)
        self.test_0()

    def test_7(self):
        """
        The procedure to test the event throwing/receive sequence is the
        following. Given the standard content of the RDF store, we update
        a new event instance. We then check that the subscription query
        contains all data required. Outputs, if present, are checked.
        Delete is then performed.
        """
        events = [
            Event.buildFromQuery(self.engine,
                                 "<http://MyFirstWebThing.com/Event1>"),
            Event.buildFromQuery(self.engine,
                                 "<http://MyThirdWebThing.com/Event1>")]

        # Adding the instances
        for index, event in enumerate(events):
            bindings = {"thing": event.thing,
                        "event": event.uri,
                        "newEInstance": event.uri.replace(">", "/instance1>"),
                        "newOData": event.uri.replace(">", "/instance1/OutputData>"),
                        "newValue": "2018-06-23T10:05:19.478Z",
                        "newDS": "<http://XSDdateTimeStampDataSchema.org>"}

            notification_iteration = 0

            def event_monitor(added, removed):
                nonlocal notification_iteration
                if added:
                    if notification_iteration == 0:
                        self.assertTrue(switch_handler(
                            added,
                            "res_new_{}_event_instance.json".format(event.type.value.lower()),
                            ignore=["eTS"]))
                    else:
                        self.assertTrue(switch_handler(
                            added,
                            "res_new_{}_event_instance_update.json".format(event.type.value.lower()),
                            ignore=["eTS"]))
                    notification_iteration += 1

            events[index].observe(event_monitor)
            instance = event.notify(bindings)

            # Update the instances
            bindings["newEInstance"] = event.uri.replace(">", "/instance2>")
            if event.type is EType.OUTPUT_EVENT:
                bindings["newOData"] = event.uri.replace(">", "/instance2/OutputData>")
                bindings["newValue"] = "2018-06-23T17:05:19.478Z"
            instance = event.notify(bindings)

            # Remove instances and outputs
            events[index].stop_observing()
            event.deleteInstance(instance)
        self.test_0()


if __name__ == '__main__':
    unittest.main(failfast=True)
