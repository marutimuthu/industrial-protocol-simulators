#!/usr/bin/env python3
"""
mqtt_pub.py
A simple MQTT publisher that reads settings from 'mqtt_config.ini'.
Publishes messages at a configurable interval.
"""

import time
import logging
import configparser
import sys

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_publisher():
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
    publish_interval = config["mqtt_broker"].getint("publish_interval", 5)

    if not config.has_section("publisher"):
        logger.error("Missing [publisher] section in mqtt_config.ini")
        sys.exit(1)

    # Publisher section
    pub_topic = config["publisher"].get("topic", "my/test/topic")
    message_payload = config["publisher"].get("message_payload", "Hello from MQTT Publisher!")

    # 2) Create MQTT client
    client = mqtt.Client(clean_session=clean_session)
    
    # Set username/password if provided
    if username:
        client.username_pw_set(username, password=password)

    # 3) Define callbacks (optional)
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {broker_host}:{broker_port}")
        else:
            logger.error(f"Failed to connect, return code={rc}")

    def on_publish(client, userdata, mid):
        logger.info(f"Message ID {mid} published successfully")

    client.on_connect = on_connect
    client.on_publish = on_publish

    # 4) Connect to broker
    try:
        logger.info(f"Connecting to {broker_host}:{broker_port}, clean_session={clean_session}, qos={qos}")
        client.connect(broker_host, broker_port, keepalive=60)
    except Exception as e:
        logger.error(f"Error connecting to broker: {e}")
        sys.exit(1)

    # 5) Start background network loop
    client.loop_start()

    # 6) Publish messages at intervals
    try:
        while True:
            # Publish a message
            result, mid = client.publish(pub_topic, message_payload, qos=qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published '{message_payload}' to topic='{pub_topic}' QoS={qos}")
            else:
                logger.error(f"Failed to publish message: {result}")

            time.sleep(publish_interval)

    except KeyboardInterrupt:
        logger.info("Publisher stopped by user (Ctrl+C).")

    finally:
        # 7) Clean up
        client.loop_stop()
        client.disconnect()
        logger.info("MQTT publisher disconnected.")


if __name__ == "__main__":
    run_publisher()
