import argparse
import os.path
import json
import sys

from api import Api
from files import Files
from slack import Slack
from status import Status
from switches import Switches

def arg_setup():
    # Required args
    parser = argparse.ArgumentParser()
    parser.add_argument('token',
                        help="Slack authorisation token")
    parser.add_argument('dm',
                        help="ID of the direct message chat")

    # Date args
    parser.add_argument('-df', '--date-format',
                        help="Date format to use. Supported options: " + Switches.list_enum(Switches.DateModes))
    parser.add_argument('-ds', '--date-start',
                        help="Earliest messages to archive (inclusive)")
    parser.add_argument('-de', '--date-end',
                        help="Latest messages to archive (exclusive)")

    # Export args
    parser.add_argument('-o', '--output', nargs='?', const='output', default='',
                        help="Output directory to use for exports (excluding files)")
    parser.add_argument('-j', '--json', nargs='?', const='dm.json',
                        help="Output the message history in raw json form")
    parser.add_argument('-t', '--text', nargs='?', const='dm.txt',
                        help="Output the message history in human readable form")

    # File args
    parser.add_argument('-f', '--files', nargs='?', const='output_files',
                        help="Download files found in JSON to the directory")
    parser.add_argument('-fo', '--files-overwrite', action='store_true',
                        help="Overwrite files if they exist")

    # Process basic args
    parsed_args = parser.parse_args()
    Switches.set_switches(parsed_args, parser)
    Api.token = parsed_args.token

    return parsed_args

def get_user_map():
    print("Retrieving user mappings")
    user_id_map = {}

    # Make requests until response_metadata has no cursor
    cursor = None
    while True:
        profiles, cursor = Api.get_profiles(cursor)

        for profile in profiles:
            user_id_map[profile['id']] = profile['profile']['display_name']

        if cursor is None:
            break

    return user_id_map

def get_conversation_map():
    print("Retrieving conversation mappings")
    conv_id_map = {}

    # Make requests until response_metadata has no cursor
    cursor = None
    while True:
        conversations, cursor = Api.get_conversations(cursor)

        for conv in conversations:
            name = conv['name']
            if conv['is_im']:
                name = "@" + name
            else:
                name = "#" + name

            conv_id_map[conv['id']] = name

        if cursor is None:
            break

    return conv_id_map

def write_to_file(file: str, data):
    # Get full path and create directory if it doesn't exist
    loc = os.path.join(args.output, file)
    print(f"Saving data to {loc}")
    Files.make_dirs(loc)

    # Write to file and return true/false
    try:
        with open(loc, "w", encoding='utf-8') as f:
            f.write(data)
    except (IOError, FileNotFoundError) as e:
        print(e)
        return False

    return True

def download_files(file_list):
    # Old method using scraping
    # files = Files.get_files(messages)
    if len(file_list) == 0:
        return

    # Download files
    print("")
    for file in file_list:
        success = Files.download_file(args.token, file, args.files, user_map, overwrite=args.files_overwrite)

        if success:
            Status.tot_files += 1
        else:
            Status.file_failures += 1

    # Status messages
    print("File download complete")
    if Status.files_already_exist == 0:
        return
    if args.files_overwrite:
        print(f"{Status.files_already_exist} files were overwritten")
    else:
        print(f"{Status.files_already_exist} files were not downloaded as files with the same name already existed")

# PROGRAM START
args = arg_setup()

# Retrieve messages
messages = Api.get_conv_history(args.dm, Switches.date_start, Switches.date_end)
messages.reverse()

# Get user map
print("")
user_map = get_user_map()
conversation_map = get_conversation_map()
slack = Slack(user_map, conversation_map)

# Write to JSON
if args.json is not None:
    print("Exporting raw json")
    Status.export_json = not write_to_file(args.json, json.dumps(messages, indent=4))

# Write to txt
if args.text is not None:
    print("Formatting text")
    formatted_text = slack.format_messages(messages)
    print("Exporting text")
    Status.export_text = not write_to_file(args.text, formatted_text)

if args.files is not None:
    print("\nRetrieving list of ALL files uploaded to slack")
    files = Api.get_file_list(args.dm, Switches.date_start, Switches.date_end)
    print(f"Found {len(files)} file(s) that were sent in {args.dm}")

    download_files(files)

Status.print_warnings()
