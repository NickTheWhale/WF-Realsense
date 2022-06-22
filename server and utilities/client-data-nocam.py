import opcua
from opcua import ua
import opcua.ua.uatypes
import time
import random as r


def main():

    print("Connecting to Server... ", end="")
    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()
    print("success")

    print("Gettings Nodes...       ", end="")
    # depth_node = client.get_node('ns=3;s="OPC Testing"."Realsense Depth"')
    # timer_node = client.get_node('ns=3;s="OPC Testing"."Counter"')
    # client_tick = client.get_node('ns=3;s="OPC Testing"."Client Tick"')
    # array_node = client.get_node('ns=3;s="OPC Testing"."Realsense Depth Array"')

    depth_node = client.get_node('ns=2;i=2')
    timer_node = client.get_node('ns=2;i=3')
    client_tick = client.get_node('ns=2;i=4')
    array_node = client.get_node('ns=2;i=5')

    print("success")

    tick = False

    while True:

        # Send data to PLC
        dv = ua.DataValue(ua.Variant(r.random(), ua.VariantType.Float))
        depth_node.set_value(dv)

        dv = ua.DataValue(ua.Variant(r.random(), ua.VariantType.Float))
        timer_node.set_value(dv)

        tick = not tick
        dv = ua.DataValue(ua.Variant(tick, ua.VariantType.Boolean))
        client_tick.set_value(dv)

        arr = []
        for i in range(100):
            arr.append(r.random())

        dv = ua.DataValue(ua.Variant(arr, ua.VariantType.Float))
        array_node.set_value(dv)

        time.sleep(0.01)


if __name__ == "__main__":
    main()
