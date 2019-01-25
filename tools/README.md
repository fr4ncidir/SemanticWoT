# Cocktail tools

- `sapGenerate.py`
- `discovery.py`

##### Prerequisites
- [SAP](http://mml.arces.unibo.it/TR/jsap.html) file
- [SEPA](https://github.com/arces-wot/SEPABins)
- [sepy](https://github.com/arces-wot/SEPA-python3-APIs/tree/dev-0.9.5) APISs (branch dev-0.9.5)
- [SWoT ontology](https://github.com/fr4ncidir/SemanticWoT/blob/master/swot.owl) concepts

### How-To `sapGenerate.py`
The use of `sapGenerate.py` is needed, most of the time, if you want to create new applications that work with Cocktail. The SAP file is a necessary entity used with SEPA. 

In this file is contained the list of all SPARQL interactions that Cocktail may need to perform. You may be interested in modify them, or to add your own special discoveries.

In addition to this, the SAP file contains the informations about how to reach the SEPA. Therefore, once you generate the template, the first thing to do is to customize it with the IPs and Ports of your running SEPA instance.

You can generate a YAML compliant sap by calling
```
$ python3 sapGenerate.py > path_to_destination_file
```
and, for more detailed information, 
```
$ python3 sapGenerate.py -h
```

### How-To `discovery.py`
This tool is useful to test the basic types of discoveries that Cocktail is able to perform in the SWTE. If you look to the help
```
$ python3 discovery.py -h
```
you will see that a few discoveries are available

- Thing discovery
- Action discovery
- Event discovery
- Property discovery
- DataSchema discovery

that can also be combined. You can perform discoveries as a query, or as a subscription, and get the raw results coming from SEPA or with a nicer format.

Of course, to run this tool you need a running instance of SEPA, and therefore the tool requires a compulsory parameter: the path to a Cocktail ysap file in which you have customized IPs and Ports of you own SEPA.

Notice that if you make some changes to the ysap, you can make the tool performing different kind of discoveries...