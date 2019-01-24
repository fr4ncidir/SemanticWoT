# Cocktail
Within this repository we store all the necessary to start with a Semantic 
Web Of Things implementation. 

### 1. The SWoT Ontology
Before using Cocktail, we suggest to have a look to the SWoT ontology.

### 2. Cocktail python3 framework
##### Basic setup
To run, and use, the APIs for the Semantic Web of Things, you need
- A running [SEPA]() instance
- The SEPA python3 APIs, available in [sepy](https://github.com/arces-wot/SEPA-python3-APIs/tree/dev-0.9.5) repository. *Be Careful! Use the branch dev-0.9.5*

Cocktail uses those APIs to post Things and their descriptions. In particular, you may 
want to have a look to the `SEPA.py` python3 class.

As Cocktail builds up in SEPA's RDF knowledge base a Semantic WebThing Environment, a SEPA instance is required in almost every method within Cocktail. 

Therefore, here an example of how to instantiate a SEPA:
1. run the SEPA instance
2. create a Cocktail SAP file. The SAP file is an entity related to SEPA, where all the information about how the application will interact with it is contained (IP-port, SPARQLs,...). Have a look to the tools available in this repository to create an YSAP (which stands for YAML-SAP).
3. Code your application
```
with open(path_to_ysap_file, "r") as ysap_file:
    ysap = SAPObject(yaml.load(ysap_file))
engine = SEPA(sapObject=ysap, logLevel=logging.ERROR)
```
For more complex situations, please refer to sepy repo documentation or the various example available in this repository.

Once SEPA has been declared, you may want to define your first WebThing. 
A WebThing is made up of some Actions, some Events, some Properties. 
Additionally, there may be the possibility to declare their parameter's
`DataSchema` and `FieldSchema`. Therefore,

##### Building WebThings
1. Define your WebThing. So,
```
myThing = Thing(myEngine,bindings,superThing=None)
```
where `superthing` might be left unused, if your WebThing is not represented 
on the Web by another WebThing. In such case, you would put here the URI 
of that WebThing.
`myEngine` is the `Sepa` instance;
`bindings` is a python3 dictionary that should be formatted as in the 
corresponding `.sparql` file. In that case,
```
bindings = {
    "thing":"",
    "newName":"",
    "newTD":""
}
```
2. Declare your Actions, calling 
```
myAction = Action(myEngine,bindings,action_task,forProperties=[],force_type=None)
```
`bindings`, in this case, has to be formatted according to the `.sparql`
available in the `updates` folder. For instance, if you are creating an
`IO` Action, you would have
```
bindings = {
   "td":"",
   "action":"",
   "newName":"",
   "ids":"",
   "ods":""
}
```
As you can see, the `td` field is required: this means that you need to
know prior to creating the Action (but also the other InteractionPatterns)
which is the WebThing you will connect this Action to. In the `td` entry you 
will put the same URI that you put in the previous `Thing` `newTD` field.
`action_task` is the method you need to be run when a new Action Request 
is detected. For this reason, it must be formatted either as a lambda expression
```
lambda added, removed: do_something_function()
```
either as a complete handler:
```
def do_something_function(added,removed)
```
`forProperties` is a list that may be empty. If you previously declared 
some Properties, and you want to connect them to this action so that there 
will be a `<myAction> wot:forProperty <myProperty>` triple, just put the 
property in the list.
`forceType` will be discussed later.

3. Declare your Properties, with
```
myProperty = Property(myEngine,bindings)
```
where in this case `bindings` is a python3 dictionary that can be inferred 
from `new_property.sparql`. You might consider also to use the `getBindingList` 
method.

4. Declare your Events:
```
myEvent = Event(myEngine,bindings,forProperties=[],force_type=None)
```
with the same meaning of parameters.

5. You can now post your WebThing like this:
```
myThing.post(interaction_patterns=[myAction,myEvent,myProperty])
```
Once the WebThing is posted to SEPA successfully, it is still not operational.
You can enable Actions with the following command:
```
myAction.enable()
```
And you can notify Events with the following command:
```
myEvent.notify(bindings)
```
where `bindings` is a dictionary to be formatted as in `new_empty_event_instance.sparql`
(if your event is of EMPTY type), or as in `new_o_event_instance.sparql`
otherwise. To make an example:
```
bindings = {
    "event":"",
    "newEInstance":"",
    "newOData":"",
    "newValue":"",
    "newDS":""
}
```

##### Cocktail Discovery
When it comes to discover what WebThings are available, just consider that
in Cocktail every class has its own `discover` static method. Therefore,
```
Property.discover(myEngine,prop="UNDEF",nice_output=False)
```
will output the result of a query available in `property.sparql`. You might
ask for a specific Property URI discovery changing the `prop` parameter.
Similarly,
```
Action.discover(sepa,action="UNDEF",nice_output=False)
Event.discover(sepa,event="UNDEF",nice_output=False)
DataSchema.discover(sepa,ds="UNDEF",nice_output=False)
```
While little difference in the prototype in `discover` method for
```
Thing.discover(sepa,bindings={},nice_output=False)
InteractionPattern.discover(sepa,td_uri="UNDEF",ip_type="UNDEF",nice_output=False)
```
where the `bindings` are given from the `queries/things.sparql`, and
for the `InteractionPattern` you might want to customize your discovery
with a specific ThingDescription URI, or to ask for discovery only for 
Actions, Events or Properties.

##### Requesting Actions
To request an Action, you need to know a few informations about the Action
itself. This is possible by querying the knowledge base, and by building
up an image of the Action. An image of an Action is an Action that has the
inferred flag to True. 
Internally, a call to `isInferred()` checks if there is a handler connected to
that Action. If not, it is an image (i.e., you are not the Action owner, but some external entity that what to interact with it).
You can retrieve an Action image with the following static method:
```
myActionImage = Action.buildFromQuery(myEngine,actionUri)
```
This call returns an Action so that `myActionImage.isInferred()` is `True`.
From that Action item, you can then call the request:
```
myActionImage.newRequest(bindings,confirm_handler=None,completion_handler=None,output_handler=None)
```
Whose parameters are the following:
`bindings` is a python3 dictionary that can be inferred from `new_action_instance` 
SPARQLs file. As an example, in case the action is an I_Action:
```
bindings = {
    "action":"",
    "newAInstance":"",
    "newAuthor":"",
    "newIData":"",
    "newIValue":"",
    "newIDS":""
}
```
where you give the action uri, action instance uri, author uri, input data uri, 
input value, and input DataSchema. 

_TODO: some of these informations (action uri, author) may be already available!_

`confirm_handler` is a method that is triggered when the confirmation flag 
is inserted in the SEPA. `completion_handler` is a method triggered when 
the confirmation flag is inserted in the SEPA. `output_handler` is another 
method, called when the output of the execution is available. The three 
methods are not compulsory, and should be given as lambdas, or functions 
with added and removed parameters.

##### Being notified of Events
In order to receive the notification of an Event, the procedure is the 
following.

First of all, you have to retrieve an image of the Event, as we did for
Actions. Therefore,
```
myEventImage = Event.buildFromQuery(myEngine,eventURI)
```
Once you have that image, you can start and stop observing notifications:
```
myEventImage.observe(handler)
myEventImage.stop_observing()
```
where `handler` is as usual a lambda, or a full handler for subscription
notification.

### 3. Install Cocktail
First of all clone this repository. Then `cd` to the `cocktail_swot_framework` folder.
```
$ python3 setup.py build
$ python3 setup.py sdist
$ sudo python3 setup.py install
```

### 4. Tests
For now, tests are available only to check ontology consistency.
```
$ python3 setup.py test
```

### 5. Other Examples
##### _Coding_
Some examples on how to build Semantic WebThings and how to make them interact are available in `SWTE_example` folder! There is a README to help you run the experiment of the [paper]() (being submitted now).

##### _Available tools and experiments_
In `tools` folder a ysap generation tool and a discovery tool are available as well. A README is provided.

### Contribute
Feel free to get in touch, if you have any question or suggestions
