# coding=utf-8
"""Module containing the value logger and functions nescessary for its work"""

import os
import re
from os import path

from typing import Dict, List, Sequence

import pandas
from pandas.core.frame import DataFrame


def add_to_value(
    value_to_recover, var_data_frame: pandas.DataFrame
) -> pandas.DataFrame:
    """Add one to the count of one value, set it to one if it doesn't exist"""
    if var_data_frame["Value"].isin([value_to_recover]).any():
        var_data_frame.loc[var_data_frame["Value"] == value_to_recover, "Count"] += 1
    else:
        dataframe = DataFrame({"Value": [value_to_recover], "Count": [1]})
        var_data_frame = var_data_frame.append(dataframe)

    return var_data_frame


def look_for_value(
    var_seq, file_data_structure, var_name, dictionary
) -> None:
    """Initiate search for a value in a FileDataStructure"""

    def lookup_function(var_seq, last):
        """Recursive search in FileDataStructure for var_name (argument of look_for_value)"""
        if isinstance(last, List):
            for obj in last:
                lookup_function(var_seq, obj)
        else:
            match = re.search(r"\[\d+\]", var_seq[0])
            if match:
                ind = int(var_seq[0][match.span()[0] + 1 : match.span()[1] - 1])
                curr = getattr(last, var_seq[0][: match.span()[0]])[ind]
            else:
                curr = getattr(last, var_seq[0])
            if not isinstance(curr, bytes) and isinstance(curr, List):
                value = len(curr)
            else:
                value = curr

            if len(var_seq) > 1:
                lookup_function(var_seq[1:], curr)
            else:
                dictionary[var_name] = add_to_value(value, dictionary[var_name])

    lookup_function(var_seq, file_data_structure)


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

    logged_var: Dict[str, pandas.DataFrame]

    def __init__(self, variables_name: Sequence[str]) -> None:
        self.logged_var = {}
        self.error = []
        self.read_files = []
        self.log_path = ""
        for var_name in variables_name:
            self.logged_var.update(
                {var_name: pandas.DataFrame(columns=("Value", "Count"))}
            )

    def update(self, file_data_structure) -> None:
        """Looked for variable value to count inside the FileDataStructure"""
        self.log_path = ".\\results\\" + type(file_data_structure).__name__
        for var_name in self.logged_var:
            var_seq = var_name.split(".")
            look_for_value(var_seq[1:], file_data_structure, var_name, self.logged_var)

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
            values.to_csv(path_to_csv)

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
