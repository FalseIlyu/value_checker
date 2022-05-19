# coding=utf-8
"""Module containing the value logger and functions nescessary for its work"""

import os
import re
from os import path

from typing import Dict, List, Sequence

from pandas.core.frame import DataFrame


class ValueRangeLogger:
    """
    Count the values for asked variables in a FileDataStructure,
    use should be as follow.
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
        self.log_path = f".\\results\\{type(file_data_structure).__name__}"

        for var_name, dict_values in self.logged_var.items():
            var_seq = var_name.split(".")[1:]
            last = [file_data_structure]

            for seq in var_seq:
                matches = re.findall(r"\[(-?\d*)(\:?)(-?\d*)\]", seq)
                end = re.search(r"\[", seq)

                if end:
                    end = end.span()[0]

                indexes = [
                    (int(match[0]), int(match[2])) if match[1] and match[2]
                    else () if match[1]
                    else (int(match[0]),)
                    for match in matches
                ]

                for obj in last:
                    curr = getattr(obj, seq[:end])

                    for index in indexes:
                        if len(index) > 1:
                            curr = tuple(i for i in curr[index[0]: index[1]])
                        elif len(index) > 0:
                            curr = curr[index[0]]
                        else:
                            curr = tuple(i for i in curr)

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
            path_to_csv = f"{self.log_path}\\varsDist\\"

            if not path.exists(path_to_csv):
                os.mkdir(path_to_csv)

            file_name = re.sub(r"\.", "_", var_name)
            file_name = re.sub(r"\:", "to", var_name)
            path_to_csv += f"{file_name}.csv"
            temp_dict = {
                "Value": list(values.keys()),
                "Count": list(values.values()),
            }

            with open(path_to_csv, "wb") as writer:
                DataFrame(temp_dict).to_csv(writer)

        with open(
            f"{self.log_path}\\readFiles.txt", "wt", encoding="utf-8"
        ) as err_file:
            err_file.write(f"Completed file parse : {len(self.read_files)}\n")

            for successful_read in self.read_files:
                err_file.write(f"{successful_read}\n")
            err_file.write(
                f"\nFiles where an error was encountered : {len(self.error)}\n"
            )

            for err in self.error:
                err_file.write(f"{err}\n")

    def file_not_read(self, filepath: str) -> None:
        """Add the filepath to the list of file not read"""
        self.error.append(filepath)

    def file_read(self, filepath: str) -> None:
        """Add the filepath to the list of file read"""
        self.read_files.append(filepath)
