# File value checker
When creating a data structure from a file this script allows to count the occurence of a value for a variable from inside a selection of files.
To use define your file reader inside file_definitions, modify the `config.json` file and run `compile_info.py`
It also keep track of errors when parsing the file.

## Configuring the script
The `config.json` is organized with one large array named `to_investigate` which contain a dictionnary of the different logs to make. This dictionnary is organized as follow :
```
{
    "files" : // Regular expression representing the path to files to explore, 
    "data_type" : // A file data structure (must be able to be initialized from a fileReader),
    "var_to_check" : // An array containing the different variable to check inside the data_type
}
```
Be warned that the script is designed for only one entry in `to_investigate` for each datatype as it will overwrite previous count of a variable.

### Syntax to check a variable
The array `var_to_check` is made up of string each representing one variable to keep track of to the logger. The string must be written as follow :
```
self.path.to.var
```
If the variable tracked is a list the value tracked by the logger will be its length. If the variable is inside a list the logger will track its value accross all variable of the list. It is possible to limit the scope using the following syntax (where to is our list of object containing var) :
```
self.path.to[1].var
```
Finally the syntax allow for only looking for slices but only between indexes `to[2:6]` is supported not `to[1:]`. On a final note, the program suppress any error from invalid index access and continue to the next file.