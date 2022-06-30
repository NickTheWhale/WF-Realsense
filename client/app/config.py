"""
title:   RealSenseOPC client application config class
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import configparser


class Config():
    def __init__(self, file_name, required_data=None):
        """creates config object

        :param file_name: name of file
        :type file_name: string
        :param required_data: nested dictionary with section titles and key. Values
        be anything or None
        :type required_data: dict
        :raises FileNotFoundError: if unable to open file
        :raises RuntimeError: if there is a discrepency between the configuration
        file data and the requried data dict
        """
        config_file = configparser.ConfigParser()
        try:
            file_list = config_file.read(file_name)
        except configparser.DuplicateOptionError as e:
            raise e

        if len(file_list) <= 0:
            raise FileNotFoundError(f'"{file_name}" was not found')

        self.__data = config_file.__dict__['_sections'].copy()

        if required_data is not None:
            self.__required_data = required_data
            validity = self.is_valid()
            if len(validity) > 0:
                raise RuntimeError(
                    f'"{file_name}" is missing required configuration data: "{validity}"')

    def get_value(self, section, key):
        """gets config file value at specified location

        :param section: values section title
        :type section: string
        :param key: values key title
        :type key: string
        :return: value
        :rtype: string
        """
        return self.__data[section][key]

    def is_valid(self):
        """checks if configuration file contains the required data

        :return: validity
        :rtype: bool
        """
        missing = []
        for section in self.__required_data:
            if section == 'nodes':
                if len(self.__data[section]) < 1:
                    missing.append((section, 'any_node'))
            else:
                for key in self.__required_data[section]:
                    if key not in self.__data[section]:
                        missing.append((section, key))
        return missing

    @property
    def data(self):
        """configuration file contents

        :return: config file dictionary 
        :rtype: dict
        """
        return self.__data
