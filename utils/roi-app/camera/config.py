"""
title:   RealSenseOPC client application config class
author:  Nicholas Loehrke 
date:    June 2022
license: TODO
"""

import configparser
import logging as log

MSG_ERROR_SHUTDOWN = "~~~~~~~~~~~~~~~Error Exited Application~~~~~~~~~~~~~~\n"


class Config():
    def __init__(self, path, required_data=None):
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
        
        self._path = path
        self._config_file = configparser.ConfigParser()
        try:
            file_list = self._config_file.read(self._path)
        except configparser.Error:
            raise

        if len(file_list) < 1:
            raise FileNotFoundError(f'"{self._path}" was not found')

        self._data = self._config_file.__dict__['_sections'].copy()

        if required_data is not None:
            self._required_data = required_data
            validity = self.is_valid()
            if len(validity) > 0:
                raise RuntimeError(
                    f'"{self._path}" is missing required configuration data: "{validity}"')

    def get_value(self, section: str, key: str, fallback=None) -> str:
        """gets config file value at specified location

        :param section: values section title
        :type section: string
        :param key: values key title
        :type key: string
        :param fallback: fallback value if unable to find value in file
        :type fallback: string
        :return: value
        :rtype: string
        """
        try:
            return self._data[section][key]
        except KeyError as e:
            if isinstance(fallback, str):
                log.warning(
                    f'Failed to get value from "[{section}]: {key}". Defaulting to "{fallback}"')
                return fallback
            log.error(f'Failed to get value from "[{section}]: {key}"')
            raise KeyError

    def is_valid(self):
        """checks if configuration file contains the required data

        :return: validity
        :rtype: bool
        """
        missing = []
        for section in self._required_data:
            if section == 'nodes':
                if len(self._data[section]) < 1:
                    missing.append((section, 'any_node'))
            else:
                for key in self._required_data[section]:
                    if key not in self._data[section]:
                        missing.append((section, key))
        return missing

    def save(self, file):
        """write configuration to file"""
        self._config_file.write(file, space_around_delimiters=True)        

    def set(self, *args, **kwargs):
        """assign value to section, key. Creates section of not found
        
        REQUIRED ARGS:
            section (str), option, (str), value (str)
        """
        try:
            self._config_file.set(*args, **kwargs)
        except configparser.NoSectionError:
            self._config_file.add_section(args[0])
            self._config_file.set(*args, **kwargs)
        
    @property
    def path(self):
        return self._path    
    
    @property
    def data(self):
        """configuration file contents

        :return: config file dictionary 
        :rtype: dict
        """
        return self._data

