#!/usr/bin/env python3
"""
http_simulator.py
A simple HTTP simulator using Flask that returns a JSON payload from an INI config.
To test use: 
$ curl http://127.0.0.1:5000/api/data
"""
import logging
import configparser
import json
import threading
import time

from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables to store config
HOST = "127.0.0.1"
PORT = 5000
ENDPOINT = "/api/data"
JSON_PAYLOAD = {"status": "OK"}  # default fallback

def update_json_periodically():
    import random
    while True:
        JSON_PAYLOAD["value"] = random.randint(0, 1000)
        time.sleep(5)

def load_config():
    """
    Reads http_config.ini and sets global variables.
    """
    global HOST, PORT, ENDPOINT, JSON_PAYLOAD

    config = configparser.ConfigParser()
    config.read("http_config.ini")

    if not config.has_section("server"):
        logger.warning("No [server] section found in http_config.ini, using defaults.")
    else:
        HOST = config["server"].get("host", "127.0.0.1")
        PORT = config["server"].getint("port", 5000)
        ENDPOINT = config["server"].get("endpoint", "/api/data")

    if not config.has_section("json_data"):
        logger.warning("No [json_data] section found in http_config.ini, using fallback JSON.")
    else:
        payload_str = config["json_data"].get("payload", '{"status": "OK"}')
        try:
            # Attempt to parse the string as JSON
            JSON_PAYLOAD = json.loads(payload_str)
        except json.JSONDecodeError:
            logger.error("Failed to parse 'payload' as valid JSON. Falling back to default.")
            JSON_PAYLOAD = {"status": "ERROR", "message": "Invalid JSON in config"}


@app.route("/", methods=["GET"])
def root():
    """
    Simple root endpoint with instructions.
    """
    return jsonify(
        {
            "message": "HTTP Simulator is running. Try the configured endpoint.",
            "endpoint": ENDPOINT,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint (optional).
    """
    return jsonify({"health": "ok"})


@app.route("/api/data", methods=["GET"])  # We'll re-map dynamically below
def default_api():
    """
    Placeholder. We'll update the rule to match ENDPOINT after config load.
    """
    return jsonify(JSON_PAYLOAD)


def main():
    load_config()
    # Dynamically update the rule for the main JSON endpoint
    # (Flask doesn't easily let us define routes with variables before the config is loaded.
    #  So we create a placeholder route above, then re-map it here.)
    view_func = app.view_functions["default_api"]
    # Remove old rule ("/api/data") from the URL map
    app.url_map._rules_by_endpoint["default_api"].clear()
    # Add new rule from the config
    app.add_url_rule(ENDPOINT, "default_api", view_func, methods=["GET"])

    logger.info(f"Starting HTTP Simulator on {HOST}:{PORT}")
    logger.info(f"Serving JSON payload at endpoint: {ENDPOINT}")
    app.run(host=HOST, port=PORT)


if __name__ == "__main__":
    thread = threading.Thread(target=update_json_periodically, daemon=True)
    thread.start()

    main()
