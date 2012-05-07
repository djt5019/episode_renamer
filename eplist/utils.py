# -*- coding: utf-8 -*-
"""
A module containing general utilities and text functions / parsing
functionality for the program
"""
from __future__ import unicode_literals

import os
import sys
import json
import time
import logging

from eplist import constants

from eplist.settings import Settings

import requests

if Settings.py3k:
    from urllib.parse import quote_plus
    basestring = bytes
    unicode = str
    raw_input = input
else:
    from urllib import quote_plus


def get_url_descriptor(url):
    """
    Returns an url descriptor or None on failure
    """
    try:
        resp = requests.get(url)
    except requests.exceptions.ConnectionError:
        logging.error("Error connecting to {}".format(url))
        return None

    if resp.ok:
        return resp

    return None


def is_valid_file(filename):
    """
    Returns true if the filename is a valid video file
    """
    ext = os.path.splitext(filename)[1].lower()

    return os.path.isfile(filename) and ext in constants.video_extensions


##############################
## Renaming utility functions
##############################
def regex_search(filename):
    """
    Compare the filename to each of the regular expressions for a match
    """
    if not filename:
        return {}

    logging.info("Matching '{}'".format(filename))
    # deal with anything in brackets, they tend to throw off the regexes
    filename = filename.lower()

    encoding = constants.encoding_regex.search(filename)
    filename = constants.encoding_regex.sub("", filename)

    checksum = constants.checksum_regex.search(filename)
    filename = constants.checksum_regex.sub("", filename)

    season = constants.bracket_season_regex.search(filename)
    filename = constants.bracket_season_regex.sub('', filename)

    filename = filename.replace('h.264', '')

    filename = constants.remove_junk_regex.sub("", filename)

    regex_result = None
    for count, regex in enumerate(constants.regexList):
        regex_result = regex.search(filename)
        if regex_result:
            name = filename.encode(Settings.encoding, 'ignore')
            msg = "Regex #{} matched {}".format(count, name)
            logging.info(msg)
            break

    # Work with the result dict rather than the annoying groupdicts
    result = {}
    result.update(encoding.groupdict() if encoding else {})
    result.update(checksum.groupdict() if checksum else {})
    result.update(season.groupdict() if season else {})
    result.update(regex_result.groupdict() if regex_result else {})

    if not regex_result:
        msg = "Unable to find information on: {}".format(filename)
        logging.error(msg)
        return {}

    logging.info(result)

    # Info dict will hold the proper data for our episode or special
    info_dict = {}
    if 'junk' in result:
        return info_dict

    result['checksum'] = result.get('checksum', None)

    if 'special_number' in result:
        result['special_number'] = int(result['special_number'])
        result['special_type'] = result.get('special_type', 'ova')
    else:
        result['episode_number'] = int(result['episode_number'])
        result['season'] = int(result.get('season', '1'))

    result['encoding'] = result.get('encoding', None)

    return result


def clean_filenames(path):
    """
    Attempts to extract order information about the files passed
    returns: list of EpisodeFiles
    """

    from eplist import episode
    # Filter out anything that doesnt have the correct extension and
    # filter out any directories
    files = []
    for file_ in os.listdir(path):
        if is_valid_file(os.path.join(path, file_)):
            files.append(file_)
        else:
            logging.info("Invalid file: {}".format(file_))

    if not files:
        logging.error("No video files were found in {}".format(path))
        return []

    cleanFiles = []
    # We are going to store the episode number and path in a tuple then
    # sort on the episodes number.  Special episodes will be appended to the
    # end of the clean list
    for file_ in files:
        info = regex_search(file_)

        if info:
            info['path'] = os.path.join(path, file_)
            info['ext'] = os.path.splitext(info['path'])[1]
            info['name'] = encode(os.path.split(info['path'])[1])

            episode_data = episode.EpisodeFile(info)

            cleanFiles.append(episode_data)

    if not cleanFiles:
        logging.error("The files could not be matched")
        return cleanFiles

    logging.info("Successfully cleaned the file names")

    return cleanFiles


