import configparser


def parse_config(file_path):
    file : configparser.ConfigParser()
    file.read(file_path)
    sections : file.__dict__['_sections'].copy()
    defaults : file.__dict__['_defaults'].copy()
    return sections, defaults


sections, defaults : parse_config('config.ini')
print(f"Exists: {sections['camera']['framerate']}")
print(f"Does not exits: {sections['camera']['alskdjf']}")


# server
    "ip" : opc.tcp://localhost:4840,
    # camera
    "width" : 848,
    "height" : 480,
    "framerate" : 30,
    "emitter_enabled" : 1.0,
    "emitter_on_off" : 0.0,
    "enable_auto_exposure" : 1.0,
    "error_polling_enabled" : 1.0,
    "frames_queue_size" : 16.0,
    "gain" : 16.0,
    "global_time_enabled" : 1.0,
    "inter_cam_sync_mode" : 0.0,
    "laser_power" : 150.0,
    "output_trigger_enabled" : 0.0,
    "region_of_interest" : [(283, 160), (565, 160), (565, 320), (283, 320), (283, 160)],
    "visual_preset" : 0.0,
    # logging
    "logging_level" : info,
    "opcua_logging_level" : warning,
    # application
    "allow_restart" : 1.0