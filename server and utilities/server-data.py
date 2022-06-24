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
    
    # depth
    roi_depth_node = opc_db.add_variable(idx, "roi_depth_node", 0, ua.VariantType.Float)
    roi_depth_node.set_writable(writable=True)
    
    # accuracy
    roi_accuracy_node = opc_db.add_variable(idx, "roi_accuracy_node", 0, ua.VariantType.Float)
    roi_accuracy_node.set_writable(writable=True)
    
    # roi select
    roi_select_node = opc_db.add_variable(idx, "roi_select_node", 0, ua.VariantType.Float)
    roi_select_node.set_writable(writable=True)

    # status
    status_node = opc_db.add_variable(idx, "status_node", 0, ua.VariantType.Float)
    status_node.set_writable(writable=True)    

    # trigger
    picture_trigger_node = opc_db.add_variable(idx, "picture_trigger_node", 0, ua.VariantType.Boolean)
    picture_trigger_node.set_writable(writable=True)
    
    # alive
    alive_node = opc_db.add_variable(idx, "alive_node", 0, ua.VariantType.Boolean)
    alive_node.set_writable(writable=True)
    

    count = 0
    while True:
        depth = roi_depth_node.get_value()
        accuracy = roi_accuracy_node.get_value()
        status = status_node.get_value()
        picture = picture_trigger_node.get_value()
        alive = alive_node.get_value()
        roi_select = roi_select_node.get_value()

        print(f'Depth: {depth:.2f} | Accuracy: {accuracy:.2f} | '
              f'Status: {status:.2f} | Picture: {picture:.2f} | '
              f'Alive: {alive:.2f} | ROI select: {roi_select:.2f}')

        if count > 10:
            count = 0
            dv = True
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            picture_trigger_node.set_value(dv)
        else:
            dv = False
            dv = ua.DataValue(ua.Variant(dv, ua.VariantType.Boolean))
            picture_trigger_node.set_value(dv)
        time.sleep(0.5)


if __name__ == "__main__":
    main()


    # old stuff

    # depth_tag = opc_db.add_variable(
    #     idx, "Realsense Depth", 0, ua.VariantType.Float)
    # depth_tag.set_writable(writable=True)
    # depth_tag.set_value(0)

    # timer_tag = opc_db.add_variable(idx, "Counter", 0, ua.VariantType.Float)
    # timer_tag.set_writable(writable=True)
    # timer_tag.set_value(0)

    # client_tick_tag = opc_db.add_variable(
    #     idx, "Client Tick", 0, ua.VariantType.Boolean)
    # client_tick_tag.set_writable(writable=True)
    # client_tick_tag.set_value(0)

    # array_tag = opc_db.add_variable(
    #     idx, "Realsense Depth Array", 0, ua.VariantType.Float)
    # array_tag.set_writable(writable=True)
    # array_tag.set_value(0)
    
    
    # depth = depth_tag.get_value()
    # timer = timer_tag.get_value()
    # tick = client_tick_tag.get_value()
    # array = array_tag.get_value()
