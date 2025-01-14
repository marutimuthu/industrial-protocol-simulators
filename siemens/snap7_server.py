#!/usr/bin/env python3
"""
snap7_server.py
A simple Snap7-based server to simulate a Siemens S7 PLC.
"""
import logging
import configparser
import sys
import time
from ctypes import create_string_buffer

import snap7
from snap7.server import Server as Snap7Server
from snap7.util import set_byte
from snap7.type import SrvArea

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_snap7_server():
    # --- 1) Load config ---
    config = configparser.ConfigParser()
    config.read("snap7_config.ini")

    if not config.has_section("snap7_server"):
        logger.error("Missing [snap7_server] section in snap7_config.ini")
        sys.exit(1)

    ip = config["snap7_server"].get("ip", "127.0.0.1")
    tcpport = config["snap7_server"].getint("tcpport", 1102)
    db_number = config["snap7_server"].getint("db_number", 1)
    db_size = config["snap7_server"].getint("db_size", 256)
    update_interval = config["snap7_server"].getint("update_interval", 5)
    # Create a ctypes string buffer instead of a Python bytearray
    db_buffer = create_string_buffer(db_size)

    # --- 2) Create Snap7 server ---
    server = Snap7Server()
    server.register_area(SrvArea.DB, db_number, db_buffer)

    # server.register_area(snap7.type.SrvArea.DB, db_number, bytearray(db_size))
    # server.register_area(snap7.type.srvAreaDB, db_number, bytearray(db_size))
    # The above creates a DB area of `db_size` bytes as a bytearray.

    # If you want, you could also register other areas like I/O, Markers, etc.
    # server.register_area(snap7.types.srvAreaPA, 0, bytearray(256))  # Process inputs
    # server.register_area(snap7.types.srvAreaPE, 0, bytearray(256))  # Process outputs

    # --- 3) Start listening ---
    logger.info(f"Starting Snap7 server on {ip}:{tcpport}, DB#={db_number}, size={db_size}")
    # The server_name, on the underlying side, is optional
    server.start_to(ip, tcpport)

    # You can also do `server.start()` if you only want to listen on 0.0.0.0:102 (or whatever default port).
    # For custom IP/port, we use `start_to(ip, tcpport)`.

    # --- 4) Periodically update data in the DB to simulate changes ---
    try:
        while True:
            # Example: Write incremental data each cycle
            # data = server.get_db(db_number)
            # # Let's set the first byte to some changing value:
            # current_val = data[0]
            # new_val = (current_val + 1) % 256
            # set_byte(data, 0, new_val)
            # server.set_db(db_number, data)

            # logger.info(f"Updated DB{db_number} first byte: {current_val} -> {new_val}")

            time.sleep(update_interval)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, stopping Snap7 server.")
    finally:
        server.stop()
        server.destroy()
        logger.info("Snap7 server shut down.")


if __name__ == "__main__":
    run_snap7_server()
