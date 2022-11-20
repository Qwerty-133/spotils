"""View a pretty-formatted representation of a response's JSON."""
import json
import pprint

from spotipy import Spotify

from spotils import console, instance

response_data = Spotify.current_user_saved_tracks(instance, limit=2)

depth = 2

formatted_data = pprint.pformat(response_data, depth=depth)

# Change these to whatever you want
def print_response_data():
    console.print(formatted_data)


def dump_response_data(formatted=False):
    if formatted:
        with open("dump.txt", "w") as f:
            f.write(formatted_data)
    else:
        with open("dump.json", "w") as f:
            json.dump(response_data, f, indent=4)


# Comment this out to skip printing
print_response_data()

# Uncomment this to dump the JSON into dump.json
# Pass formatted=True to dump formatted data into dump.txt
# dump_response_data()
