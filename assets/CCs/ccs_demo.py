# This is the demo file of the CCSA (Custom Command System API) to add custom commands to the terminal.
# There are 2 important things to keep in mind:
# 1. All the names must be the same in all files (e.g. class name, class attribute names, parameters of the custom command).
#    Because the part that checks it uses specific names - have a look at modules/commandHandler.py line: 198 to understand what I mean
# 2. Your function must be in this shape:
#    def func_name(command_list, full_command):
#    - `command_list`: a list holding the parts of the command (e.g. if entered `test ok no`, it will be ['test', 'ok', 'no'])
#    - `full_command`: a string holding the entire command (e.g. what you write to the terminal -> 'test ok no')
# 3. IDK what to write here lmao, I just said there were 2 things, just read everything else carefully.

# The command to run
def com(cmdlist, cmdall):  # cmdlist holds the list version of the command e.g. ['test', 'remove', 'hello'], cmdall holds the whole command e.g. 'test remove hello'
    j = 0
    print("It worked!")
    print(f"The command you ran is: {cmdall}")
    for i in cmdlist:
        if i != "test":
            j += 1
            print(f"{j}. Parameter --> {i}")


class CCS:
    def __init__(self):
        self.isHidden = True  # This will hide the command from the help menus, making help, alias, and detailedHelp attributes not required. This should make easter eggs easier!
        self.help = "This is a test command for the CCS"  # The text to show as the help
        self.command = "test"  # Command's name, also means what will be called on the terminal
        # e.g. If this is set to 'somtin', you must write 'somtin' in the terminal to run the command
        self.whenRan = com  # The function to be called when the command is run, do not include parentheses! It will cause a crash!(Too lazy to set up a try-except block)
        self.alias = "t"  # Optional: A shortcode alias for the command, like 't' for the command 'test' !!! KEEP IN MIND THAT THESE CAN OVERLAP AND CAUSE UNWANTED PROBLEMS !!!
        self.detailedHelp = "This command will print the parameters you entered, since it's a test command"  # Optional: A detailed help message for the command
