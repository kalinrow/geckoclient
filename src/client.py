#!/usr/bin/python3
"""
    Client program for GeckoLib. Publishes most relevant data
    on a configured broker.

    version 0.6.0
"""

# import python modules
import locale
import sys

import logging
import logging.handlers

import asyncio
import signal

# import custom modules
from mqtt import Mqtt
from paho.mqtt.client import MQTT_ERR_QUEUE_SIZE

from geckolib import GeckoConstants, GeckoSpaState

# own module
from mySpa import MySpa

# import config
import config
import const

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

    # create rotating file handler
    # log file location is depending on write access
    try:
        rfh = logging.handlers.RotatingFileHandler(
            config.LOGFILE, mode='a', maxBytes=100000, backupCount=config.BACKUP_COUNT, encoding=None, delay=False)
    except PermissionError:
        rfh = logging.handlers.RotatingFileHandler(
            "gecko_client.log", mode='a', maxBytes=100000, backupCount=config.BACKUP_COUNT, encoding=None, delay=False)
    rfh.setLevel(config.DEBUG_LEVEL)

    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to rtf
    rfh.setFormatter(formatter)

    # separate level for geckolib
    geckolib = logging.getLogger("geckolib")
    gecko_level = 'WARN'
    try:
        gecko_level = config.GECKOLIB_DEBUG_LEVEL
    finally:
        geckolib.setLevel(gecko_level)

    # add rtf to logger
    root.addHandler(rfh)


######################
#
# Main routine connecting to the SPA and start looping
#
##########


async def main() -> None:

    # force decimal separator to point
    locale._override_localeconv = {'decimal_point': '.'}
    locale._override_localeconv = {'thousands_sep': ','}

    # prepare MQTT
    logger.info("Connecting to MQTT...")
    mqtt = Mqtt(config.BROKER_ADDRESS, config.BROKER_PORT)

    result = await mqtt.connect_mqtt(config.BROKER_USERNAME, config.BROKER_PASSWORD)
    if result != 0:
        logger.error("Stopping - Can't connect to broker")
        exit(1)

    # get IP of the SPA if set
    ip = 'DHCP'
    try:
        ip = config.SPA_IP_ADDRESS
    finally:
        if ip == "DHCP":
            ip = None

    logger.info("Connecting to SPA...")
    async with MySpa(config.CLIENT_ID, spa_address=ip, spa_identifier=config.SPA_IDENTIFIER, spa_name=config.SPA_NAME) as spaman:

        await asyncio.sleep(GeckoConstants.ASYNCIO_SLEEP_TIMEOUT_FOR_YIELD)

        # Add the value change callback to publish on mqtt
        spaman.onValueChange(mqtt.publish_state)

        # Now wait for the facade to be ready
        is_facade_ready = await spaman.wait_for_facade()
        if not is_facade_ready:
            logger.error(
                "Stopping - Can't connect to facade. Please check settings.")
            mqtt.close()
            exit(1)

        # subscribe and add callbacks
        await mqtt.subscribe_and_message_callback_async(
            const.TOPIC_CONTROL, spaman.controls)

        # get the facade
        facade = spaman.facade

        # set initial values
        try:
            broker_int = config.BROKER_INTERVAL
        except:
            broker_int = 10
        refresh_counter = 0
        reconnect_counter = 0

        # Start loop until break signal received
        while not stop_service:

            refresh_counter += 1
            # check each 10 seconds if mySpa is still connected
            if (refresh_counter > broker_int):

                refresh_counter = 1
                if spaman.spa_state is not GeckoSpaState.CONNECTED:
                    logger.warning("SPA is not connected. Trying to reconnect...")
                    reconnect_counter += 1
                    await spaman.async_connect(spa_address=ip, spa_identifier=config.SPA_IDENTIFIER)
                    if (reconnect_counter > 5):
                        logger.error(
                            "Can't reconnect after 5 attempts. Quitting now...")
                        mqtt.close()
                        exit(2)
                else:
                    reconnect_counter = 0

            await asyncio.sleep(1)

        # final cleanup
        await facade.disconnect()
        mqtt.close()


#########
# main

if __name__ == "__main__":

    # prepare the logging
    prepare_logger()
    logger = logging.getLogger("geckoclient")
    logger.info("GeckoClient starting...")
    logger.info("Python version : " + sys.version)
    logger.info("GC Version     : " + const.GECKO_CLIENT_VERSION)
    logger.info("Decimal Sep.   : " + locale.localeconv()["decimal_point"])

    # add signal listeners
    signal.signal(signal.SIGINT, handler_stop_signals)
    signal.signal(signal.SIGTERM, handler_stop_signals)

    asyncio.run(main())
