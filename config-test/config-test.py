# .ini configuration test

from configparser import ConfigParser

# instantiate
config = ConfigParser()

# parse file
config.read('config.ini')

# read values
ip = config.get('section_server', 'ip')
depth = config.get('section_server', 'depth_node')
timer = config.get('section_server', 'timer_node')
client = config.get('section_server', 'client_node')
array = config.get('section_server', 'array_node')


print(f'ip:     {ip}')

print(f'depth:  {depth}')

print(f'timer:  {timer}')

print(f'client: {client}')

print(f'array:  {array}')
