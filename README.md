$ source venv/bin/activate

Few other protocols: https://github.com/Orange-Cyberdefense/awesome-industrial-protocols

### How to use?

Step 1: Install all dependencies
Step 2: Edit the config file (xx.ini) within each protocol
Step 3: Run the simulator

For Sparkplug-b:
$ brew install protobuf
$ protoc -I=../../sparkplug_b/ --python_out=. ../../sparkplug_b/sparkplug_b.proto