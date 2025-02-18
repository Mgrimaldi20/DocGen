# DocGen
Generates HTML documentation for C code based upon a type of comment format above a function definition or declaration

## Running The Script
This is a python script that is simple to run, simply use it as follows:
```
python docgen.py /path/to/code
```

## The Comment String
The comment to put above functions looks something like this, there are some optional fields:
```
/*
* Function: FunctionName
* A description for the function, can be multi-line
* like this, where the description takes up two lines.
* 
* 	(optional)param1: Description of parameter one
* 	(optional)param2: Description of parameter two
* 
* (optional)Returns: A description of the return type or value
*/
```

The fields marked with optional are not required to exist, and any number of parameters may be used, I have just put two here for an example.

## Example Use In Real Code
```
/*
* Function: HashFileName
* Hashes the name of the file to generate an index
* 
* 	name: The name of the file
* 
* Returns: The hash value
*/
static size_t HashFileName(const char *name)
{
...
}
```

Above is a real function that I have in my game engine, with a comment string above it which will be used to generate web documentation.

This will also work in header files with declarations too, and a body does not need to be present.
```
/*
* Function: FileSys_Init
* Initializes the filesystem
* 
* Returns: A boolean if initialization was successful or not
*/
bool FileSys_Init(void);

/*
* Function: FileSys_Shutdown
* Shuts down the filesystem
*/
void FileSys_Shutdown(void);
```
