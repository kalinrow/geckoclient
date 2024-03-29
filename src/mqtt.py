####
# deals with MQTT connection

# import configuration variables
from config import *

import asyncio

import logging
from typing import List
import paho.mqtt.client as paho
from asyncio_paho import AsyncioPahoClient

CONNECTION_RC = ("MQTT Connection successful",
                 "MQTT Connection refused – incorrect protocol version",
                 "MQTT Connection refused – invalid client identifier",
                 "MQTT Connection refused – server unavailable",
                 "MQTT Connection refused – bad username or password",
                 "MQTT Connection refused – not authorised")


logger = logging.getLogger(__name__)

#


class Mqtt:
    """
    Return a mqtt.

    The mqtt server name and optionally the port to connect need to be provided.
    The username and password are provided later when requesting to connect
    """

    global client, logger

    def __init__(self, mqtt_server: str, mqtt_port: int = 1883):
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port

    # MQTT message receiver
    async def on_message_async(self, client, userdata, message):
        """
        Messages from top level TOPIC, not caught elsewhere
        """
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(
            f'MQTT default on_message: topic: {topic}, payload: {msg}')

    # MQTT subscript during on_connect callback
    async def on_connect_async(self, client, userdata, flags, rc):
        if (rc == 0):
            logger.info(
                f"MQTT successfully connected to broker {self.mqtt_server}")
            # test subscription

        else:
            logger.error(f"Connection error number {rc} occurred")
            logger.error(f"Error: {CONNECTION_RC[rc]}")

    # MQTT disconnect callback
    def on_subscribe(self, client, userdata, mid, granted_qos):
        logger.debug(f"{mid} - QOS={granted_qos} ")

    def on_disconnect(self, client, userdata, rc):
        if (rc != 0):
            logger.error(f"Unexpected disconnection.Error number {rc}")

    # prepare MQTT
    async def connect_mqtt(self, user: str, password: str) -> int:

        self.client = AsyncioPahoClient(
            client_id=BROKER_ID, clean_session=True)  # create new instance

        self.client.username_pw_set(user, password)

        self.client.asyncio_listeners.add_on_connect(self.on_connect_async)
        self.client.on_subscribe = self.on_subscribe
        self.client.asyncio_listeners.add_on_message(self.on_message_async)
        self.on_disconnect = self.on_disconnect

        try:
            self.client.connect_async(
                self.mqtt_server, self.mqtt_port)  # connect to broker
        except Exception as ex:
            logger.error(f"Connection error: {ex.args[0]}: {ex.args[1]}")
            return 1

        # self.client.loop_start()
        return 0

    def subscribe(self, sub: str) -> None:
        logger.info(f'Subscribing to {sub}')
        self.client.subscribe(sub)

    async def subscribe_and_message_callback_async(self, sub: str, callback) -> None:
        '''
        Register a message callback for a specific topic. Messages that match 'sub' 
        will be passed to 'callback'. Any non-matching messages will be passed to the default on_message callback.
        '''
        logger.info(f'Subscribing to {sub}')
        await self.client.asyncio_subscribe(sub)
        self.client.asyncio_listeners.message_callback_add(sub, callback)

    def publish(self, topic: str, msg: str, qos=0):
        '''
        Publish the msg in topic with qos.
        '''
        self.client.publish(topic, msg, qos)

    def publish_state(self, topic: str, msg: str, qos=0):
        '''
        Publish the state (msg) in topic + "/state" with qos.
        '''
        self.client.publish(topic + "/state", msg, qos)

    def close(self):
        self.client.disconnect()
