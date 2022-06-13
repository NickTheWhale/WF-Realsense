import opcua
import time
import random

# def update_gauge():
    # update the gauges with the OPC-UA values every 1 second
    # gtemp.set_value(client.get_node("ns=2;i=2").get_value())
    # gwind.set_value(client.get_node("ns=2;i=5").get_value())


d = 10

def main():
    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()

    while True:
        # pixels = client.get_node("ns=2;i=2").get_value()
         
        # for i in range(10):
        #     print(pixels[i])
        # print()
        
        # distance = client.get_node("ns=2;i=2").get_value()
        depth_node = client.get_node("ns=2;i=2")
        depth_node.set_value(random.randint(0, 10))
        # print(f'Distance (feet): {distance:0.4f}')
        
        time.sleep(0.01)


if __name__ == "__main__":
    main()