# Cocktail example
In this example, we show how to run a Semantic WebThing Environment using the Cocktail framework.

In our SWTE we have
1. Some DataSchemas, which you will find in `dataschemas.py`. _Here you can learn how to insert a new DataSchema into your SWTE_
2. The Thermostat WebThing
3. The HotCold heater/air conditioner WebThing
4. The Smart Clock (dummy) WebThing
5. The temperature simulator (this is just a utility, in the real world we would not need that)
6. A specific YSAP file to enhance the capabilities of our SWTE (`example.ysap`).

## Thermostat
It defines 
- one Action, to setup T_low and T_high, boundaries of the user temperature "comfort zone".
- one Event to trigger new Temperatures.

Every 2 seconds an Event is triggered until the user stops the process.
In addition to this, when the temperature is outside the comfort zone, the Thermostat can request actions from specific actuators that are available in the SWTE. This is an example of Smart Discovery: have a look to `example.ysap` and to the [paper]().

## HotCold
Is the actuator that acts on temperature. It has an Action, that triggers heating or air conditioning, and it waits for some events triggered by any sensor sensing temperature. This is another example of Smart Discovery.

## Smart Clock
Is a dummy WebThing, that proves that the smart discovery is efficient, as neither Thermostat, neither HotCold use it.

## How to run the example
1. Run a SEPA instance
2. Insert DataSchemas in the SWTE
```
$ python3 dataschemas.py clear
```
3. Run the temperature simulator
```
$ python3 temperature.py
```
4. Run the three WebThings. No matter the order!
```
$ python3 thermostat.py
$ python3 smart_clock.py
$ python3 hotcold.py
```
And see how the temperature reaches autonomously the comfort zone.