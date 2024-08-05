# -*- coding: utf-8 -*-

import json


class Util:
    @staticmethod
    def convert_numeric_strings(data: dict) -> dict:
        def convert_value(value):
            if isinstance(value, str) and value.isdigit():
                return int(value)
            elif isinstance(value, (dict, list)):
                return Util.convert_numeric_strings(value)
            return value

        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = convert_value(value)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                data[index] = convert_value(value)
    
        return data
    
    @staticmethod
    def convert_string_to_list(data) -> list:
        if (isinstance(data, str)):
            d = json.loads(data)
        else:
            d = data
        Util.convert_numeric_strings(d)
        return d
