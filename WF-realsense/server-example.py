from importlib.resources import read_binary
import sys
sys.path.insert(0, "..")
import logging

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()

from opcua import ua, Server


def main():
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger("opcua.server.internal_subscription")
    logger.setLevel(logging.DEBUG)

    # setup our server
    server = Server()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # setup our own namespace, not really necessary but should as spec
    # uri = "http://examples.freeopcua.github.io"
    uri = "http://plc/"
    idx = server.register_namespace(uri)

    # get Objects node, this is where we should put our custom stuff
    objects = server.get_objects_node()
    print(f"Objects: {objects}")

    # populating our address space
    ready_bit_obj = objects.add_object(1, "ReadyBit")

    # Creating a custom event: Approach 1
    # The custom event object automatically will have members from its parent (BaseEventType).
    etype = server.create_custom_event_type(idx, 'MyFirstEvent', ua.ObjectIds.BaseEventType, 
                                            [('MyNumericProperty', ua.VariantType.Float), 
                                             ('MyStringProperty', ua.VariantType.String)])

    myevgen = server.get_event_generator(etype, ready_bit_obj)

    # Creating a custom event: Approach 2
    custom_etype = server.nodes.base_event_type.add_object_type(2, 'MySecondEvent')
    custom_etype.add_property(2, 'MyIntProperty', ua.Variant(0, ua.VariantType.Int32))
    custom_etype.add_property(2, 'MyBoolProperty', ua.Variant(True, ua.VariantType.Boolean))

    mysecondevgen = server.get_event_generator(custom_etype, ready_bit_obj)

    # starting!
    server.start()

    try:
        # time.sleep is here just because we want to see events in UaExpert
        import time
        count = 0
        while True:
            time.sleep(2)
            myevgen.event.Message = ua.LocalizedText("MyFirstEvent %d" % count)
            myevgen.event.Severity = count
            myevgen.event.MyNumericProperty = count
            myevgen.event.MyStringProperty = "Property " + str(count)
            myevgen.trigger()
            mysecondevgen.trigger(message="MySecondEvent %d" % count)
            print(f'Debug: {type(ready_bit_obj)} {ready_bit_obj.get_properties()} {ready_bit_obj.get_variables()}')
            count += 1

        embed()
    finally:
        # close connection, remove subcsriptions, etc
        server.stop()
        
        
if __name__ == "__main__":
    main()