import time

import opcua
from opcua import ua


def main():
    server = opcua.Server()
    server.set_server_name("Realsense OCP")
    server.set_endpoint("opc.tcp://localhost:4840")

    # Register the OPC-UA namespace
    idx = server.register_namespace("http://localhost:4840")
    # Start the OPC UA server (no tags at this point)
    server.start()

    # Populate address space
    objects = server.get_objects_node()
    opc_db = objects.add_object(idx, "OPC Testing")

    # Add tags
    depth_tag = opc_db.add_variable(
        idx, "Realsense Depth", 0, ua.VariantType.Float)
    depth_tag.set_writable(writable=True)
    depth_tag.set_value(0)

    timer_tag = opc_db.add_variable(idx, "Counter", 0, ua.VariantType.Float)
    timer_tag.set_writable(writable=True)
    timer_tag.set_value(0)

    client_tick_tag = opc_db.add_variable(
        idx, "Client Tick", 0, ua.VariantType.Boolean)
    client_tick_tag.set_writable(writable=True)
    client_tick_tag.set_value(0)

    array_tag = opc_db.add_variable(
        idx, "Realsense Depth Array", 0, ua.VariantType.Float)
    array_tag.set_writable(writable=True)
    array_tag.set_value(0)

    while True:
        depth = depth_tag.get_value()
        timer = timer_tag.get_value()
        tick = client_tick_tag.get_value()
        array = array_tag.get_value()

        print(f'Depth: {depth} Timer: {timer} Tick: {tick}')

        time.sleep(0.5)


if __name__ == "__main__":
    main()
