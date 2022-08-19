"""
title:   RealSenseOPC client application
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import logging as log
import os
import sys
import time

import opcua
import opcua.ua.uatypes
from opcua import Node, ua


IP = 'opc.tcp://localhost:4840'

ROI_DEPTH_NODE = 'ns=2;i=2'
ROI_INVALID_NODE = 'ns=2;i=3'
ROI_DEVIATION_NODE = 'ns=2;i=4'
ROI_SELECT_NODE = 'ns=2;i=5'
STATUS_NODE = 'ns=2;i=6'
ALIVE_NODE = 'ns=2;i=8'


def _setup_logging() -> None:
    """setup root and opcua logging levels"""
    log.getLogger().setLevel(log.DEBUG)
    log.getLogger(opcua.__name__).setLevel(log.WARNING)


def _setup_opc(ip: str) -> opcua.Client:
    """setup opc connection"""
    try:
        client = opcua.Client(ip)
        client.connect()
        log.info(f'Successfully setup opc client connection to "{ip}"')
    except OSError:
        log.critical(f'Failed to connect to server')
        os._exit(1)
    return client


def setup() -> tuple:
    """setup client connection and logging"""
    try:
        _setup_logging()
        client = _setup_opc(IP)
    except Exception as e:
        log.critical(f'Error in setup: {e}')
        os._exit(1)

    return client


class App:
    def __init__(self, client: opcua.Client):
        self._client = client

        self._nodes = self.get_nodes()
        self._running = True

    def run(self) -> None:
        """main loop"""
        log.info('Running')
        while self._running:
            self.read_nodes()
            
            time.sleep(1)

    def write_node(self, node: Node, value, type: ua.VariantType) -> bool:
        """write value to node

        :param node: node
        :type node: Node
        :param value: write value
        :type value: any
        :param type: value type to convert value to
        :type type: ua.VariantType
        """
        try:
            dv = ua.DataValue(ua.Variant(value, type))
            node.set_value(dv)
        except (ua.UaError, TimeoutError) as e:
            log.error(f'Failed to set "{node.get_browse_name()}" to "{value}": {e}')
            return False
        return True

    def read_node(self, node: Node) -> None:
        """get node value"""
        try:
            return node.get_value()
        except ua.UaError as e:
            log.error(f'Failed to get "{node.get_browse_name()}": {e}')
            
    def read_nodes(self) -> None:
        """log node values"""
        longest = max([len(x) for x in self._nodes])

        for node in self._nodes:
            val = self.read_node(self._nodes[node])
            current = len(node)
            spaces = ' ' * (longest - current)
            log.info(f'"{node}":{spaces} {val}')
        print()

    def get_nodes(self) -> None:
        """retrieve nodes from opc server"""
        try:
            self._nodes = {
                'roi_depth': self.get_node(ROI_DEPTH_NODE),
                'roi_invalid': self.get_node(ROI_INVALID_NODE),
                'roi_deviation': self.get_node(ROI_DEVIATION_NODE),
                'roi_select': self.get_node(ROI_SELECT_NODE),
                'status': self.get_node(STATUS_NODE),
                'alive': self.get_node(ALIVE_NODE)
            }
        except Exception as e:
            log.error(f'Failed to retrieve nodes from server: {e}', False)
            self.stop()
        else:
            return self._nodes

    def get_node(self, nodeid: str) -> Node:
        """retrieve node from opc server"""
        return self._client.get_node(nodeid)

    def stop(self) -> None:
        """disconnect client and exit"""
        try:
            self._client.disconnect()
        except RuntimeError:
            pass
        sys.exit()


def main():
    client = setup()
    app = App(client)

    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()
    except TimeoutError:
        print('itmeout')
        app.stop()


if __name__ == '__main__':
    main()
