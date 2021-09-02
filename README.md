# File value checker
When creating a data structure from a file this script allows to count the occurence of a value for a variable from inside a selection of files.
To use define your file reader inside file_definitions and modify the `config.json` file.

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