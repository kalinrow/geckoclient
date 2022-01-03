#!/usr/bin/python3
"""
    Client program for geckolib. Publishs most relevant data
    on a configured broker.

    version 0.2
"""

# import configuration variables
import config
import const

import time
import logging
import logging.handlers

import signal

from datetime import datetime

from mqtt import Mqtt
from paho.mqtt.client import MQTT_ERR_QUEUE_SIZE


from geckolib import GeckoLocator
from geckolib.automation.facade import GeckoFacade
from geckolib.spa import GeckoSpa

# from reminders import GeckoReminders


### CONSTANTS ###
refresh_interval = 60

# keep running until terminated
stop_service = False


# handler for signals
def handler_stop_signals(signum, frame):
    global stop_service, logger
    logger.debug(f'Thread interrupted: {signum}')
    stop_service = True


# prepare logger
def prepare_logger():
    global logger

    root = logging.getLogger()

    root.setLevel(config.DEBUG_LEVEL)

    # create routating file handler
    # log file location is depanding on write access
    try:
        rfh = logging.handlers.RotatingFileHandler(
            config.LOGFILE, mode='a', maxBytes=100000, backupCount=1, encoding=None, delay=False)
    except PermissionError:
        rfh = logging.handlers.RotatingFileHandler(
            "gecko_client.log", mode='a', maxBytes=100000, backupCount=1, encoding=None, delay=False)
    rfh.setLevel(config.DEBUG_LEVEL)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to rtf
    rfh.setFormatter(formatter)

    # separate level for geckolib
    geckolib = logging.getLogger("geckolib")
    geckolib.setLevel('WARN')

    # add rtf to logger
    root.addHandler(rfh)


####################################################
#
#  JSON payload creator for the different devices
#
###########################################
def get_pumps_payload() -> str:
    # get actual time
    now = datetime.now()  # current date and time

    # loop over all pumps
    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    for pump in facade.pumps:
        json += f'"{pump.name}":"{pump.mode}",'

    # find circulation pump
    for sensor in facade.binary_sensors:
        if sensor.key == "CIRCULATING PUMP":
            json += f'"{sensor.name}":"{sensor.state}"'
            break
    json += '}'
    return json


def get_lights_payload() -> str:
    # get actual time
    now = datetime.now()  # current date and time

    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    for light in facade.lights:
        json += f'"{light.name}":"{light.state_sensor().state}"'
    json += '}'
    return json


def get_waterheater_payload() -> str:

    # get actual time
    now = datetime.now()  # current date and time

    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    json += f'"current_operation": "{facade.water_heater.current_operation}",'
    json += f'"temperature_unit":"{facade.water_heater.temperature_unit}",'
    json += f'"current_temperature":{facade.water_heater.current_temperature},'
    json += f'"target_temperature":{facade.water_heater.target_temperature},'
    json += f'"real_target_temperature":{facade.water_heater.real_target_temperature}'
    json += '}'
    return json


def get_watercare_payload() -> str:
    '''
    get's the values for watercare module and create a nice json payload
    '''
    # update values
    facade.water_care.update()

    # get care mode
    mode = facade.water_care.mode
    if mode == None:  # only to ensure a real value
        mode = 1

    # get care modes
    modes = facade.water_care.modes
    # care mode as text
    mode_txt = modes[mode]

    # get actual time
    now = datetime.now()  # current date and time

    mode_len = len(modes) - 1

    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    json += f'"mode":{mode}, "modes":['
    i = 0
    for modetxt in modes:
        json += "{"
        json += f'"text":"{modes[i]}",'
        json += f'"value":{i}}}'
        if (i < mode_len):
            json += ","
        i += 1
    json += f'], "mode(txt)":"{mode_txt}"'
    json += '}'
    return json

def get_filter_status() -> str:
    '''
    gets the filter status. can be clean and purge
    '''
    for sensor in facade.binary_sensors:
        if (sensor.name == 'Filter Status:Clean'):
            filerStatusClean = sensor.state
        if (sensor.name == 'Filter Status:Purge'):
            filerStatusPurge = sensor.state
    

    # get actual time
    now = datetime.now()  # current date and time
    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    json += f'"Filter Status:Clean":{str(filerStatusClean).lower()},'
    json += f'"Filter Status:Purge":{str(filerStatusPurge).lower()}'
    json += '}'
    return json

