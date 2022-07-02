import opcua
from opcua import ua
import opcua.ua.uatypes
import time
import random


def main():

    print("Connecting to Server... ", end="")
    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()
    print("success")

    print("Gettings Nodes...       ", end="")

    roi_depth_node = client.get_node("ns=2;i=2")

    roi_accuracy_node = client.get_node("ns=2;i=3")

    roi_select_node = client.get_node("ns=2;i=4")

    status_node = client.get_node("ns=2;i=5")

    alive_node = client.get_node("ns=2;i=7")

    print("success")


    while True:

        # depth
        dv = random.random() * 10
        dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
        roi_depth_node.set_value(dv)

        # accuracy
        dv = random.random() * 10
        dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
        roi_accuracy_node.set_value(dv)

        # roi select
        dv = random.random() * 10
        dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
        roi_select_node.set_value(dv)

        # status
        dv = random.random() * 10
        dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Float))
        status_node.set_value(dv)

        # alive
        if not alive_node.get_value():
            dv = True
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            alive_node.set_value(dv)

        time.sleep(0.01)


if __name__ == "__main__":
    main()
