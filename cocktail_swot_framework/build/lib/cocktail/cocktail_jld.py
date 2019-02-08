#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  cocktail_jld.py
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


from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from time import asctime
from rdflib import Graph, Literal, BNode, URIRef
from pyld import jsonld

import logging
import json


logger = logging.getLogger("cocktail_log")
bnode_id = {}


def graphNodeBuilder(binding):
    global bnode_id
    bindingValue = binding["value"]
    if binding["type"] == "uri":
        return URIRef(bindingValue)
    elif binding["type"] == "literal":
        return Literal(bindingValue)
    elif bindingValue in bnode_id.keys():
        return bnode_id[bindingValue]
    else:
        bnode_id[bindingValue] = BNode()
        return bnode_id[bindingValue]


def jldTaskBuilder(jld_content):
    class JLDServerTask(BaseHTTPRequestHandler):
        def do_GET(self):
            self.respond()
        
        def handle_http(self, status, content_type):
            self.send_response(status)
            self.send_header("Content-type", content_type)
            self.end_headers()
            result = bytes(jld_content, "UTF-8")
            return result

        def respond(self):
            content = self.handle_http(200, "application/json-ld")
            self.wfile.write(content)
    return JLDServerTask
    
def jldFileBuilder(construct_result, frame=None):
    thingGraph = Graph()
    for binding in construct_result["results"]["bindings"]:
        # subject
        s = graphNodeBuilder(binding["subject"])
        # predicate
        p = graphNodeBuilder(binding["predicate"])
        # object
        o = graphNodeBuilder(binding["object"])
        thingGraph.add((s, p, o))
    jld_result = thingGraph.serialize(format="json-ld").decode("utf-8")
    if frame:
        jld_frame = json.loads(frame)
        jld_result_framed = jsonld.frame(json.loads(jld_result), jld_frame)
        return json.dumps(jld_result_framed, indent=4)
    return jld_result

class JLDServer(Thread):
    def __init__(self, ip, port, jld_content):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.httpd = None
        self.jld_content = jld_content

    def run(self):
        self.httpd = HTTPServer((self.ip, self.port), jldTaskBuilder(self.jld_content))
        logger.debug(asctime(), 'Server UP - {}:{}'.format(self.ip, self.port))
        self.httpd.serve_forever()
        logger.debug(asctime(), 'Server DOWN - {}:{}'.format(self.ip, self.port))
        
    def kill(self):
        self.httpd.server_close()