def prepare_filenames(path, show):
    """
    Rename the files located in 'path' to those in the list 'show', modifies
    the show objects episodeList/specialsList
    """
    path = os.path.abspath(path)
    cleanFiles = []
    episode_files = clean_filenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable
    if not episode_files:
        logging.info("No files were able to be renamed")
        return

    for file_ in episode_files:
        if file_.is_special:
            episode_data = show.get_special(file_.special_number)

            if not episode_data:
                msg = "Could not find a special episode for {}".format(file_)
                logging.info(msg)
                continue
        elif 1 < show.num_episodes < file_.episode_number:
            episode_data = show.get_special(file_.episode_number - show.max_episode)
        else:
            episode_data = show.get_episode(file_.episode_number, file_.season)

        if not episode_data:
            msg = "Could not find episode data for {}".format(file_.name)
            logging.info(msg)
            continue

        # attach the episode_data file to the corresponding episode_data entry
        episode_data.file = file_

        new = show.formatter.display(episode_data) + file_.ext
        new = replace_invalid_path_chars(new)
        new = os.path.join(path, trim_long_filename(new))

        episode_data.file.new_name = new

        cleanFiles.append((file_.path, new))

    return cleanFiles


def rename(files, resp=""):
    """
    Performs the actual renaming of the files
    returns a tuple:
    (list of tuples with old info, list of file that cold not be renamed)
    """
    errors = []
    old_order = []

    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        logging.info("Changes were not committed to the files")
        return old_order, errors

    for old, new in files:
        if old == new:
            continue

        try:
            os.rename(old, new)
            old_order.append((new, old))
        except OSError:
            errors.append(old)

    return old_order, errors

#############################
## Undo rename functionality
#############################
## data format, save as json:
## { path_name_str_1: {
##      show_name: string,
##      num_files: int,
##      file_list: [ (new_name, old_name)]
##      },
##  path_name_str_2: {
##      show_name: string,
##      num_files: int,
##      file_list: [ (new_name, old_name)]
##      }, ...
## }
#############################


def save_renamed_file_info(old_order=None, show_title=None, path=None):
    """
    Save the previous names from the last renaming operation to disk
    """
    logging.info("Backing up old filenames")

    if not old_order:
        return

    if not path:
        path = os.path.split(old_order[0][0])[0]

    # If we have a title provided by the comand line, use that otherwise fall
    # fall back on the folder name (at least it's something)
    if show_title:
        name = show_title
    else:
        name = os.path.split(path)[1]

    fmt = dict(num_files=len(old_order), file_list=old_order, name=name)
    Settings.backup_list[path] = fmt

    with open_file_in_resources(Settings.rename_backup, 'w') as file_:
        json.dump(Settings.backup_list, file_)


def find_old_filenames(path, show_title=None):
    """
    Returns a list of tuples with the filenames
    """
    logging.info("Loading up old filenames")
    if 'backup_list' not in Settings:
        load_renamed_file()

    default = dict(name="", file_list=[], num_files=0)
    info = Settings.backup_list.get(path, default)

    if info['num_files'] > 0:
        return info['file_list']

    for info in Settings.backup_list:
        possible_info = Settings.backup_list.get(info, default)
        if possible_info['name'].lower() == show_title.lower():
            return possible_info['file_list']

    ## Couldn't be found in the json file
    return default['file_list']


def load_renamed_file():
    """
    Loads the json file of renamed shows into Settings.backup_list
    """
    logging.info("Loading the renamed episode json file")
    if not file_exists_in_resources(Settings.rename_backup):
        msg = "File [{}] with old name information was not be found, recreating"
        msg = msg.format(Settings.rename_backup)
        logging.warn(msg)
        create_new_backup_file()
        Settings.backup_list = {}
        return None

    with open_file_in_resources(Settings.rename_backup) as file_:
        try:
            Settings.backup_list = json.load(file_)
        except ValueError:
            logging.warning("The json file is empty")
            Settings.backup_list = {}


########################
## Text based functions
#######################

def parse_range(num_range):
    """
    Returns a list containing a range of numbers from the range passed
    """
    num_range = constants.num_range_regex.split(num_range)
    num_range = [int(val) for val in num_range if val.strip()]
    return range(min(num_range), max(num_range) + 1)


def trim_long_filename(name):
    """
    Trim a long filename on a windows platform to conform to 256 char limit
    """
    if len(name) > 255:
        ext = os.path.splitext(name)[1]
        logging.error('Truncating long filename: "{}" '.format(name))
        offset = 255 - len(ext)
        name = name[:offset] + ext
    return name

if sys.platform != 'win32':
    trim_long_filename = lambda name: name


