#!/usr/bin/env python3
"""
modbus_server.py
Load settings from an INI config file, then run a Modbus server (TCP or Serial).
"""

import logging
import configparser

from pymodbus.server import StartTcpServer, StartSerialServer
from pymodbus.datastore import (
    ModbusSlaveContext,
    ModbusServerContext,
    ModbusSequentialDataBlock,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_modbus_server():
    # Read the INI config
    config = configparser.ConfigParser()
    config.read("modbus_config.ini")

    # Extract server parameters
    server_type = config["server"].get("server_type", "tcp").lower()
    host = config["server"].get("host", "127.0.0.1")
    port = config["server"].getint("port", 5020)
    single_mode_str = config["server"].get("single_slave_mode", "true")
    single_mode = single_mode_str.lower() == "true"
    initial_value = config["server"].getint("initial_value", 0)
    
    # Create data blocks
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [initial_value]*100),
        co=ModbusSequentialDataBlock(0, [initial_value]*100),
        hr=ModbusSequentialDataBlock(0, [initial_value]*100),
        ir=ModbusSequentialDataBlock(0, [initial_value]*100),
    )
    context = ModbusServerContext(slaves=store, single=single_mode)

    if server_type == "tcp":
        # TCP server
        logger.info(f"Starting Modbus TCP Server on {host}:{port}")
        StartTcpServer(context, address=(host, port))
    elif server_type == "serial":
        # Serial server
        serial_port = config["server_serial"].get("port", "/dev/ttyUSB0")
        baudrate = config["server_serial"].getint("baudrate", 9600)
        logger.info(f"Starting Modbus Serial Server on {serial_port} at {baudrate} baud")
        StartSerialServer(
            context,
            port=serial_port,
            baudrate=baudrate,
            # If needed, set framer=ModbusRtuFramer, etc.
        )
    else:
        logger.error(f"Unknown server type: {server_type}")
        return


if __name__ == "__main__":
    run_modbus_server()