def get_reminders_payload() -> str:
    '''
    get's the active remainders and create a nice json payload
    '''
    # update values
    # facade.reminders.update()

    # get reminders
    reminders = facade.reminders

    if (reminders is None) or (len(reminders) == 0):
        logger.debug('No reminders received')
        return

    reminders_len = len(reminders) - 1

    # get actual time
    now = datetime.now()  # current date and time

    json = '{"Time":"' + now.strftime("%d.%m.%Y, %H:%M:%S") + '",'
    json = '{'
    i = 0
    for reminder in reminders:
        if reminder[0] == "Time":
            json += f'"{reminder[0]}":"{reminder[1]}"'
        else:
            json += f'"{reminder[0]}":{reminder[1]}'
        if (i < reminders_len):
            json += ","
        i += 1
    json += '}'
    return json


def set_lights(client, userdata, message):
    '''
    Switch light state
    '''
    topic = str(message.topic)
    msg = str(message.payload.decode("UTF-8"))
    logger.debug(f'msg erhalten: topic: {topic}, payload: {msg}')
    if (msg.startswith("set_lights")):
        parts = msg.split("=")
        if len(parts) == 2:
            if "HI" == parts[1]:
                logger.info("Switching lights on")
                facade.lights[0].turn_on()
            elif "OFF" == parts[1]:
                logger.info("Switching lights off")
                facade.lights[0].turn_off()


def set_temperature(client, userdata, message):
    '''
    Set the new target temperature
    '''
    topic = str(message.topic)
    msg = str(message.payload.decode("UTF-8"))
    logger.debug(f'msg erhalten: topic: {topic}, payload: {msg}')
    if (msg.startswith("set_temp")):
        parts = msg.split("=")
        if len(parts) == 2:
            try:
                temp = float(parts[1])
            except:
                logger.error(f"Wrong temperature value received: {parts[1]}")
                return
            facade.water_heater.set_target_temperature(temp)


# log all changes
# can later be used for actions
def on_spa_change(sender, old_value, new_value):
    logger.debug(f"{sender} changed from {old_value} to {new_value}")


#########
# main

# prepare the logging
prepare_logger()
logger = logging.getLogger("geckoclient")


# add signal listners
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# prepare MQTT
mqtt = Mqtt(config.BROKER_ADDRESS, config.BROKER_PORT)
result = mqtt.connect_mqtt(config.BROKER_USERNAME, config.BROKER_PASSWORD)
if result != 0:
    logger.error("Stopping - Can't connect to broker")
    exit(1)

# subscripbe and add callbacks
mqtt.subscribe_and_message_callback(
    const.TOPIC_WATERHEAT + "/cmnd", set_temperature)
mqtt.subscribe_and_message_callback(const.TOPIC_LIGHTS + "/cmnd", set_lights)


logger.debug("Locating spas on your network")
with GeckoLocator(config.CLIENT_ID, spa_to_find=config.SPA_IDENTIFIER) as locator:

    logger.debug(
        f"Connecting to Spa {config.SPA_NAME}({config.SPA_IDENTIFIER})")
    s = GeckoSpa(locator.get_spa_from_name(config.SPA_NAME))
    facade = GeckoFacade(s.start_connect())
    wait_for_connection = True
    if wait_for_connection:
        while not facade.is_connected:
            facade.wait(0.1)

    # add observers
    # facade.water_heater.watch(on_spa_change)
    facade.watch(on_spa_change)

    # get a reminder object
    # remaindes = GeckoReminders(facade, logger)

    refresh_counter = refresh_interval
    while not stop_service:

        refresh_counter += 1

        if (refresh_counter > refresh_interval):

            logger.debug("Starting refresh data")

            # refresh spa live data
            facade.spa.refresh()

            # publish heater data
            logger.debug("Refreshing heater data")
            json = get_waterheater_payload()
            mqtt.publish_state(const.TOPIC_WATERHEAT, json)

            # publish care mode
            logger.debug("Refreshing care mode data")
            json = get_watercare_payload()
            mqtt.publish_state(const.TOPIC_WATERCARE, json)

            # publish filter status
            logger.debug("Refreshing filter data")
            json = get_filter_status()
            mqtt.publish_state(const.TOPIC_FILTER_STATUS, json)

            # publish pumps
            logger.debug("Refreshing pumps data")
            json = get_pumps_payload()
            mqtt.publish_state(const.TOPIC_PUMPS, json)

            # publish lights
            logger.debug("Refreshing lights data")
            json = get_lights_payload()
            mqtt.publish_state(const.TOPIC_LIGHTS, json)

            # publish remainders
            logger.debug("Refreshing remainders data")
            json = get_reminders_payload()
            if json is not None:
                mqtt.publish_state(const.TOPIC_REMINDERS, json)

            # rest counter
            refresh_counter = 1

        time.sleep(1)

    # final cleanup
    mqtt.close()
    facade.complete()
