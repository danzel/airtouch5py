# airtouch5py
Python client for the airtouch 5


## Discovery Method.

The discover method uses UDP to broadcast over the given IP or subnet, defaulting to `255.255.255.255`

```
    discovery_instance = AirtouchDiscovery()
    devices = discovery_instance.discover_airtouch_devices_broadcast(ip)
```

The given list of devices can be used to create a client.

```
client = Airtouch5SimpleClient(device)
try:
    await client.test_connection()
    print("Succeeded")
except Exception as e:
    print(f"Failed: {e}")
    return
```

Now the device details are available. including
- ip: The IP which you can now connect to using TCP
- console_id: an ID of the touch screen appliance
- model: (always AirTouch5)
- system_id: unique id for the system (useful for multiple units on the same network)
- name: the name given to the unit in the console settings

```
    client.device.system_id
```

you can still use the old way of just providing an ip address
```
client = Airtouch5SimpleClient(ip)
```