def remove_punctuation(title):
    """
    Remove any punctuation and whitespace from the title
    """
    name, ext = os.path.splitext(title)
    exclude = set('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
    name = ''.join(ch for ch in name if ch not in exclude)
    return name + ext


def replace_invalid_path_chars(path, replacement='-'):
    """
    Replace invalid path character with a different, acceptable, character
    """
    exclude = set('\\/"?<>|*:-')
    path = ''.join(ch if ch not in exclude else replacement for ch in path)
    return path


def prepare_title(title):
    """
    Remove any punctuation and whitespace from the title
    """

    if not title:
        return ""

    title = remove_punctuation(title).split()

    if not title:
        return ""

    if title[0].lower() == 'the':
        title.remove(title[0])

    out = []
    for number in title:
        try:
            value = num_to_text(int(number))
            out.append(value)
        except (ValueError, KeyError):
            out.append(number)

    return ''.join(out)


def num_to_text(num):
    """
    Converts a number up to 999 to its English representation
    """
    # The purpose of this function is to resolve numbers to text so we don't
    # have additional entries in the database for the same show.  For example
    # The 12 kingdoms and twelve kingdoms will yield the same result in the DB

    if num < 20:
        return constants.num_dict[str(num)]

    args = []
    num = str(num)

    while num:
        digit = int(num[0])
        length = len(num)

        if length == 3:
            args.append(constants.num_dict[num[0]])
            args.append("hundred")
        else:
            value = str(digit * (10 ** (length - 1)))
            args.append(constants.num_dict[value])

        num = num[1:]

    return '_'.join(args)


def encode(text, encoding='utf-8'):
    """
    Returns a unicode representation of the string
    """
    if isinstance(text, basestring):
        if not isinstance(text, unicode):
            text = unicode(text, encoding, 'ignore')
    return text


###############################
##  Web Source Functionality
###############################

show_not_found = constants.show_not_found


def able_to_poll(site, delay=None, wait=False):
    """
    Prevents flooding by waiting two seconds from the last poll
    """
    if not delay:
        delay = Settings.poll_delay

    if not Settings.access_dict:
        Settings.access_dict = load_last_access_times()

    last_access = Settings.access_dict.get(site, -1)
    now = int(time.time())

    flooding = True

    if (last_access < 0) or (now - last_access >= delay):
        Settings.access_dict[site] = now
        flooding = False

    if flooding and wait:
        logging.warn('Possible flooding of "{}" detected"'.format(site))
        logging.warn("Waiting for {} second".format(delay))
        time.sleep(int(delay))
        flooding = False

    elif flooding:
        logging.warn('Possible flooding of "{}" detected'.format(site))

    return not flooding


def open_file_in_resources(name, mode='r'):
    """
    Returns a file object if the filename exists in the resources directory
    """
    name = os.path.split(name)[1]
    name = os.path.join(constants.resource_path, name)

    if mode in ('w', 'wb'):
        return open(name, mode)

    if file_exists_in_resources(name):
        return open(name, mode)

    raise OSError("File {} was not found".format(name))


def file_exists_in_resources(name):
    """
    Returns true if the filename exists in the resources directory
    """
    name = os.path.split(name)[1]
    name = os.path.join(constants.resource_path, name)
    return os.path.exists(name)


def save_last_access_times():
    """
    Save the last access times dictionary to a file in resources
    """
    if not Settings.access_dict:
        return False

    with open_file_in_resources(Settings.access_time_file, 'w') as file_:
        json.dump(Settings.access_dict, file_)

    return True


def load_last_access_times():
    """
    Load the access times dictionary from the file in resource path
    """
    if not file_exists_in_resources(Settings.access_time_file):
        return {}

    with open_file_in_resources(Settings.access_time_file) as file_:
        return json.load(file_)


#################
## Creation of default functions/files functionality
#################

def init_resource_folder():
    """
    Recreate the default resources folder and create some resources such as
    anidb database file
    """
    print("[+] Creating resource path")
    print("[+] Path = {}".format(constants.resource_path))
    os.makedirs(constants.resource_path, 0o755)
    print("[+] Updating the AniDb database file")
    update_db()
    print("[+] Creating a renamed file backup listing")
    create_new_backup_file()


def create_new_backup_file():
    """
    Create an empty backup file in the resources folder
    """
    logging.info("Creating a new rename info backup file")
    with open_file_in_resources(Settings.rename_backup, 'w') as file_:
        json.dump({}, file_)


def update_db():
    """
    Grab an updated version of the AniDb database, limited to once a day
    """
    logging.info("Attempting to update AniDb database file")
    one_unix_day = 24 * 60 * 60

    def _download():
        """
        perform the grabbing of the file
        """
        with open_file_in_resources(Settings.anidb_db_file, 'w') as file_:
            logging.info("Retrieving AniDB Database file")
            url = get_url_descriptor(Settings.anidb_db_url)
            file_.write(url.content.decode('utf-8'))

        logging.info("Successfully updated anidb_db_file")

    if not file_exists_in_resources(Settings.anidb_db_file):
        _download()
    elif able_to_poll('db_download', one_unix_day):
        _download()
    else:
        logging.error("Attempting to download the database file multiple times")
