import opcua
import time


# def update_gauge():
    # update the gauges with the OPC-UA values every 1 second
    # gtemp.set_value(client.get_node("ns=2;i=2").get_value())
    # gwind.set_value(client.get_node("ns=2;i=5").get_value())


def main():
    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()

    while True:
        print(f'Value: {client.get_node("ns=2;i=2").get_value()}')
        time.sleep(0.01)


if __name__ == "__main__":
    main()