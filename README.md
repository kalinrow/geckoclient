# GeckoClient

A client for Gecko SPA system using in.touch. It used the gecklib from gazoodle to connect to your SPA and publishes the most relevant information on a broker. From there your homeautomation system can retrive the values again.

So far the heater, watercare, filter, the pumps and lights status as well as the remiders are published. The lights can also be controlled.

## Requirements

The script has been written and tested only on a Linux machine. No idea, if it also works on a Windows host.
For sure the service installation needs to be adapted.

You need to have python 3 installed with the libraries geckolib and asyncio-paho.

```console
sudo apt install python3-pip
sudo pip install geckolib==0.4.7
sudo pip install asyncio-paho
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
You can use the in.touch APP to retrive the SPA_NAME and SPA_IDENTIFIER. the identifier should be the MAC Adresse with SPA as prefix.
If the spa is not detected you can add the IP address. That can help to fix the issue.
See example below.


Please use the UUID generator to create an unique ID for your client. That is important for have a good communication.
See also comments from the developer of the geckolib on this topic under https://github.com/gazoodle/geckolib

```config
# SPA values
SPA_NAME = "My Spa"
SPA_IDENTIFIER = "SPAXX:XX:XX:XX:XX:XX"
SPA_IP_ADDRESS = "DHCP"   # either the IP address or DHCP in case of dynatic assigment


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

# Control the light
The lights can be switched via the broker. To do so simple use the command topic `%prefix%/whirlpool/lights/cmnd` and send the text `set_lights=HI` for on and `set_lights=OFF` for off.

# Control the temerature
The temperature can be the broker. To do so  use the command topic `%prefix%/whirlpool/water_heater/cmnd` and send the text `set_temp=TEMP` where _TEMP_ is the desired temerature (only CELSIUS values from 15 to 40 are allowed).

# Control the pumps
Pumps can alsow be switched via the broker. To do so use the command topic `%prefix%/whirlpool/pumps/cmnd` with payload  `set_pump:PUMP=[HI|OFF]`. Wherer _PUMP_ is the pump number (zero based, so first pump is 0) and _HI/OFF_ will switch ON or OFF the pump.

# Known Issues

## Long waiting time for receivung value change notification
Without manipualting the geckolib, receiving changed values might take up to 2 minutes. I was not able to figure out why.

If you need quicker, e.g because you want to measure runtimes of pumps, etc. you need to change the file async_facade.py. To do so, first find the file (in a standard Debian 11 with python3.9 is might be under /usr/local/lib/python3.9/dist-packages/geckolib/automation).
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

To do so, change the value in `const.py` from geckolib main folder (see above) from 0.001 to 0.02. The later value work well for me.
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


# Improvments
* Error handling not able to find/connect to a spa

# History

### v0.5
* Breaking change: IP address parameter needs to be provided in config.py
* Fixing publishing filter values
* Adding smart winter and ozone mode values
* Adding setting of first blower and watecare more (thanks to Macus)
* Add BACKUP_COUNT option in config.py


### v0.4
* Adapting to geckolib 0.4.7
* No manipulation of the gecklib is needed anymore to get the reminders.
* Switching to Asynchronous I/O (asyncio) Paho MQTT client to be able to use the async part of teh geckoclient

### v0.3
* Adding states for blowers

### v0.2
* fix for reading pumps correctly

### v0.1
* first working version


