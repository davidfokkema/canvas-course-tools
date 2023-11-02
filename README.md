# canvas-course-tools

Canvas course tools was created at the physics practicals at the Vrije Universiteit Amsterdam to greatly reduce the time needed to create class lists (with photos!) for staff and teaching assistants.
Class lists are also created for students so that they can easily lookup their assigned experiments and TA's.
Furthermore, we use it to create student groups on Canvas for peer feedback.

This package provides the `canvas` command-line utility.
After registering a Canvas URL and API key (which you can generate on your profile settings page) this tool allows you to list courses and students in different sections of your courses.
The output has a light markup and is ideally suited for saving as a text file.
It is then easy to copy and move lines inside the file to create student groups.
The file can then be parsed by the `canvas templates` command to render templates based on the text file.
This allows for creating class lists (with short notes for each student) and even class lists with photos (if you provide photos).

You can also use this tool to create groups and group sets on Canvas based on a group list file.
These groups can then be used for grading or peer feedback.
Especially for grading, it can be very helpful to review small groups of students instead of finding particular students in a long list.


## Installation

You can install using `pip` in any Python environment, but the recommended way to install canvas-course-tools is using [pipx](https://pypa.github.io/pipx/):
```console
$ pipx install canvas-course-tools
```
The `canvas` utility is available from the terminal.


## Tutorial

### Initial setup

First, we'll need to tell the `canvas` utility where it can find the Canvas installation of your institition.
If you run `canvas` without arguments it will show you a list of supported commands:
```console
$ canvas

 Usage: canvas [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────╮
│ --version      Show the version and exit.                            │
│ --help         Show this message and exit.                           │
╰──────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────╮
│ courses      Add, remove and list Canvas courses.                    │
│ groups       Create Canvas groups based on group lists.              │
│ servers      Add, remove and list Canvas servers.                    │
│ students     Search for or list students.                            │
│ templates    Generate files based on templates and group lists.      │
│ tui          Open Textual TUI.                                       │
╰──────────────────────────────────────────────────────────────────────╯
```
It appears that the `servers` command might be a good match. Let's check:
```console
$ canvas servers
                                                                        
 Usage: canvas servers [OPTIONS] COMMAND [ARGS]...                      
                                                                        
 Add, remove and list Canvas servers.                                   
                                                                        
╭─ Options ────────────────────────────────────────────────────────────╮
│ --help      Show this message and exit.                              │
╰──────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────╮
│ add     Register an alias for a server with corresponding access     │
│         token.                                                       │
│ list    List the registered servers.                                 │
│ remove  Remove server from configuration.                            │
╰──────────────────────────────────────────────────────────────────────╯
```
Let's try the `add` subcommand:
```console
$ canvas servers add
                                                                        
 Usage: canvas servers add [OPTIONS] ALIAS URL TOKEN                    
                                                                        
 Try 'canvas servers add --help' for help.                              
╭─ Error ──────────────────────────────────────────────────────────────╮
│ Missing argument 'ALIAS'.                                            │
╰──────────────────────────────────────────────────────────────────────╯
```
We're clearly missing something called `ALIAS` but the output is not very helpful.
It _does_ suggest, however, to include the `--help` argument.
If we do, we get:
```console
$ canvas servers add --help

 Usage: canvas servers add [OPTIONS] ALIAS URL TOKEN

 Register an alias for a server with corresponding access token.
 Example:
 canvas servers add school http://canvas.school.example.com/ 123~secret

╭─ Options ────────────────────────────────────────────────────────────╮
│ --force  -f    If alias already exists, force overwrite.             │
│ --help         Show this message and exit.                           │
╰──────────────────────────────────────────────────────────────────────╯
```
That helps! The output even gives an example of how to use the command.
Here, the alias `school` is used to refer to your institution's Canvas.
You can use this alias in other `canvas` commands when we need to refer to the Canvas server.
The `123~secret` should be the text of an access token that you can generate in your account page in Canvas.
For more information, please see the [Canvas documentation](https://canvas.instructure.com/doc/api/file.oauth.html#manual-token-generation) on how to generate tokens.
You can only view your token once.
If you lose it, you can revoke it from your Canvas profile page and generate a new one.
Once you've created your token, use it to add the server using the `canvas servers add` command as shown above.
If successful, your Canvas installation should be available in the list:
```console
$ canvas servers list

 ────────────────────────────────────────────
  Alias    URL
 ────────────────────────────────────────────
  school   http://canvas.school.example.com/
 ────────────────────────────────────────────
```
Now that we have registered the Canvas server, we can use the utility to do some work.
In the rest of this tutorial we will be more brief on how to use the different commands.
Don't forget you can always add `--help` to the end of any command to get a description of the command and the different ways you can use it.


### Listing and adding courses

You can list all courses accessible by your account using:
```console
$ canvas courses list school

 ────────────────────────────────────────────────────────────────────── 
  ID      Alias   Name                        Term                      
 ────────────────────────────────────────────────────────────────────── 
  12345           Physics 101                 2023-2024                
  23456           Calculus 102                2022-2023                
 ────────────────────────────────────────────────────────────────────── 
```
Note that the `Alias` field is still empty because we have not yet added courses.
You can add courses for future reference by creating an alias like this:
```console
$ canvas courses add phys101 school 12345
```
We first specified the alias (you can choose anything you like as long as it doesn't contain spaces) and after that we specified the server alias and the course ID.
We can see that it was successful:
```console
$ canvas courses list school

 ────────────────────────────────────────────────────────────────────── 
  ID      Alias     Name                       Term                     
 ────────────────────────────────────────────────────────────────────── 
  12345   phys101   Physics 101                2023-2024               
  23456             Calculus 102               2022-2023               
 ────────────────────────────────────────────────────────────────────── 
```
To only list registered courses we can leave off the canvas server as an argument:
```console
$ canvas courses list

 ────────────────────────────────────────────────────────────────────── 
  ID      Alias     Name                       Term                     
 ────────────────────────────────────────────────────────────────────── 
  12345   phys101   Physics 101                2023-2024               
 ────────────────────────────────────────────────────────────────────── 
```
We can now use this course alias (`phys101`) in other `canvas` commands.