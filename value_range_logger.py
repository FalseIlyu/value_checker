# coding=utf-8
"""Module containing the value logger and functions nescessary for its work"""

import os
import re
from os import path

from typing import Dict, List, Sequence

from pandas.core.frame import DataFrame


class ValueRangeLogger:
    """
    Count the values for asked variables in a FileDataStructure, use should be as follow.
    If a variable is a list the value counted will be its size.
    Add values to look for using add_var or add_vars.
    Open the file and instanciate a FileDataStructure
    if the file opens:
        call update using the FileDataStructure
        (Optional) call file_read
    (Optional) else:
        call file_not_read
    """

    logged_var: Dict[str, Dict]

    def __init__(self, variables_name: Sequence[str]) -> None:
        self.logged_var = {}
        self.error = []
        self.read_files = []
        self.log_path = ""
        for var_name in variables_name:
            self.logged_var.update({var_name: {}})

    def update(self, file_data_structure) -> None:
        """Looked for variable value to count inside the FileDataStructure"""
        self.log_path = ".\\results\\" + type(file_data_structure).__name__
        for var_name, dict_values in self.logged_var.items():
            var_seq = var_name.split(".")[1:]
            last = [file_data_structure]
            for seq in var_seq:
                match = re.search(r"\[\d+\]", seq)
                if match:
                    index = int(seq[match.span()[0] + 1 : match.span()[1] - 1])
                else:
                    index = None

                for obj in last:
                    if not index is None:
                        curr = getattr(obj, seq[: match.span()[0]])[index]
                    else:
                        curr = getattr(obj, seq)

                    if isinstance(curr, List):
                        new_last = curr
                        value = len(curr)
                    else:
                        new_last = [curr]
                        value = curr

                    if seq in var_seq[-1]:
                        if value in dict_values.keys():
                            dict_values[value] += 1
                        else:
                            dict_values[value] = 1

                last = new_last

    def write_log(self) -> None:
        """Write the compiled info in the ./resulsts folder"""
        if not path.exists(self.log_path):
            os.makedirs(self.log_path)

        for var_name, values in self.logged_var.items():
            path_to_csv = self.log_path + "\\varsDist\\"
            if not path.exists(path_to_csv):
                os.mkdir(path_to_csv)
            file_name = re.sub(r"\.", "_", var_name)
            path_to_csv += file_name + ".csv"
            temp_dict = {
                "Value": list(values.keys()),
                "Count": list(values.values()),
            }
            DataFrame(temp_dict).to_csv(path_to_csv)

        with open(
            self.log_path + "\\readFiles.txt", "wt", encoding="utf-8"
        ) as err_file:
            err_file.write("Completed file parse : " + str(len(self.read_files)) + "\n")
            for successful_read in self.read_files:
                err_file.write(str(successful_read) + "\n")
            err_file.write(
                "\nFiles where an error was encountered : "
                + str(len(self.error))
                + "\n"
            )
            for err in self.error:
                err_file.write(str(err) + "\n")

    def file_not_read(self, filepath: str) -> None:
        """Add the filepath to the list of file not read"""
        self.error.append(filepath)

    def file_read(self, filepath: str) -> None:
        """Add the filepath to the list of file read"""
        self.read_files.append(filepath)
