import sys
sys.path.insert(0, "..")

try:
    from IPython import embed
except ImportError:
    import code

    def embed():
        vars = globals()
        vars.update(locals())
        shell = code.InteractiveConsole(vars)
        shell.interact()


from opcua import Client


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing.
    """
    def event_notification(self, event):
        print("New event recived: ", event)


def main():
    
    connections = []
    
    print("IP test\n")
    
    for ip in range(0, 65354):
        try:
            client = Client(f"tcp://localhost:{ip}")
            client.connect()
            print(f"Connected to {ip}")
            
            connections.append(ip)
            print(connections)
            
            client.disconnect()
        except:
            print(f"Error connecting to {ip}")
    # client = Client("tcp://localhost:49320")
    # try:
    #     client.connect()
        

if __name__ == "__main__":
    main()