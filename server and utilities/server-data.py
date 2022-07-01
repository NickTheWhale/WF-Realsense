import time

import opcua
from opcua import ua


LOOP_TIME = 50 # amount of time to wait every loop in milliseconds


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

    # depth
    roi_depth_node = opc_db.add_variable(
        idx, "roi_depth_node", 0, ua.VariantType.Float)
    roi_depth_node.set_writable(writable=True)

    # accuracy
    roi_accuracy_node = opc_db.add_variable(
        idx, "roi_accuracy_node", 0, ua.VariantType.Float)
    roi_accuracy_node.set_writable(writable=True)

    # roi select
    roi_select_node = opc_db.add_variable(
        idx, "roi_select_node", 0, ua.VariantType.Float)
    roi_select_node.set_writable(writable=True)

    # status
    status_node = opc_db.add_variable(
        idx, "status_node", 0, ua.VariantType.Float)
    status_node.set_writable(writable=True)

    # trigger
    picture_trigger_node = opc_db.add_variable(
        idx, "picture_trigger_node", 0, ua.VariantType.Boolean)
    picture_trigger_node.set_writable(writable=True)

    # alive
    alive_node = opc_db.add_variable(
        idx, "alive_node", 0, ua.VariantType.Boolean)
    alive_node.set_writable(writable=True)

    dead_count = 0
    picture_count = 0

    while True:
        # get tag values
        depth = roi_depth_node.get_value()
        accuracy = roi_accuracy_node.get_value()
        status = status_node.get_value()
        picture = picture_trigger_node.get_value()
        alive = alive_node.get_value()
        roi_select = roi_select_node.get_value()

        picture_count += 1

        if picture_count == 1:
            dv = True
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            picture_trigger_node.set_value(dv)
        elif picture_count != 1:
            dv = False
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            picture_trigger_node.set_value(dv)
        if picture_count > 15000 // LOOP_TIME:
            picture_count = 0

        # check if client is alive
        if alive:
            dead_count = 0
            dv = alive = False
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            alive_node.set_value(dv)
        else:
            dead_count += 1

        # print tag values
        print(f'Depth: {depth:.2f} | Accuracy: {accuracy:.2f} | '
              f'Status: {status:.2f} | Picture: {picture:.2f} | '
              f'Alive: {alive:.2f} | ROI select: {roi_select:.2f} | '
              f'Dead: {dead_count} | PicCount: {picture_count}')

        time.sleep(LOOP_TIME / 1000)


if __name__ == "__main__":
    main()
