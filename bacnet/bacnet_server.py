#!/usr/bin/env python3
"""
bacnet_server.py - Minimal BACnet server simulating a water tank with:
 - water level (analogValue)
 - temperature (analogValue)
 - alarm (binaryValue)
"""

import sys
import logging
import argparse
import configparser
import time
from threading import Thread
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.core import run, stop
from bacpypes.object import AnalogValueObject, BinaryValueObject

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class WaterTank:
    """
    Simulates a water tank with a 'level', 'temperature', and possible alarm states.
    """
    def __init__(self, level, temperature, high_thresh, low_thresh):
        self.level = level
        self.temperature = temperature
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.high_alarm = False
        self.low_alarm = False

    def update_tank(self):
        """Randomly change level & temperature, then check alarms."""
        import random
        # Level moves randomly
        self.level += random.uniform(-1.0, 2.0)
        # Keep in 0-100 range
        self.level = max(0.0, min(100.0, self.level))

        # Slight temperature drift
        self.temperature += random.uniform(-0.1, 0.1)

        # Check thresholds
        self.high_alarm = (self.level >= self.high_thresh)
        self.low_alarm = (self.level <= self.low_thresh)

        log.info(
            f"Tank Update => level={self.level:.1f}%, temp={self.temperature:.1f}C, "
            f"high_alarm={self.high_alarm}, low_alarm={self.low_alarm}"
        )

def main():
    parser = argparse.ArgumentParser(description="BACnet Water Tank Server")
    parser.add_argument("--config", default="config.ini", help="Path to config file")
    args = parser.parse_args()

    # Read config
    cfg = configparser.ConfigParser()
    cfg.read(args.config)

    # Server section
    server = cfg['bacnet_server']
    host = server['host']
    mask = server['mask']
    port = server['port']
    device_id = server.getint('device_id')
    address = f"{host}/{mask}:{port}"

    # Object IDs and tank params
    lvl_obj_id = server.getint('water_level_object_id')
    tmp_obj_id = server.getint('temperature_object_id')
    alm_obj_id = server.getint('alarm_object_id')

    initial_level = server.getfloat('initial_level')
    initial_temp = server.getfloat('initial_temperature')
    high_thresh = server.getfloat('high_level_threshold')
    low_thresh = server.getfloat('low_level_threshold')

    # Create water tank
    tank = WaterTank(initial_level, initial_temp, high_thresh, low_thresh)

    # BACnet device
    local_device = LocalDeviceObject(
        objectName="WaterTankDevice",
        objectIdentifier=device_id,
        maxAPDULengthAccepted=1024,
        segmentationSupported="noSegmentation",
        vendorIdentifier=15
    )
    # BACpypes application
    app = BIPSimpleApplication(local_device, address)

    # Create BACnet objects
    level_obj = AnalogValueObject(
        objectIdentifier=("analogValue", lvl_obj_id),
        objectName="TankLevel",
        presentValue=tank.level,
        units="percent"
    )
    temp_obj = AnalogValueObject(
        objectIdentifier=("analogValue", tmp_obj_id),
        objectName="TankTemp",
        presentValue=tank.temperature,
        units="degreesCelsius"
    )
    alarm_obj = BinaryValueObject(
        objectIdentifier=("binaryValue", alm_obj_id),
        objectName="TankAlarm",
        presentValue=False  # 0=False, 1=True
    )

    # Add them to the app
    app.add_object(level_obj)
    app.add_object(temp_obj)
    app.add_object(alarm_obj)

    log.info(f"Starting BACnet server at {address} (device_id={device_id})")

    # Background thread to update tank & BACnet objects
    def update_loop():
        while True:
            time.sleep(5)
            tank.update_tank()
            # Sync presentValue with tank state
            level_obj.presentValue = tank.level
            temp_obj.presentValue = tank.temperature
            alarm_active = tank.high_alarm or tank.low_alarm
            alarm_obj.presentValue = 1 if alarm_active else 0

    Thread(target=update_loop, daemon=True).start()

    # Run the server event loop
    try:
        run()
    except KeyboardInterrupt:
        log.info("Server interrupted by user")
    finally:
        stop()

if __name__ == "__main__":
    sys.exit(main())
