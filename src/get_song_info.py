import argparse
import json
import os
from pathlib import Path

import eyed3


# This is the name of the class, see `MusicInfo()` at the bottom
class MusicInfo:
    # Everything after this 'class MusicInfo' belongs to the MusicInfo object, when MusicInfo talks to itself it
    # uses `self` to self-reference itself.

    # init is your 'constructor' this doesn't matter right now but i left it in case you had questions
    def __init__(self):
        pass

    # call the eyed3 load api and return the artist, album, song title and track number
    # Note: 'track_num[0]' means the first item in the track_num tuple, track_num is unlike the others, it's a
    # 2-item tuple containing the track number and the total number of tracks. Most MP3's don't know the total
    # number of tracks and we don't care.
    def get_song_info_from_file(self, file_name):
        local_file_md = eyed3.load(file_name)
        # if local_file_md was populated successfully.. return the values
        if local_file_md:
            return local_file_md.tag.album_artist, local_file_md.tag.album, local_file_md.tag.title, \
                   local_file_md.tag.track_num[0]
        else:
            # throw an exception to let the caller know something went wrong when eyed3.load() was called.
            # Note: eyed3.load may also throw an error if something goes horribly wrong. I leave this to the caller
            # to handle. See 'try/except'.
            raise LookupError("Failed to find metadata for {}".format(file_name))

    # walk through a directory and it's subdirectory recursively saving the song information as you go along.
    def get_song_info_from_dir(self, root_dir):
        # {} indicates this is an empty dictionary, dictionaries are key/value pairs.
        dir_dict = {}

        # os.walk is used to walk through an input directory 'root_dir' until all sub-directories have been returned
        # each iteration of this loop returns the name of the directory containing 'file_list' and a list of
        # sub directories within that directory.
        for dir_name, sub_dir_list, file_list in os.walk(root_dir):
            # for every file in file list, meaning each file in 'dir_name' as we go along.
            for file in file_list:
                # try means, something could go wrong.. so try to do this and if it fails the code skips into the
                # 'except' block
                try:
                    fully_qualified_file_path = os.path.join(dir_name, file)
                    # call the api to get the song information
                    artist, album, title, trackno = self.get_song_info_from_file(fully_qualified_file_path)
                    # call our custom 'add_entry' method to add this song's details to 'dir_dict'
                    self.add_entry(dir_dict, artist, album, title, trackno, fully_qualified_file_path)
                except (Exception, LookupError) as e:
                    # something went wrong, odds are we don't care because we are calling the eyed3 api on every file
                    # in the directory including .ini files, etc. Only print exception details for files ending in 'mp3'
                    # we could make this better by including other audio format extensions.
                    if file.endswith(".mp3"):
                        # print a generic error, we dont have a log because we're lazy!
                        print("Exception {} for file {}".format(e, file))
                        # Add every 'mp3' file that failed processing into a list pointed to be the key 'FAILED'
                        # Hopefully a band is not named FAILED.
                        if 'FAILED' in dir_dict:
                            dir_dict['FAILED'].append(fully_qualified_file_path)
                        else:
                            dir_dict['FAILED'] = [fully_qualified_file_path]

        return dir_dict

    # This function adds entries to 'input_dict'. 'input_dict's format is
    # confusing. It's a dictionary keyed by artist which points to another
    # dictionary for album, then another dictionary for trackno, within this
    # dictionary is a tuple containing the track title and number.
    ''' For example:
    {
    "Amon Tobin": {
        "Permutation": {
            "3": [
                "Reanimator",
                "D:\\Music\\Khalil\\Amon Tobin\\Unsorted\\Permutation\\Amon Tobin - 03 - Reanimator.mp3"
            ],
            "8": [
                "People Like Frank",
                "D:\\Music\\Khalil\\Amon Tobin\\Unsorted\\Permutation\\Amon Tobin - 08 - People Like Frank.mp3"
            ]
        }
    }
    '''

    def add_entry(self, input_dict, artist, album, title, trackno, file_path):
        if artist in input_dict:
            if album in input_dict[artist]:
                input_dict[artist][album][trackno] = (title, file_path)
            else:
                input_dict[artist][album] = {trackno: (title, file_path)}
        else:
            input_dict[artist] = {album: {trackno: (title, file_path)}}


# Python's build in argument parser 'argparse'. A really good library for creating quick CLI access
# Note; This isn't within the MusicInfo object, this is under it, anything written in this tab-level
# will run whenever executed using `python <file_name>`
# in this case we defined 2 parameters `-p` or `--path` (either is fine they are synonymous
# and '-o' '--outputfile', both are Path types, python will ensure the input is validated as a
# path. Once we have these arguments we create the music info object and based on user input we
# execute in different ways.

parser = argparse.ArgumentParser(description='Get audio file metadata')
parser.add_argument('-p', '--path', type=Path, required=True)
# output file isn't required, if it's not set we write to standard output (the terminal).
parser.add_argument('-o', '--outputfile', type=Path, default=None)
# parse_args() reads the arguments from the user and places them into the 'args' variable accordingly
args = parser.parse_args()
# Create a MusicInfo() object
info = MusicInfo()

# if the input path is a directory, run the directory method
if os.path.isdir(args.path):
    # store the output from get_song_info into memory (RAM).
    # json.dumps let's us format it nicely but isn't necessary for anything
    # other than human readability.
    output = json.dumps(info.get_song_info_from_dir(args.path), indent=4)
else:
    # if the path indicated by the user is a file name like 'song.mp3' then we need only return the single file's info
    # A nice 'python' thing here is you can us ' within " or " within ' without escape characters. If I wanted
    # to use " within a string delimited by " i would use \" to do that.
    artist, album, title, trackno = info.get_song_info_from_file(args.path)
    output = "'{title}' by {artist} from album '{album}' track #{trackno}".format(artist=artist, title=title,
                                                                                  trackno=trackno,
                                                                                  album=album)
# is specified by the user, write the output to file
# we have output regardless, now write to a file if specified otherwise print it.
if args.outputfile:
    # with statements are neat, they allow you to open things like files
    # and once the indent is broken it releases the file handle / resources for you
    # so cleanup of closing the file is auto-magic.
    with open(args.outputfile, '+w') as output_file:
        output_file.write(output)
else:
    print(output)
