# HomeWizard-Wifi-1F-plugin
A Python plugin for Domoticz that creates several devices for the HomeWizard Wifi 1F kWh meter.

![HomeWizard Wi-Fi kWh meters](https://cdn.homewizard.com/wp-content/uploads/2024/04/kWh-Meter-1-phase-3-phase-1.png)

The [HomeWizard Wi-Fi kWh meters](https://www.homewizard.com/nl/kwh-meter/) are devices that can be installed in a modern power distribution system in your home. By default it sends all of its data to the HomeWizard servers but thanks to its local API you can read the device locally too. With this plugin you can use Domoticz to read the meter and store the data without using your internet connection.

###### Installing this plugin

Domoticz uses Python to run plugins. Use the [installation instructions](https://www.domoticz.com/wiki/Using_Python_plugins#Required:_install_Python) on the Domoticz wiki page to install Python. When Python is installed use [these instructions](https://www.domoticz.com/wiki/Using_Python_plugins#Installing_a_plugin) to install this plugin.

###### Enabling the API

To access the data from the Wifi 1 Phase kWh meter, you have to enable the API. You can do this in the HomeWizard Energy app (version 1.5.0 or higher). Go to Settings > Meters > Your meter, and turn on Local API.

## Devices

The plugin is able to create several devices depending on the values that are read from your meter and that you enable when creating the hardware device. By default only the devices listed under Intial devices are created, even some of these may not be usefull for everyone but you can safely ignore those.
Setting Mode 5 to 1, initially it is 0, enables all possible devices.
Initial devices are, in the order the author thinks are most important:
 1. An energy meter that reads the historical counters with measured energy drawn and fed back (kWh) from/to the grid, together with the average power (Watt)
 2. An energy meter that shows the actual power (Watt) and the calculated used/produced energy (kWh) in case calculation is enabled.
 3. A meter that shows the actual amperage through the meter (A)
 4. A voltage meter that shows the current voltage (V)
 5. A Wi-Fi signal strength meter that shows the current signal strength of the Wi-Fi 1F kWh meter (%)

Additional devices, enabled when Mode5 is 1:
 1. A meter that shows the apparent current in the meter (A)
 2. A meter that shows the reactive current in the meter (A)
 3. An energy meter that shows the apparent power in the meter (VA)
 4. An energy meter that shows the reactive power in the meter (VA)
 5. A meter that shows the power factor of the phase (%)
 
Actual power is the power that is really consumed or produced and that is payed for.
Apparent power is the power that passes between the source and the target.
Reactive power is the power that is exchanged between the source and the target during a cycle; it is exchanged, so you have to dimension your circuit to cope with its current (i.e. the size of the fuse in your circuit), but it is not charged.
Actual power is the difference between apparent power and reactive power.
The power factor is the percentage of actual power compared to apparent power.

## Configuration

The configuration is pretty self explaining. You just need the IP address of your Wi-Fi 1F kWh meter or the name in your local network. Make sure the IP address is static DHCP so it won't change over time.

| Configuration | Explanation |
|--|--|
| IP address | The IP address of the Wi-Fi 3F kWh meter |
| Port | The port on which to connect (80 is default) |
| Data interval | The interval for the data devices to be refreshed |
| Mode5 | 0 when only initial devices need to be generated |
| | 1 when also these additional devices are wanted |
| Debug | Used by the developer to test stuff |

## Additional remark

The desing of this plugin is based on the Python set **elements**. Each element is a list of values. In case you want less devices than the standard implemeted in this plugin, it is quite simple to change the set by commenting out the specific element in the set. Nothing else needs to change.