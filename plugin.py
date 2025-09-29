##           HomeWizard Wi-Fi 1F Meter Plugin
##
##           Author:         FdeKruijf
##           Version:        1.0.1
##           Last modified:  29-09-2025
##
"""
<plugin key="HomeWizardWifi1FMeter" name="HomeWizard Wi-Fi 1F Meter" author="FdeKruijf" version="1.0.1" externallink="https://www.homewizard.nl/kwh-meter">
    <description>
        
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1" />
        <param field="Port" label="Port" width="200px" required="true" default="80" />
        <param field="Mode1" label="Data interval" width="200px">
            <options>
                <option label="10 seconds" value="10"/>
                <option label="20 seconds" value="20"/>
                <option label="30 seconds" value="30"/>
                <option label="1 minute" value="60" default="true"/>
                <option label="2 minutes" value="120"/>
                <option label="3 minutes" value="180"/>
                <option label="4 minutes" value="240"/>
                <option label="5 minutes" value="300"/>
            </options>
        </param>
        <param field="Mode3" label="Counter offset (Wh)" width="100px" required="false" default="0" />
        <param field="Mode4" label="Production value (Watt)" width="100px" required="false" default="0" />
        <param field="Mode5" label="0=Only active_apparent, 1=Also reactive and factor" width="50px" required="false" default="0"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import urllib
import urllib.request

class BasePlugin:
    #Plugin variables
    pluginInterval = 10     #in seconds
    dataInterval = 60       #in seconds
    dataIntervalCount = 0
    
    # Homewizard kWh meter variables contains in varable elements:
    # {"name of element",
    # [initial value to generate device; replaced by the readed values after reading the parameters from the device,
    # True or False; if True generate device else do not, but see further on,
    # device-ID; ; used as Unit and in as second part in ID in list of devices,
    # multiplying factor for the right shown value, W,Wh,VA,A, percentage]
    #
    # device-ID<=0 never generate device, >0 means generate if True, but if Mode5=1 change False in True
    # example values shown are values once read from the 1F meter
	#
    #: Not used in plugin because device-ID = 0
    elements={"wifi_ssid":["",False,0,1],                     # example value "ABCDE"
    #: [Number] The strength of the Wi-Fi signal, generate device, device-ID
    "wifi_strength":[-1,True,180,1],                          # example value "100" is percentage
    #: [Number] The counter of the really imported energy in the meter, generate device, -(part of device-ID and Unit#)
    "total_power_import_kwh":[-1,False,-101,1000],               # example value in kWh "0.02"
    #: [Number] The counter of the measured imported energy in the meter, generate device, -(part of device-ID and Unit#)
    "total_power_import_t1_kwh":[-1,False,-101,1000],            # example value in kWh "305.332"
    #: [Number] The counter of the measured exported energy in the meter, generate device, -(part of device-ID and Unit#)
    "total_power_export_kwh":[-1,False,-101,1000],               # example value in kWh "0.003"
    #: [Number] The counter of the measured exported energy in the meter, generate device, -(part of device-ID and Unit#)
    "total_power_export_t1_kwh":[-1,False,-101,1000],            # example value in kWh "0.003"
    # When processing next element also above values are used with device-ID -101
    #: [Number] The really currently measured power (W) in the meter, generate device, part of device-ID and Unit#
    "active_power_w":[-1000000.0,True,101,1],                 # example value in W "25.931"
    #: [Number] The really currenly measured power in the meters only phase, generate device, part of device-ID and Unit#
    "active_power_l1_w":[-1000000.0,True,105,1],              # example value in W "25.931"
    #: [Number] The voltage coming from the grid, generate device, part of device-ID and Unit#
    "active_voltage_v":[-1.0,True,108,1],                  # example value in V "231.55"
    #: [Number] The current that flows in the meter, generate device, part of device-ID and Unit#
    "active_current_a":[-1000000.0,True,120,1],               # example value in A "0.122"
    #: [Number] The apparent current that flows in the meter, device generated, part of device-ID and Unit#
    "active_apparent_current_a":[-1000000.0,False,130,1],     # example value in A "0.124"
    #: [Number] The current that does not produce used power, device generated, part of device-ID and Unit#
    "active_reactive_current_a":[-1000000.0,False,140,1],     #example value in A "0.022"
    #: [Number] The used power and non-productive power in the meter, device generated, part of device-ID and Unit#
    "active_apparent_power_va":[-1000000.0,False,150,1],       # example value in VA "26.357"
    #: [Number] The non-productive power in the meter, device generated, part of device-ID and Unit#
    "active_reactive_power_var":[-1000000.0,False,160,1],     # example value in VAr "4.717"
    #: [Number] Percentage of total power (used+non-used) realy used, device generated, part of device-ID and Unit#
    "active_power_factor":[-1,False,171,100],                # example value "0.984"
    #: [Number] frequency in Hz, device generated, device-ID=0 means do never generate device
    "active_frequency_hz":[-1.0,False,0,1]}                   # example value "50.049"

    #Calculated variables
    total_power = 0                 #: The total combined power.
    import_active_power_w = 0       #: The current power imported from the net.
    export_active_power_w = 0       #: The current power exported to the net.
    Debug = False
    counterOffsetValue = 0          #: The value set with Mode3; however when this hardware device is used more than once
                                    # this value can not be used it takes the value of the last initialized device
    
    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            DumpConfigToLog()
            self.Debug = True
        
        # If data interval between 10 sec. and 5 min.
        if 10 <= int(Parameters["Mode1"]) <= 300:
            self.dataInterval = int(Parameters["Mode1"])
        else:
            # If not, set to 60 sec.
            self.dataInterval = 60
            
        # If counter offset value
        if isNumber(Parameters["Mode3"]) == True and 1 <= int(Parameters["Mode3"]) <= 99999999:
            self.counterOffsetValue = int(Parameters["Mode3"])
        else:
            # If not, set to 0 (means no offset)
            self.counterOffsetValue = 0
            
        # If production switch value
        #if isNumber(Parameters["Mode4"]) == True and 1 <= int(Parameters["Mode4"]) <= 999999:
        #    self.productionSwitchValue = int(Parameters["Mode4"])
        #else:
        #    # If not, set to 0 (means off)
        #    self.productionSwitchValue = 0
        
        EarlierDone = False
        if (isNumber(Parameters["Mode5"]) == True and int(Parameters["Mode5"]) == 1):
            EarlierDone = True
            for x in self.elements:
                # initial value is False and DeviceUnitID > 0, activate DeviceUnitID
                if not self.elements[x][1] and self.elements[x][2] > 0:
                    self.elements[x][1] = True
                    EarlierDone = False
        if EarlierDone:
            Domotics.Warning("Disabling DeviceUnits for reactive data is not supported. Delete these devices in the Devices page.")

        # Start the heartbeat
        Domoticz.Heartbeat(self.pluginInterval)
        
        return True
        
    def onConnect(self, Status, Description):
        return True

    def onMessage(self, Data, Status, Extra):
        # Make sure counterOffsetValue and Debug use the values for the current hardware device
        if isNumber(Parameters["Mode3"]) == True and 1 <= int(Parameters["Mode3"]) <= 99999999:
            self.counterOffsetValue = int(Parameters["Mode3"])
        else:
            # If not, set to 0 (means no offset)
            self.counterOffsetValue = 0
        if Parameters["Mode6"] == "Debug":
            self.Debug = True
        try:
            Domoticz.Debug("Processing electricity values from 1F input")
            if self.Debug: self.logMessage("Position 1")
            active_power_counter = 0
            n101 = 0
            for x in self.elements:
                if self.Debug: self.logMessage("Posiion 2 x=" + x + " elements[x][1]=" + str(self.elements[x][1]))
                # Process this element: yes if True or rowID is -101
                if (self.elements[x][1] or self.elements[x][2] == -101):
                    if self.Debug: self.logMessage("Position 3 " + x + ": " + str(self.elements[x][1]) + " ID=" + str(self.elements[x][2]))
                    # self.elements[x][3] is a multiplication factor
                    if (self.elements[x][3] == 1):
                        self.elements[x][0] = float(Data[x])
                    else:
                        self.elements[x][0] = int(Data[x] * self.elements[x][3])
                    if self.Debug: self.logMessage("Position 4: " + x +" Data[x]=" + str(Data[x]) + " elements[x][2]=" + str(self.elements[x][2]) + " value to store=" + str(self.elements[x][0]))
                    if (self.elements[x][2] == -101):
                        n101 = n101 + 1
                        # even means t1 counter, uneven means normal counter; don't know the difference seams none
                        if (n101%2 == 0):
                            if 'import' in x :
                                active_power_counter = active_power_counter + self.elements[x][0]
                            else: # means export
                                active_power_counter = active_power_counter - self.elements[x][0]
                            # add an offset to the counter value
                                active_power_counter = active_power_counter +self.counterOffsetValue 
                    elif (self.elements[x][2] == 101):
                        active_power_w = self.elements[x][0]
                    # end of initial processing
                # process this element
                if (self.elements[x][1]):
                    # device already generated?
                    if (self.elements[x][2] not in Devices): # [2] is device-ID
                        if self.Debug: self.logMessage("Position after not in Devices x=" + x + " elements[x][2]=" + str(self.elements[x][2]))
                        try: # Device with one or two counters and W value?
                            if (self.elements[x][2] in {101}):
                                # x is: active_power_w
                                if self.Debug: self.logMessage("Create device 101 with W")
                                Domoticz.Device(Name=x.replace('a', 'Total a').replace('_p', ' p').replace('_w', ''),  Unit=self.elements[x][2], Type=243, Subtype=29).Create()
                            # Device with W?
                            elif (self.elements[x][2] in {105}):
                                # x is: active_power_l1_w
                                Domoticz.Device(Name=x.replace('active_', 'Active ').replace('_l1__w', ' '),  Unit=self.elements[x][2], Type=243, Subtype=29).Create()
                            # Device with Volt
                            elif (self.elements[x][2] in {108}):
                                # x is: active_voltage_v
                                Domoticz.Device(Name=x.replace('active_', '').replace('vo', 'Vo').replace('_v', ''), Unit=self.elements[x][2], Type=243, Subtype=8).Create()
                            # Device with Ampere
                            elif (self.elements[x][2] in {120,130,140}):
                                # x is: active_current_a or active_apparent_current_a or active_reactive_current_a
                                if self.Debug: self.logMessage("Create device 120 or 130 or 140 with A")
                                Domoticz.Device(Name=x.replace('active_', 'Total ',1).replace('_a', '').replace('_cu', ' cu'), Unit=self.elements[x][2], Type=243, Subtype=23).Create()
                            # Device with VA
                            elif (self.elements[x][2] in {150}):
                                # active_apparent_power_va
                                Domoticz.Device(Name=x.replace('active_', 'Total ').replace('_p', ' p').replace('_va', ''),  Unit=self.elements[x][2], Type=243, Subtype=31, Options={'Custom':'1;VA'}).Create()
                            # Device with VAR
                            elif (self.elements[x][2] in {160}):
                                # x is: active_reactive_power_var
                                Domoticz.Device(Name=x.replace('active_', 'Total ',1).replace('_p', ' p').replace('_var', ''),  Unit=self.elements[x][2], Type=243, Subtype=31, Options={'Custom':'1;VAR'}).Create()
                            # Device with factor becomes percentage
                            elif (self.elements[x][2] in {171,180}):
                                # x is: active_power_factor or wifi_strength
                                Domoticz.Device(Name=x.replace('active_','').replace('p','P').replace('_f', ' f').replace('wifi_', 'Wifi '), Unit=self.elements[x][2], Type=243, Subtype=6).Create()
                        except:
                            Domoticz.Error("Failed to create device id " + str(elements[x][2]))
                    # Update device
                    try: 
                        if (self.elements[x][2] in {101}):
                            if self.Debug: self.logMessage("Update of: " + x + " active_power_w=" + f'{active_power_w:.3f}' + "active_power_counter=" + numStr(active_power_counter) + " total_power=" +  f'{self.total_power:.3f}')
                            UpdateDevice(self.elements[x][2], 0, f'{active_power_w:.3f}' + ";" + numStr(active_power_counter), True)
                        elif (self.elements[x][2] in {105}):
                            # Watt
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.3f}' + ';0', True)
                        elif (self.elements[x][2] in {108}):
                            # Volt
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.3f}' + ';0', True)
                        elif (self.elements[x][2] in {120,130,140}):
                            # Ampere
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.3f}' + ';0', True)
                        elif (self.elements[x][2] in {150}):
                            # VoltAmpere
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.3f}', True)
                        elif (self.elements[x][2] in {160}):
                            # ReactiveVoltAmpere
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.3f}', True)
                        elif (self.elements[x][2] in {171,180}):
                            UpdateDevice(self.elements[x][2], 0, f'{self.elements[x][0]:.1f}', True)
                            if self.Debug: self.logMessage("Percentage=" + f'{self.elements[x][0]:.1f}')
                    except:
                        Domoticz.Error("Failed to update device id " + str(elements[x][2]))
                if self.Debug: self.logMessage("Position after yes or no processing element")
        except:
            Domoticz.Error("Failed to read response data")
            if self.Debug: self.logMessage("Failed to read response data when x="+x)
            return
           
        return True
                    
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        return True

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)
        return

    def onHeartbeat(self):
        self.dataIntervalCount += self.pluginInterval
        
        #------- Collect data -------
        if ( self.dataIntervalCount >= self.dataInterval ):
            self.dataIntervalCount = 0
            self.readMeter()
        
        return

    def onDisconnect(self):
        return

    def onStop(self):
        Domoticz.Log("onStop called")
        return True

    def readMeter(self):
        try:
            APIdata = urllib.request.urlopen("http://" + Parameters["Address"] + ":" + Parameters["Port"] + "/api/v1/data").read()
        except:
            Domoticz.Error("Failed to communicate with Wi-Fi 1F meter at ip " + Parameters["Address"] + " with port " + Parameters["Port"])
            return False
        
        try:
            APIjson = json.loads(APIdata.decode("utf-8"))
        except:
            Domoticz.Error("Failed converting API data to JSON")
            return False
            
        try:
            self.onMessage(APIjson, "200", "")
        except:
            Domoticz.Error("onMessage failed with some error")
            return False
    def logMessage(self, Message):
        f= open("plugins/HomeWizard-Wifi-1F-plugin/log.txt","a+")
        f.write(Message+'\r\n')
        f.close()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
        
def numStr(s):
    try:
        return str(s).replace('.','')
    except:
        return "0"

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def UpdateDevice(Unit, nValue, sValue, AlwaysUpdate=False, SignalLevel=12):    
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if ((Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (AlwaysUpdate == True)):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), SignalLevel=SignalLevel)
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
