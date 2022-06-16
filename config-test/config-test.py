# .ini configuration test

from configparser import ConfigParser
import logging

# instantiate
config = ConfigParser()

# parse file
rs = config.read('config.ini')
print(f'Read Status: {rs}')

# read values
if len(rs) > 0:
    ip = config.get('section_server', 'ip', fallback=None)
    depth = config.get('section_server', 'depth_node', fallback=None)
    timer = config.get('section_server', 'timer_node', fallback=None)
    client = config.get('section_server', 'client_node', fallback=None)
    array = config.get('section_server', 'array_node', fallback=None)

    print(f'ip:     {ip}')
    print(f'depth:  {depth}')
    print(f'timer:  {timer}')
    print(f'client: {client}')
    print(f'array:  {array}')
else:
    print('Cannot open file')


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

logging.debug("Debug message")

logging.info("Informative message")

logging.error("Error message")
