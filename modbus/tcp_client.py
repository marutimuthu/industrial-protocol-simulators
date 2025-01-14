#!/usr/bin/env python3
"""
modbus_client.py

A Modbus client that polls DI, CO, HR, IR at a configurable interval.
Configuration is read from 'modbus_config.ini'.
"""

import logging
import configparser
import time
import sys

from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_modbus_client():
    # --- 1) Load the INI config ---
    config = configparser.ConfigParser()
    config.read("modbus_config.ini")

    # --- 2) Extract shared client params ---
    client_type = config["client"].get("client_type", "tcp").lower()
    host = config["client"].get("host", "127.0.0.1")
    port = config["client"].getint("port", 5020)
    unit_id = config["client"].getint("unit_id", 1)
    poll_interval = config["client"].getint("poll_interval", 5)

    # --- 3) Extract the data block configs ---
    # Coils
    coils_start = config["client_data"].getint("coils_start_address", 0)
    coils_count = config["client_data"].getint("coils_count", 10)
    # Discrete Inputs
    discretes_start = config["client_data"].getint("discretes_start_address", 0)
    discretes_count = config["client_data"].getint("discretes_count", 10)
    # Holding Registers
    hr_start = config["client_data"].getint("holding_registers_start_address", 0)
    hr_count = config["client_data"].getint("holding_registers_count", 5)
    # Input Registers
    ir_start = config["client_data"].getint("input_registers_start_address", 0)
    ir_count = config["client_data"].getint("input_registers_count", 5)

    # --- 4) Initialize the client (TCP or Serial) ---
    if client_type == "tcp":
        logger.info(f"Connecting TCP Client to {host}:{port}")
        client = ModbusTcpClient(host=host, port=port)
    elif client_type == "serial":
        serial_port = config["client_serial"].get("port", "/dev/ttyUSB1")
        baudrate = config["client_serial"].getint("baudrate", 9600)
        logger.info(f"Connecting Serial Client to {serial_port} at {baudrate} baud")
        client = ModbusSerialClient(method="rtu", port=serial_port, baudrate=baudrate)
    else:
        logger.error(f"Unknown client type: {client_type}")
        sys.exit(1)

    if not client.connect():
        logger.error("Failed to connect to the Modbus server.")
        sys.exit(1)

    logger.info(
        "Polling DI, CO, HR, IR at the following settings:\n"
        f"  * Coils: start={coils_start}, count={coils_count}\n"
        f"  * Discretes: start={discretes_start}, count={discretes_count}\n"
        f"  * Holding Regs: start={hr_start}, count={hr_count}\n"
        f"  * Input Regs: start={ir_start}, count={ir_count}\n"
        f"  * Poll Interval: {poll_interval}s\n"
    )

    # --- 5) Polling Loop ---
    try:
        while True:
            # Read Coils (FC=1)
            if coils_count > 0:
                try:
                    resp = client.read_coils(address=coils_start, count=coils_count)
                    if resp.isError():
                        logger.error(f"Error reading coils: {resp}")
                    else:
                        logger.info(f"Coils[{coils_start}..{coils_start+coils_count-1}] = {resp.bits}")
                except ModbusIOException as ex:
                    logger.error(f"Modbus IOException (coils): {ex}")

            # Read Discrete Inputs (FC=2)
            if discretes_count > 0:
                try:
                    resp = client.read_discrete_inputs(address=discretes_start, count=discretes_count)
                    if resp.isError():
                        logger.error(f"Error reading discrete inputs: {resp}")
                    else:
                        logger.info(f"Discretes[{discretes_start}..{discretes_start+discretes_count-1}] = {resp.bits}")
                except ModbusIOException as ex:
                    logger.error(f"Modbus IOException (discretes): {ex}")

            # Read Holding Registers (FC=3)
            if hr_count > 0:
                try:
                    resp = client.read_holding_registers(address=hr_start, count=hr_count)
                    if resp.isError():
                        logger.error(f"Error reading holding registers: {resp}")
                    else:
                        logger.info(f"Holding Registers[{hr_start}..{hr_start+hr_count-1}] = {resp.registers}")
                except ModbusIOException as ex:
                    logger.error(f"Modbus IOException (HR): {ex}")

            # Read Input Registers (FC=4)
            if ir_count > 0:
                try:
                    resp = client.read_input_registers(address=ir_start, count=ir_count)
                    if resp.isError():
                        logger.error(f"Error reading input registers: {resp}")
                    else:
                        logger.info(f"Input Registers[{ir_start}..{ir_start+ir_count-1}] = {resp.registers}")
                except ModbusIOException as ex:
                    logger.error(f"Modbus IOException (IR): {ex}")

            # Sleep for the poll_interval
            logger.info(f"Sleeping for {poll_interval} seconds...\n")
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down client polling loop...")
    finally:
        client.close()
        logger.info("Client connection closed.")


if __name__ == "__main__":
    run_modbus_client()
