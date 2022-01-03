#
# Small test script to ensure connectivity to the broker
#

import paho.mqtt.client as paho
import time

from config import *

TEST_TOPIC = TOPIC + "/mqtt_test"

# MQTT message receiver
def on_message(client, userdata, message):
    """
    Messages fro top level TOPIC, not catched elsewhere
    """
    print ("Receiving message:")
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain, "\n")

# create new instance
print("creating new instance")
client = paho.Client(
    BROKER_ID, clean_session=True)  # create new instance
client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
# define call method
client.on_message = on_message

# connecting to broker
print("connecting to broker\n")
client.connect(BROKER_ADDRESS, BROKER_PORT)  # connect to broker
client.loop_start()

# subscripte to test topic
print("Subscribing to topic",TEST_TOPIC)
client.subscribe(TEST_TOPIC)

# Publish to test topic
print("Publishing message to test topic\n")
client.publish(TEST_TOPIC, "This is a publish test", 0)

time.sleep(4) # wait

# stopping and closing
print("Stopping loop and disconneting from broker\n")
client.loop_stop()
client.disconnect()
