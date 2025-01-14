#!/usr/bin/env python3
"""
opcua_client.py
Connect to an OPC UA server, read variables at a configurable interval,
and log the results.
"""
import logging
import configparser
import time
import sys

from opcua import Client
from opcua.ua import NodeId, NodeIdType
from opcua import ua

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_nodeid(nodeid_str):
    """
    Convert a string like 'ns=2;s="Pressure"' into an actual NodeId object.
    (Same helper as in the server script, so we can interpret IDs from config.)
    """
    parts = nodeid_str.split(";")
    ns_part = parts[0]  # e.g. ns=2
    id_part = parts[1]  # e.g. s=Something
    ns_idx = int(ns_part.split("=")[1])
    if id_part.startswith("s="):
        return NodeId(id_part.split("=", 1)[1], ns_idx, NodeIdType.String)
    elif id_part.startswith("i="):
        return NodeId(int(id_part.split("=", 1)[1]), ns_idx, NodeIdType.Numeric)
    elif id_part.startswith("b="):
        return NodeId(id_part.split("=", 1)[1], ns_idx, NodeIdType.ByteString)
    else:
        return NodeId(id_part, ns_idx, NodeIdType.String)


def run_opcua_client():
    # --- 1) Load the config ---
    config = configparser.ConfigParser()
    config.read("opcua_config.ini")

    client_endpoint = config["client"].get("endpoint", "opc.tcp://127.0.0.1:4840")
    poll_interval = config["client"].getint("poll_interval", 5)

    node1_id_str = config["client_variables"].get("node1_nodeid", "ns=2;s=Var1")
    node2_id_str = config["client_variables"].get("node2_nodeid", "ns=2;s=Var2")
    node3_id_str = config["client_variables"].get("node3_nodeid", "ns=2;s=Var3")

    node1_id = parse_nodeid(node1_id_str)
    node2_id = parse_nodeid(node2_id_str)
    node3_id = parse_nodeid(node3_id_str)

    # --- 2) Create an OPC UA Client object ---
    client = Client(client_endpoint)
    logger.info(f"Connecting to OPC UA server at {client_endpoint}")
    try:
        client.connect()
        logger.info("OPC UA client connected.")
    except Exception as e:
        logger.error(f"Failed to connect to server: {e}")
        sys.exit(1)

    # --- 3) Obtain Node objects ---
    node1 = client.get_node(node1_id)
    node2 = client.get_node(node2_id)
    node3 = client.get_node(node3_id)

    logger.info(
        "Polling variables:\n"
        f"  node1 = {node1_id_str}\n"
        f"  node2 = {node2_id_str}\n"
        f"  node3 = {node3_id_str}\n"
        f"  poll_interval = {poll_interval}s"
    )

    # --- 4) Polling Loop ---
    try:
        while True:
            val1 = node1.get_value()
            val2 = node2.get_value()
            val3 = node3.get_value()

            logger.info(
                f"Read values: "
                f"{node1_id_str}={val1}, "
                f"{node2_id_str}={val2}, "
                f"{node3_id_str}={val3}"
            )

            time.sleep(poll_interval)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down client.")
    finally:
        client.disconnect()
        logger.info("Client disconnected.")


if __name__ == "__main__":
    run_opcua_client()
