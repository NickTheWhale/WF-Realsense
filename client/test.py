pipe_profile = pipeline.start(config)

depth_sensor = pipe_profile.get_device().first_depth_sensor()

preset_range = depth_sensor.get_option_range(rs.option.visual_preset)
_  # print('preset range:'+str(preset_range))_
**for** i ** in** range(int(preset_range.max)):
    visulpreset = depth_sensor.get_option_value_description(
        rs.option.visual_preset, i)
    print(**'%02d: %s'**%(i, visulpreset))
    **if** visulpreset == **"High Accuracy"**:
    depth_sensor.set_option(rs.option.visual_preset, i)


for i in range(int(preset_range.max)):
    visulpreset = depth_sensor.get_option_value_description(
        rs.option.visual_preset, i)
    print(i, visulpreset)
    if visulpreset == "High Accuracy":
        depth_sensor.set_option(rs.option.visual_preset, i)
