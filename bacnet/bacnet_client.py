#!/usr/bin/env python3
"""
bacnet_client.py - Minimal BACnet client to read water tank properties
and optionally clear alarm (binaryValue).
"""

import sys
import logging
import argparse
import configparser
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.core import run, stop
from bacpypes.apdu import ReadPropertyRequest, WritePropertyRequest
from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class WaterTankClient:
    def __init__(self, local_addr, local_device_id):
        self.local_device = LocalDeviceObject(
            objectName="WaterTankClient",
            objectIdentifier=local_device_id,
            maxAPDULengthAccepted=1024,
            segmentationSupported="noSegmentation",
            vendorIdentifier=15
        )
        self.app = BIPSimpleApplication(self.local_device, local_addr)

    def read_prop(self, target_addr, obj_type, obj_inst, prop_id):
        request = ReadPropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id
        )
        request.pduDestination = target_addr

        iocb = self.app.request_io(request)
        iocb.wait()

        if iocb.ioError:
            log.error(f"Read error: {iocb.ioError}")
            return None

        response = iocb.ioResponse
        if not response:
            log.error("No response from server.")
            return None

        # Try to cast to Real for analog objects
        val = response.propertyValue.cast_out(Real)
        if val is None:
            # Could be binary
            val = response.propertyValue
        return val

    def write_prop(self, target_addr, obj_type, obj_inst, prop_id, value):
        """
        Example for writing a Real value to an analog. 
        For binary, we also store a Real(0 or 1).
        """
        request = WritePropertyRequest(
            objectIdentifier=(obj_type, obj_inst),
            propertyIdentifier=prop_id
        )
        val = Any()
        val.cast_in(Real(value))
        request.propertyValue = val
        request.pduDestination = target_addr

        iocb = self.app.request_io(request)
        iocb.wait()

        if iocb.ioError:
            log.error(f"Write error: {iocb.ioError}")
            return False
        return True

def main():
    parser = argparse.ArgumentParser(description="BACnet Water Tank Client")
    parser.add_argument("--config", default="config.ini", help="Path to config file")
    parser.add_argument("--read-only", action="store_true",
                        help="Only read properties (don't clear alarm).")
    args = parser.parse_args()

    # Load config
    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    client_cfg = cfg['bacnet_client']

    host = client_cfg['host']
    mask = client_cfg['mask']
    port = client_cfg['port']
    device_id = client_cfg.getint('device_id')
    local_addr = f"{host}/{mask}:{port}"
    target_addr = client_cfg['target_addr']

    level_id = client_cfg.getint('level_object_id')
    temp_id = client_cfg.getint('temp_object_id')
    alarm_id = client_cfg.getint('alarm_object_id')

    client = WaterTankClient(local_addr, device_id)

    # Read the water level
    level_val = client.read_prop(target_addr, "analogValue", level_id, "presentValue")
    log.info(f"Water Level: {level_val}%")

    # Read the water temperature
    temp_val = client.read_prop(target_addr, "analogValue", temp_id, "presentValue")
    log.info(f"Water Temp : {temp_val}C")

    # Read the alarm state
    alarm_val = client.read_prop(target_addr, "binaryValue", alarm_id, "presentValue")
    log.info(f"Alarm State: {alarm_val} (1 = Active, 0 = Inactive)")

    # Clear alarm if active and not read-only
    if not args.read_only and alarm_val is not None:
        try:
            alarm_float = float(alarm_val)
            if alarm_float == 1.0:
                log.info("Alarm is active; attempting to clear it (write 0).")
                success = client.write_prop(target_addr, "binaryValue", alarm_id, "presentValue", 0.0)
                if success:
                    log.info("Alarm cleared.")
        except ValueError:
            pass

    # Done, shut down the BACpypes event loop
    stop()

if __name__ == "__main__":
    sys.exit(main())
