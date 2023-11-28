import argparse

def argument_parser():
    parser = argparse.ArgumentParser(description= "This application provides each biciMAD worker with a route for the district assigned to them.")
    help_message = "You have to select the district that has been assigned to you today. You can do this by entering '-d' and the district number. If nothing is entered, an entry will appear for you to enter the district number. Remember to enter the entry in the format '01'. Drive safely and have a nice day."
    parser.add_argument("-d", "--district", help=help_message, type=str)
    args = parser.parse_args()
    return args