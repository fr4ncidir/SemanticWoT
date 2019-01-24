#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  Thing.py
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

from sepy.SAPObject import uriFormat
from sepy.tablaze import tablify

from enum import Enum
import logging

logger = logging.getLogger("cocktail_log")


class AType(Enum):
    IO_ACTION = "IO"
    INPUT_ACTION = "I"
    OUTPUT_ACTION = "O"
    EMPTY_ACTION = "EMPTY"


class Action(InteractionPattern):
    """
    swot:Action python implementation.
    Extends InteractionPattern
    """
    
    def __init__(self, sepa, bindings, action_task,
                 forProperties=[], force_type=None):
        """
        Constructor of Action Item. 
        'sepa' is the blazegraph/sepa instance.
        'bindings' is a dictionary formatted as required by the new-action yaml
        'action_task' is the function that is triggered when the action is
        requested. When the Action is built from a query with the 'buildFromQuery'
        method, this field is left None. In this case, we say that the Action
        is 'inferred', and some methods throw exception.
        'forProperties' is a list containing the Properties that are linked
        to this action
        'force_type' is a flag which you can use to force the type of the
        action into IO, O, I, EMPTY. To do so, use the AType enum.
        """
        super().__init__(sepa, bindings)
        self._action_task = action_task
        if (("ods" in bindings.keys()) and ("ids" in bindings.keys())) or (force_type is AType.IO_ACTION):
            self._type = AType.IO_ACTION
        elif ("ods" in bindings.keys()) or (force_type is AType.OUTPUT_ACTION):
            self._type = AType.OUTPUT_ACTION
        elif ("ids" in bindings.keys()) or (force_type is AType.INPUT_ACTION):
            self._type = AType.INPUT_ACTION
        else:
            self._type = AType.EMPTY_ACTION
        self._forProperties = forProperties
        self._enable_subid = None
    
    @property
    def uri(self):
        return self._bindings["action"]
        
    @property
    def name(self):
        return self._bindings["newName"]
        
    @property
    def action_task(self):
        return self._action_task
    
    @action_task.setter
    def action_task(self, new_action_task):
        self._action_task = new_action_task
    
    def post(self):
        """
        This method is not available if the Action is inferred.
        Posts the Action to the rdf store, together with its forced bindings.
        """
        assert not self.isInferred()
        self._sepa.update(
            "ADD_{}_ACTION".format(self._type.value),
            forcedBindings=self._bindings)
        logger.debug("Posting action {}: {}".format(self.name, self.uri))
        
        if self._forProperties:
            self._sepa.sparql_update(forPropertySparqlBuilder(
                self._sepa.sap, self.uri, self._forProperties))
        return self
        
    def enable(self):
        """
        This method is not available if the Action is inferred.
        Subscribe to action requests
        """
        if self._enable_subid is None:
            assert not self.isInferred()
            logger.info("Enabling Action "+self.uri)
            self._enable_subid = self._sepa.subscribe(
                "SUBSCRIBE_ACTION_INSTANCE", self.uri,
                forcedBindings=self._bindings, handler=self._action_task)
        else:
            logger.warning("{} already enabled".format(self.uri))
        return self
        
    def disable(self):
        """
        This method is not available if the Action is inferred.
        Unsubscribe to action requests. Action will be disabled until 'enable'
        is called again
        """
        # unsubscribe to action requests
        if self._enable_subid is not None:
            assert not self.isInferred()
            logger.info("Disabling Action "+self.uri)
            self._sepa.unsubscribe(self._enable_subid)
            self._enable_subid = None
        else:
            logger.warning("{} already disabled".format(self.uri))
        
    def post_output(self, bindings):
        """
        This method is not available if the Action is inferred.
        Post to rdf store the output of an action computation
        """
        assert not self.isInferred()
        if (self._type is AType.OUTPUT_ACTION) or (self._type is AType.IO_ACTION):
            logger.debug("Posting output for instance "+bindings["instance"])
            if (("oValue" in bindings) and (bindings["oValue"] != "")):
                self._sepa.update("NEW_ACTION_INSTANCE_OUTPUT",
                                  forcedBindings=bindings)
            else:
                self._sepa.update("NEW_ACTION_INSTANCE_OUTPUT_NOVALUE",
                                  forcedBindings=bindings)
            self.post_completion(bindings["instance"])
           
    def post_completion(self, instance):
        """
        This method is not available if the Action is inferred.
        This method posts completion triple to an action instance
        """
        logger.debug("Posting completion for instance "+instance)
        self._post_timestamp("COMPLETION", instance)
        
    def post_confirmation(self, instance):
        """
        This method is not available if the Action is inferred.
        This method posts confirmation triple to an action instance
        """
        logger.debug("Posting confirmation for instance "+instance)
        self._post_timestamp("CONFIRMATION", instance)
    
    def _post_timestamp(self, ts_type, instance):
        # This method is not available if the Action is inferred.
        assert not self.isInferred()
        if (ts_type.upper() != "COMPLETION") and (ts_type.upper() != "CONFIRMATION"):
            raise ValueError("Only 'completion' and 'confirmation' are valid keys")
        self._sepa.update("ADD_{}_TIMESTAMP".format(ts_type.upper()),
                          forcedBindings={"aInstance": instance})
        
    @property
    def type(self):
        """
        Getter for the Action type: IO, EMPTY, I, O
        """
        return self._type
    
    @classmethod
    def getBindingList(self, action_type):
        """
        Utility function to know how you have to format the bindings for
        the constructor.
        """
        if action_type not in AType:
            raise ValueError
        return self._sepa.sap.updates["NEW_{}_ACTION".format(action_type.value)]["forcedBindings"].keys()

    @staticmethod
    def discover(sepa, action="UNDEF", nice_output=False):
        """
        Static method, used to discover actions in the rdf store.
        'action' by default is 'UNDEF', retrieving every action. Otherwise
        it will be more selective
        'nice_output' prints a nice table on console, using tablaze.
        """
        d_output = sepa.query("DESCRIBE_ACTION",
                              forcedBindings={"action_uri": action})
        if nice_output:
            d_output = tablify(d_output, prefix_file=sepa.sap.get_namespaces(stringList=True), destination=None)
        if (action != "UNDEF") and (len(d_output["results"]["bindings"]) > 1):
            raise Exception("Action discovery gave more than one result")
        return d_output
    
    @staticmethod
    def buildFromQuery(sepa, actionURI):
        """
        Static method to build an inferred local copy of an action by
        querying the rdf store.
        'actionURI' is the uri of the action needed.
        """
        query_action = Action.discover(sepa, action=actionURI)
        query_ip = InteractionPattern.discover(
            sepa, ip_type="swot:Action", nice_output=False)
        for binding in query_ip["results"]["bindings"]:
            if binding["ipattern"]["value"] == actionURI.replace("<", "").replace(">", ""):
                td = uriFormat(binding["td"]["value"])
        aBinding = query_action["results"]["bindings"][0]
        out_bindings = {"td": td,
                        "action": uriFormat(aBinding["action"]["value"]),
                        "newName": aBinding["aName"]["value"]}
        if "oDS" in aBinding.keys():
            out_bindings["ods"] = uriFormat(aBinding["oDS"]["value"])
        if "iDS" in aBinding.keys():
            out_bindings["ids"] = uriFormat(aBinding["iDS"]["value"])
        query_thing = Thing.discover(sepa, bindings={"td_uri": td})
        out_bindings["thing"] = uriFormat(query_thing["results"]["bindings"][0]["thing"]["value"])
        return Action(sepa, out_bindings, None)
    
    def newRequest(self, bindings, confirm_handler=None,
                   completion_handler=None, output_handler=None):
        """
        Used by clients, this method allows to ask to perform an action.
        'bindings' contains the information needed by the new-action-instance
        sparql.
        Returns the instance uri, and the subids for subscriptions in the
        form {"confirm": None,"completion": None,"output": None}
        """
        assert self.isInferred()
        subids = {"confirm": None, "completion": None, "output": None}
        if confirm_handler is not None:
            # in case i'm interested in capturing the confirm flag
            subids["confirm"] = self._sepa.subscribe(
                "SUBSCRIBE_CONFIRMATION_TS", bindings["newAInstance"],
                forcedBindings={"aInstance": bindings["newAInstance"]},
                handler=confirm_handler)
        if completion_handler is not None:
            # in case i'm interested in capturing the completion flag
            subids["completion"] = self._sepa.subscribe(
                "SUBSCRIBE_COMPLETION_TS", bindings["newAInstance"],
                forcedBindings={"aInstance": bindings["newAInstance"]},
                handler=completion_handler)
        if output_handler is not None:
            # in case i'm interested in capturing the output
            subids["output"] = self._sepa.subscribe(
                "SUBSCRIBE_INSTANCE_OUTPUT", bindings["newAInstance"],
                forcedBindings={"instance": bindings["newAInstance"]},
                handler=output_handler)
        req_type = AType.INPUT_ACTION.value if (self._type is AType.INPUT_ACTION or self._type is AType.IO_ACTION) else AType.EMPTY_ACTION.value
        if req_type is AType.EMPTY_ACTION:
            self._sepa.update("NEW_EMPTY_ACTION_INSTANCE", forcedBindings=bindings)
        elif (("newIValue" in bindings) and (bindings["newIValue"] != "")):
            self._sepa.update("NEW_I_ACTION_INSTANCE", forcedBindings=bindings)
        else:
            self._sepa.update("NEW_I_ACTION_INSTANCE_NOVALUE", forcedBindings=bindings)
        return bindings["newAInstance"], subids
            
    def isInferred(self):
        """
        An action is 'inferred' when the task to be performed when receiving
        an instance is None. You have an inferred action when you are not the 
        owner of the action, i.e. you just have a remote representation
        of the action, and use it to request instances to the real one which
        is elsewhere and has the action_task filled with a real routine.
        """
        return (self._action_task is None)
        
    def deleteInstance(self, instance):
        """
        This method is not available if the Action is inferred.
        Deletes the instance from the rdf store.
        """
        super().deleteInstance(instance)
        assert not self.isInferred()
        self._sepa.update(
            "DELETE_ACTION_INSTANCE", forcedBindings={"aInstance": instance})
