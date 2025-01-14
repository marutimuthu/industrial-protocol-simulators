#!/usr/bin/env python3
"""
mqtt_sub.py
A simple MQTT subscriber that reads settings from 'mqtt_config.ini'.
Subscribes to a given topic and logs incoming messages.
"""

import logging
import configparser
import sys

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_subscriber():
    # 1) Load config
    config = configparser.ConfigParser()
    config.read("mqtt_config.ini")

    if not config.has_section("mqtt_broker"):
        logger.error("Missing [mqtt_broker] section in mqtt_config.ini")
        sys.exit(1)

    # Extract MQTT broker settings
    broker_host = config["mqtt_broker"].get("host", "localhost")
    broker_port = config["mqtt_broker"].getint("port", 1883)
    username = config["mqtt_broker"].get("username", "")
    password = config["mqtt_broker"].get("password", "")
    clean_session_str = config["mqtt_broker"].get("clean_session", "true")
    clean_session = clean_session_str.lower() == "true"

    qos = config["mqtt_broker"].getint("qos", 0)

    if not config.has_section("subscriber"):
        logger.error("Missing [subscriber] section in mqtt_config.ini")
        sys.exit(1)

    # Subscriber section
    sub_topic = config["subscriber"].get("topic", "my/test/topic")

    # 2) Create MQTT client
    client = mqtt.Client(clean_session=clean_session)

    # Set username/password if provided
    if username:
        client.username_pw_set(username, password=password)

    # 3) Define callbacks
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {broker_host}:{broker_port}, subscribing to '{sub_topic}'")
            client.subscribe(sub_topic, qos=qos)
        else:
            logger.error(f"Failed to connect, return code={rc}")

    def on_message(client, userdata, msg):
        logger.info(f"Received message on topic='{msg.topic}': {msg.payload.decode('utf-8')}")

    client.on_connect = on_connect
    client.on_message = on_message

    # 4) Connect to broker
    try:
        logger.info(f"Connecting to {broker_host}:{broker_port}, clean_session={clean_session}, qos={qos}")
        client.connect(broker_host, broker_port, keepalive=60)
    except Exception as e:
        logger.error(f"Error connecting to broker: {e}")
        sys.exit(1)

    # 5) Blocking network loop
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Subscriber stopped by user (Ctrl+C).")
    finally:
        client.disconnect()
        logger.info("MQTT subscriber disconnected.")


if __name__ == "__main__":
    run_subscriber()
