
    try:
        while True:
            if camera.connected:
                if not camera.depth_frame:
                    continue
                depth = camera.ROI_depth(
                    list(eval(config.get_value('camera', 'region_of_interest'))))
                ret, x, y, z = camera.accel_data()
                
                if ret:
                    ta = sqrt(x*x + y*y + z*z)
                    ta = sqrt(-1)