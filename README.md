 --------------------------------
# < Industrial Protocol Simulators >
 
    -----------------------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||

# v.2 (Plan)

## Stack
```
+------------------------------------------------------+
|                   User Interface                     |
|         (CLI or Simple GUI built with PyQt,          |
|              Tkinter, or a Web-based UI)             |
+------------------------+-----------------------------+
| Configuration Manager  |   Logging & Monitoring      |
+------------------------+-----------------------------+
|             Protocol Abstraction Layer               |
|         (Common Interface for Protocols)             |
+-----------+---------------+-----------+--------------+
|   Modbus  |    MQTT       | Siemens S7|  Others...   |
|   (RTU,   | (Broker &     |           | (Profinet,   |
|    TCP)   |   Client)     |           |  Profibus,   |
|           |              ...          |  BACnet, etc)|
+-----------+---------------+-----------+--------------+
|         Networking & Serial Communication Layer      |
+------------------------------------------------------+
|                     Operating System                 |
+------------------------------------------------------+
```

# v.1
## How to use?
```
$ python3 -m venv .venv
$ source venv/bin/activate
```
Step 1: Install all dependencies

Step 2: Edit the config file (xx.ini) within each protocol e.g. modbus_config.ini

Step 3: Run the simulator e.g. tcp_client.py

For Sparkplug-b:
```
$ brew install protobuf
$ protoc -I=../../sparkplug_b/ --python_out=. ../../sparkplug_b/sparkplug_b.proto
```

Checkout later: 
- https://github.com/Orange-Cyberdefense/awesome-industrial-protocols
