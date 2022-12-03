"""View a pretty-formatted representation of a response's JSON."""
import json
import pprint

import rich
import rich.pretty
from spotipy import Spotify

from spotils import console, instance

# response_data must hold the response to be inspected
response_data = Spotify.current_user_saved_tracks(instance, limit=2)

# The maximum depth of the formatted data, assign this to None to remove
# the limit
depth = 2


def print_response_data():
    pretty_data = rich.pretty.Pretty(
        response_data, max_depth=depth, expand_all=True
    )
    console.print(pretty_data)


def dump_response_data(formatted=False):
    if formatted:
        formatted_data = pprint.pformat(response_data, depth=depth)

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
