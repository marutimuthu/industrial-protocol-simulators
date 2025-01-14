#!/usr/bin/env python3
"""
snap7_client.py
A Snap7 client that connects to a Snap7 server (simulated PLC),
reads/writes data at a configurable interval.
"""
import logging
import configparser
import sys
import time

import snap7
from snap7.util import get_byte, set_byte

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_snap7_client():
    # --- 1) Load config ---
    config = configparser.ConfigParser()
    config.read("snap7_config.ini")

    if not config.has_section("snap7_client"):
        logger.error("Missing [snap7_client] section in snap7_config.ini")
        sys.exit(1)

    ip = config["snap7_client"].get("ip", "127.0.0.1")
    tcpport = config["snap7_client"].getint("tcpport", 1102)
    rack = config["snap7_client"].getint("rack", 0)
    slot = config["snap7_client"].getint("slot", 1)
    db_number = config["snap7_client"].getint("db_number", 1)
    start = config["snap7_client"].getint("start", 0)
    size = config["snap7_client"].getint("size", 10)
    poll_interval = config["snap7_client"].getint("poll_interval", 5)

    # --- 2) Create Snap7 client ---
    client = snap7.client.Client()

    # 3) Connect to the server
    try:
        logger.info(f"Connecting to Snap7 server at {ip}:{tcpport}, rack={rack}, slot={slot}")
        # The connect_to method includes specifying the TCP port directly.
        # By default, connect() uses port 102. We can override with connect_to().
        client.connect(ip, rack, slot, tcpport)
        if not client.get_connected():
            logger.error("Failed to connect to the Snap7 server.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)

    logger.info("Snap7 client connected.")

    # --- 4) Poll in a loop (read, optionally write) ---
    try:
        while True:
            # Read a range of `size` bytes from DB
            data = client.db_read(db_number, start, size)
            logger.info(f"Read from DB{db_number}, bytes[{start}..{start+size-1}]: {list(data)}")

            # Example: we can also write something back to the server
            # Let's flip the second byte for fun
            second_byte_val = data[1]
            new_val = (second_byte_val + 1) % 256
            set_byte(data, 1, new_val)

            # Write updated data back
            client.db_write(db_number, start, data)

            logger.info(
                f"Wrote back to DB{db_number}, second byte: {second_byte_val} -> {new_val}"
            )

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Snap7 client stopped by user (Ctrl+C).")
    finally:
        # --- 5) Disconnect client ---
        if client.get_connected():
            client.disconnect()
        logger.info("Snap7 client disconnected.")


if __name__ == "__main__":
    run_snap7_client()
