import opcua
import time
import random

def main():

    client = opcua.Client("opc.tcp://localhost:4840")
    client.connect()

    depth_tag = client.get_node("ns=2;i=2")
    delay_tag = client.get_node("ns=2;i=3")
    loop_time_tag = client.get_node("ns=2;i=4")
    
    while True:
        now = time.time()
        depth_tag.set_value(random.randint(0, 9))
        delay_tag.set_value(time.time())
        loop_time_tag.set_value(time.time() - now)
        time.sleep(0.005)


if __name__ == "__main__":
    main()
