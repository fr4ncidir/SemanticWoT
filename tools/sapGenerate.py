#!/usr/bin python3
# -*- coding: utf-8 -*-
#
#  sapGenerate.py
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
#  This script allows to easily create a ysap for the cocktail framework,
#  in order to start building your own applications.

import sys
import argparse

from cocktail import utils


def main(args):
    if args["sap_template"]:
        sap = utils.generate_cocktail_sap(args["destination"], jinjaTemplate=args["sap_template"])
    else:
        sap = utils.generate_cocktail_sap(args["destination"])
    print("Sap file was generated. You can now modify it.", file=sys.stderr)
    if args["destination"] is None:
        print(sap)
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SWoT Cocktail sap generator")
    parser.add_argument("--destination", default=None, help="Destination file")
    parser.add_argument("--sap_template", default=None, help="Jinja template for SAP file")
    arguments = vars(parser.parse_args())
    sys.exit(main(arguments))
