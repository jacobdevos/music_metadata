import argparse
import json
import os
from pathlib import Path

import eyed3
import musicbrainzngs

OUTPUT_FORMAT = "{}, by {}"


class MusicInfo:

    def __init__(self):
        musicbrainzngs.set_useragent("Example music app", "0.1", "https://github.com/jacobdevos/musicbrainz")

    def get_song_info_from_file(self, file_name):
        local_file_md = eyed3.load(file_name)
        if local_file_md:
            return local_file_md.tag.album_artist, local_file_md.tag.album, local_file_md.tag.title, \
                   local_file_md.tag.track_num[0]
        else:
            raise LookupError("Failed to find metadata for {}".format(file_name))

    def get_song_info_from_dir(self, root_dir):
        dir_dict = {}
        for dir_name, sub_dir_list, file_list in os.walk(root_dir):
            for file in file_list:
                fully_qualified_file_path = os.path.join(dir_name, file)
                try:
                    artist, album, title, trackno = self.get_song_info_from_file(fully_qualified_file_path)
                    self.add_entry(dir_dict, artist, album, title, trackno, fully_qualified_file_path)
                except Exception as e:
                    if file.endswith(".mp3"):
                        print(e)
        return dir_dict

    def add_entry(self, input_dict, artist, album, title, trackno, file_path):
        if artist in input_dict:
            if album in input_dict[artist]:
                input_dict[artist][album][trackno] = (title, file_path)
            else:
                input_dict[artist][album] = {trackno: (title, file_path)}
        else:
            input_dict[artist] = {album: {trackno: (title, file_path)}}


parser = argparse.ArgumentParser(description='Get audio file metadata')
parser.add_argument('-p', '--path', type=Path, required=True)
parser.add_argument('-o', '--outputfile', type=Path, default=None)
args = parser.parse_args()
info = MusicInfo()
if os.path.isdir(args.path):
    output = json.dumps(info.get_song_info_from_dir(args.path), indent=4)
    if args.outputfile:
        with open(args.outputfile, '+w') as output_file:
            output_file.write(output)
    else:
        print(output)
elif os.path.isfile(args.path):
    artist, album, title, trackno = info.get_song_info_from_file(args.path)
    output = "{title} by {artist} from album {album} track {trackno}".format(artist=artist, title=title,
                                                                             trackno=trackno,
                                                                             album=album)
    if args.outputfile:
        with open(args.outputfile, '+w') as output_file:
            output_file.write(output)
    else:
        print(output)
