root = client.get_root_node()
        print("Root is", root)
        print("childs of root are: ", root.get_children())
        print("name of root is", root.get_browse_name())
        objects = client.get_objects_node()
        print("childs og objects are: ", objects.get_children())


        tag1 = client.get_node("ns=2;s=Channel1.Device1.Tag1")
        print("tag1 is: {0} with value {1} ".format(tag1, tag1.get_value()))
        tag2 = client.get_node("ns=2;s=Channel1.Device1.Tag2")
        print("tag2 is: {0} with value {1} ".format(tag2, tag2.get_value()))

        handler = SubHandler()
        sub = client.create_subscription(500, handler)
        handle1 = sub.subscribe_data_change(tag1)
        handle2 = sub.subscribe_data_change(tag2)

        from IPython import embed
        embed()

        
        sub.unsubscribe(handle1)
        sub.unsubscribe(handle2)
        sub.delete()