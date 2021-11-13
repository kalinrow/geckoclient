####
# deals with MQTT connection

# import configuration variables
from config import *

import logging
from typing import List
import paho.mqtt.client as paho


CONECTION_RC = ("MQTT Connection successful",
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

    The mqqt server name and optionally the port to inscribe need to be provide.
    Username and passwort are provide when requesting to connect
    """

    global client, logger

    def __init__(self, mqtt_server: str, mqtt_port: int = 1883):
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port

    # MQTT message receiver
    def on_message(self, client, userdata, message):
        """
        Messages fro top level TOPIC, not catched elsewhere
        """
        topic = str(message.topic)
        msg = str(message.payload.decode("UTF-8"))
        logger.debug(f'msg erhalten: topic: {topic}, payload: {msg}')

    # MQTT subscript during on_conect callback
    def on_conect(self, client, userdata, flags, rc):
        if (rc == 0):
            logger.info(
                f"MQTT successfull connected to broker {self.mqtt_server}")
        else:
            logger.error(f"Connection error number {rc} occured")
            logger.error(f"Error: {CONECTION_RC[rc]}")

    # MQTT disconnect callback
    def on_subscribe(self, client, userdata, mid, granted_qos):
        logger.debug(f"{mid} - QOS={granted_qos} ")

    def on_disconnect(self, client, userdata, rc):
        if (rc != 0):
            logger.error(f"Connection error number {rc} occured")

    # prepare MQTT
    def connect_mqtt(self, user: str, password: str) -> int:

        self.client = paho.Client(
            BROKER_ID, clean_session=True)  # create new instance

        self.client.username_pw_set(user, password)

        self.client.on_connect = self.on_conect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        try:
            result = self.client.connect(
                self.mqtt_server, self.mqtt_port)  # connect to broker
        except Exception as ex:
            logger.error(f"Connection error: {ex.args[0]}: {ex.args[1]}")
            return 1

        self.client.loop_start()
        return 0

    def subscribe_and_message_callback(self, sub: str, callback):
        '''
        Register a message callback for a specific topic. Messages that match 'sub' 
        will be passed to 'callback'. Any non-matching messages will be passed to the default on_message callback.
        '''
        logger.info(f'Subscribing to {sub}')
        self.client.subscribe(sub)
        self.client.message_callback_add(sub, callback)

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
        self.client.loop_stop()
