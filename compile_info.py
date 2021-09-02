# coding=utf-8
"""
    Compile all information requested by the config .json file.
"""

from glob import iglob
import json

from file_definitions import *
from value_range_logger import ValueRangeLogger


if __name__ == "__main__":
    with open(".\\config.json", encoding="utf-8") as config:
        formats_to_investigate = json.load(config)
        formats_to_investigate = formats_to_investigate["to_investigate"]
        for current_format in formats_to_investigate:
            value_logger = ValueRangeLogger(current_format["var_to_check"])
            data_type = globals()[current_format["data_type"]]

            for file_path in iglob(current_format["files"]):
                try:
                    with open(file_path, "rb") as reader:
                        file_data_structure = data_type(reader)
                        value_logger.update(file_data_structure)
                        value_logger.file_read(file_path)
                except ValueError:
                    value_logger.file_not_read(file_path)
                except IndexError:
                    continue

            value_logger.write_log()
