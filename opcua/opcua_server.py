#!/usr/bin/env python3
"""
opcua_server.py
Create an OPC UA server, configure nodes/variables, and optionally update them in a loop.
"""
import time
import logging
import configparser
from configparser import ConfigParser, ExtendedInterpolation
from opcua import ua, Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_opcua_server():
    # --- 1) Load INI config ---
    config = configparser.ConfigParser(interpolation=ExtendedInterpolation())
    config.read("opcua_config.ini")
    
    server_endpoint = config["server"].get("endpoint", "opc.tcp://127.0.0.1:4840")
    namespace_uri = config["server"].get("namespace_uri", "http://examples.freeopcua.github.io")
    server_name = config["server"].get("server_name", "MyOpcUaServer")
    server_loop_time = config["server"].getint("server_loop_time", 1)

    # Node definitions
    node1_name = config["variables"].get("node1_name", "Variable1")
    node1_nodeid = config["variables"].get("node1_nodeid", "ns=2;s=Var1")
    node1_init = config["variables"].getfloat("node1_initial_value", 0.0)

    node2_name = config["variables"].get("node2_name", "Variable2")
    node2_nodeid = config["variables"].get("node2_nodeid", "ns=2;s=Var2")
    node2_init = config["variables"].getfloat("node2_initial_value", 0.0)

    node3_name = config["variables"].get("node3_name", "Variable3")
    node3_nodeid = config["variables"].get("node3_nodeid", "ns=2;s=Var3")
    node3_init = config["variables"].getfloat("node3_initial_value", 0.0)

    # --- 2) Create Server Instance ---
    server = Server()
    server.set_endpoint(server_endpoint)
    server.set_server_name(server_name)

    # Register a new namespace
    idx = server.register_namespace(namespace_uri)
    logger.info(f"Namespace={namespace_uri} registered with index={idx}")

    # --- 3) Create an object to hold our variables ---
    #   We create one "Device" object with our example variables
    objects_node = server.get_objects_node()
    device_obj = objects_node.add_object(idx, "Device")

    # Now add each variable with its custom NodeId
    # parse_nodeid will turn "ns=2;s=VarName" into an object python-opcua can use
    from opcua.ua import NodeId, NodeIdType

    def parse_nodeid(nodeid_str):
        """
        Convert a string like 'ns=2;s="Pressure"' into an actual NodeId object.
        E.g. NodeId("Pressure", 2, NodeIdType.String)
        """
        # Typically nodeid_str looks like: ns=2;s=Pressure
        # or ns=3;i=1001 (integer-based) or ns=2;b=BASE64...
        # We'll do a quick parse for "ns=" and "s=" or "i=" or "b="
        # For simplicity, we assume 'ns=2;s=Something'
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
            # fallback to string if unknown
            return NodeId(id_part, ns_idx, NodeIdType.String)

    v1_nodeid = parse_nodeid(node1_nodeid)
    v2_nodeid = parse_nodeid(node2_nodeid)
    v3_nodeid = parse_nodeid(node3_nodeid)

    var1 = device_obj.add_variable(v1_nodeid, node1_name, node1_init)
    var2 = device_obj.add_variable(v2_nodeid, node2_name, node2_init)
    var3 = device_obj.add_variable(v3_nodeid, node3_name, node3_init)

    # Set variables as writable (optional)
    var1.set_writable()
    var2.set_writable()
    var3.set_writable()

    # --- 4) Start Server ---
    logger.info(f"Starting OPC UA server at {server_endpoint} with name={server_name}")
    server.start()
    logger.info("Server started.")

    # --- 5) Optional Loop to update variable values ---
    try:
        while True:
            # Example: increment or modify the variables in some way
            current_v1 = var1.get_value()
            current_v2 = var2.get_value()
            current_v3 = var3.get_value()

            var1.set_value(current_v1 + 1.0)
            var2.set_value(current_v2 + 0.5)
            var3.set_value((current_v3 + 1) % 5)  # cycles between 0..4

            logger.info(
                f"Updated {node1_name}={var1.get_value()}, "
                f"{node2_name}={var2.get_value()}, "
                f"{node3_name}={var3.get_value()}"
            )

            time.sleep(server_loop_time)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down OPC UA server.")
    finally:
        server.stop()
        logger.info("Server stopped.")


if __name__ == "__main__":
    run_opcua_server()
