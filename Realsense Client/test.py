import pyrealsense2 as rs
pipeline = rs.pipeline()

config = rs.config()

profile = config.resolve(pipeline) # does not start streaming

profile = pipeline.start(config) # Start streaming

depth_sensor = profile.get_device().first_depth_sensor()

value = depth_sensor.get_option(rs.option.asic_temperature)

print(value)



print("Connecting Camera...     ", end="")
    
pipeline = rs.pipeline()

w, h, f = 848, 480, 30

camera_config = rs.config()

# camera_config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)

profile = camera_config.resolve(pipeline)

profile = pipeline.start(camera_config)

depth_sensor = profile.get_device().first_depth_sensor()

value = depth_sensor.get_option(rs.options.asic_temperature)

print(f'Temp: {value}')