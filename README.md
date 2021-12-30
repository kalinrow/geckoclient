# GeckoClient

A client for Gecko SPA system using in.touch. It used the gecklib from gazoodle to connect to your SPA and publishes the most relevant information on a broker. From there your homeautomation system can retrive the values again.

So far the heater, watercare, filter, the pumps and lights status as well as the remiders are published. The lights can also be controlled.

## Requirements

The script has been written and tested only on a Linux machine. No idea, if it also works on a Windows host.
For sure the service installation needs to be adapted.

You need to have python 3 installed with the libraries geckolib and paho-mqtt.

```console
sudo apt install python3-pip
pip install geckolib
pip install paho-mqtt
```

### Reminders fix for geckolib (v0.3.20)

Until the the pull request #25 (https://github.com/gazoodle/geckolib/pull/25) has been merged into the geckolib you need to fix the geckolib just installed. 
To do so you need to find the installation path of the geckolib library and replace the the orginal files with the one from the `fix_geckolib`. Take care about the folder names to not mix the two `remindes.py` files.

## Installation
The installation is quiet simple by coping the files to a dedicated folder and configuring the client to run as a service.

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
See example below.

Please use the UUID generator to create an unique ID for your client. That is important for have a good communication.
See also comments from the developer of the geckolib on this topic under https://github.com/gazoodle/geckolib

```config
# SPA values
SPA_NAME = "My Spa"
SPA_IDENTIFIER = "SPAXX:XX:XX:XX:XX:XX"


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

# Known Issues
Sometimes getting the target temperature in case it is set directly on the pool does not work. Similar sometimes setting the targe temperature is not working too. I hope to be able to improve that in the coming month.

# Acknowledgements

 - Inspired by https://github.com/gazoodle/geckolib and https://github.com/chicago6061/in.touch2.
 - Thanks to the folk at Gecko for building this system as a local device rather than mandating a cloud solution.
 
# License
Licensed under the EUPL-1.2-or-later.

https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12


# History

## v0.2 fix for reading pumps correctly

## v0.1 first working version


