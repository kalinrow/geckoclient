# GeckoClient

A client for Gecko SPA system using in.touch. It used the GeckoLib from gazoodle to connect to your SPA and publishes the most relevant information on a broker. From there your home automation system can retrieve the values again.

So far the heater, water care, filter, the pumps and lights status as well as the reminders are published. The lights can also be controlled.

## Requirements

The script has been written and tested only on a Linux machine. No idea, if it also works on a Windows host.
For sure the service installation needs to be adapted.

You need to have Python 3.8 or later installed with the libraries geckolib and asyncio-paho.

```console
sudo apt install python3-pip       # if not already installed
sudo pip3 install geckolib==0.4.7
sudo pip3 install asyncio-paho
```

## Installation
The installation is quiet simple by coping the files to a dedicated folder and configuring the client to run as a service.
If you update from an older version, please stop the service before coping  the files.

1. Create a folder, e.g. /opt/geckoclient
2. Copy all python file into the folder
   ```
   cp src/*.py /opt/geckoclient
   ```
3. Copy the config template to `config.py`
   ```
   cp src/config.py_template /opt/geckoclient
   ```

## Configuration

In order to connect to your SPA and broker, you need to configure the connection parameters below.
You can use the in.touch APP to retrieve the SPA_NAME and SPA_IDENTIFIER. The identifier should be the MAC address with SPA as prefix.
If the spa is not detected you can add the IP address. That can help to fix the issue.
See example below.


Please use the UUID generator to create an unique ID for your client. That is important for have a good communication.
See also comments from the developer of the geckolib on this topic under https://github.com/gazoodle/geckolib

```config
# SPA values
SPA_NAME = "My Spa"
SPA_IDENTIFIER = "SPAxx:xx:xx:xx:x:xx"   # Please use lowercase characters
SPA_IP_ADDRESS = "DHCP"   # either the IP address or DHCP in case of dynamic assignment


# Replace with your own UUID, see https://www.uuidgenerator.net/>
CLIENT_ID = "123"

# BROKER values
BROKER_ADDRESS = "192.168.1.100"
BROKER_PORT = 1883
BROKER_USERNAME = "username"
BROKER_PASSWORD = "password"
BROKER_ID = "geckoclient"

# Topic
TOPIC = "whirlpool"

# Log file
LOGFILE = "/var/log/geckoclient.log"

# Debug settings
# level # can be one of the following strings
#   'CRITICAL','FATAL', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'NOTSET'
DEBUG_LEVEL = 'DEBUG'
GECKOLIB_DEBUG_LEVEL = 'WARN'
# number of log files to keep
BACKUP_COUNT=5
```

## Configure as service
1. Update the path in gecko.service (only if geckoclient has not been installed in /opt/geckoclient)
2. Copy service/gecko.service into /etc/systemd/system
   ```
   cp service/gecko.service /etc/systemd/system
   ```
5. Enable the service
   ``` 
   sudo systemctl enable gecko.service
   ```

### Start/Stop the service
To start the service use
``` 
sudo systemctl start gecko.service
```

To stop the service use
``` 
sudo systemctl stop gecko.service
```

To check the status of the service use
``` 
sudo systemctl status gecko.service
```
# SPA controllers

## Republish all values
To republish all values use command topic `%prefix%/control/cmnd` and send the text `refresh_all` 

## Control the light
The lights can be switched via the broker. To do so simple use the command topic `%prefix%/lights/cmnd` and send the text `set_lights=HI` for on and `set_lights=OFF` for off.

## Control the temperature
The temperature can be the broker. To do so  use the command topic `%prefix%/water_heater/cmnd` and send the text `set_temp=TEMP` where _TEMP_ is the desired temperature (only CELSIUS values from 15 to 40 are allowed).

## Control the pumps
Pumps can also be switched via the broker. To do so use the command topic `%prefix%/pumps/cmnd` with payload `set_pump:PUMP=[HI|OFF]`. Where _PUMP_ is the pump number (zero based, so first pump is 0) and _HI/OFF_ will switch ON or OFF the pump.

## Control the first blower
The first blower can be switched via the broker. To do so use the command topic `%prefix%/blowers/cmnd` with payload `set_blower=[HI|OFF]`. Where  _HI/OFF_ will switch ON or OFF the first blower.

## Control the water care mode
The water care mode can be set via the broker. To do so use the command topic `%prefix%/watercare/cmnd` with payload `set_watercare=[MODE]`. Where _MODE_ is one of the values below (you can use either the integer or the string value):
* 0 = "Away From Home"
* 1 = "Standard"
* 2 = "Energy Saving"
* 3 = "Super Energy Saving"
* 4 = "Weekender"

# Known Issues

## Long waiting time for receiving value change notification
Without manipulating the geckolib, receiving changed values might take up to 2 minutes. I was not able to figure out why.

If you need quicker, e.g because you want to measure runtime of pumps, etc. you need to change the file async_facade.py. To do so, first find the file (in a standard Debian 11 with python3.9 is might be under /usr/local/lib/python3.9/dist-packages/geckolib/automation).
Then add after line 78 the block (take care to use tabs or spaces depending on what the exiting file already uses):

```python
    if self._ready:
        active_mode = True
```

It should now look like:

```python
76  for device in self.all_config_change_devices:
77      if device.is_on:  # type: ignore
78          active_mode = True
79  if self._ready:
80      active_mode = True
81  set_config_mode(active_mode)
```

Now changes are reported immediately. Still there is a 2 minuted gap after the startup of the service.

## High CPU usage
If you suffer from high CPU usage you can change the yield value for asyncio sleep time.
That will dramatically reduce the CPU usage.

To do so, change the value _ASYNCIO_SLEEP_TIMEOUT_FOR_YIELD_ in gecklib `const.py` in geckolib main folder (see above) from 0.001 to 0.02. The latter value works well for me.
```python
    CONNECTION_STEP_PAUSE_IN_SECONDS = 0  # Time between connection steps
    MAX_RF_ERRORS_BEFORE_HALT = 50
    ASYNCIO_SLEEP_TIMEOUT_FOR_YIELD = 0.02 # Changed from 0.001
```

# Acknowledgements

 - Inspired by https://github.com/gazoodle/geckolib and https://github.com/chicago6061/in.touch2.
 - Thanks to the folk at Gecko for building this system as a local device rather than mandating a cloud solution.
 
# License
Licensed under the EUPL-1.2-or-later.

https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12


# Improvement ideas
* Switch command topic values to json format
* Error handling not able to find/connect to a spa

# History

### v0.5.2
* BugFix #3: Spa check interval configured as string instead of integer in const.py
* Added missing configuration values in config.py-template
* Adding refresh_all command to re-publish all values

### v0.5.1
* Adding log level option for geckolib in config.py
* Adding exception handling with default values for missing _SPA_IP_ADDRESS_ (DHCP) and _BACKUP_COUNT_ (WARN) values in config.py

### v0.5
* Breaking changes in config.py:
    * SPA_IP_ADDRESS address parameter needs to be provided
    * BACKUP_COUNT needs to be provided 
* Fixing publishing filter values
* Adding smart winter and ozone mode values
* Adding setting of first blower and water care mode (thanks to Macus)
* Add BACKUP_COUNT option in config.py


### v0.4
* Adapting to geckolib 0.4.7
* No manipulation of the GeckoLib is needed anymore to get the reminders.
* Switching to Asynchronous I/O (asyncio) Paho MQTT client to be able to use the async part of the geckoclient

### v0.3
* Adding states for blowers

### v0.2
* fix for reading pumps correctly

### v0.1
* first working version


