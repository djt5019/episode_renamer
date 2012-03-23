
# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import sys
import time
import json
import logging

import constants
import episode

from settings import Settings

import requests
import requests.exceptions


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

    return os.path.isfile(filename) and ext in constants.VIDEO_EXTENSIONS


##############################
## Renaming utility functions
##############################
def regex_search(filename):
    """
    Compare the filename to each of the regular expressions for a match
    """
    logging.info("Matching '{}'".format(filename))
    # deal with anything in brackets ourselves, they tend to throw off the regexes
    checksum = constants.checksum_regex.search(filename)
    filename = constants.checksum_regex.sub("", filename)
    season = constants.bracket_season_regex.search(filename)

    filename = constants.remove_junk_regex.sub("", filename)

    result = None
    for count, regex in enumerate(constants.regexList):
        result = regex.search(filename)
        if result:
            logging.info("Regex #{} matched {}".format(count, filename.encode(Settings['encoding'], 'ignore')))
            break

    if not result and not season:
        msg = "Unable to find information on: {}".format(filename)
        logging.error(msg)
        raise Exception(msg)

    # Work with the result dict rather than the annoying groupdicts
    result = result.groupdict() if result else {}
    result.update(**checksum.groupdict() if checksum else {})
    result.update(**season.groupdict() if season else {})

    logging.info(result)

    # Info dict will hold the proper data for our episode or special
    info_dict = {}
    if 'junk' in result:
        return info_dict

    info_dict['checksum'] = int(result.get('sum', '0x0'), base=16)

    if 'special' in result:
        info_dict['special_number'] = int(result['special'])
        info_dict['special_type'] = result.get('type', 'OVA')
    else:
        info_dict['episode_number'] = int(result['episode'])
        info_dict['season'] = int(result.get('season', '1'))

    return info_dict


def clean_filenames(path):
    """
    Attempts to extract order information about the files passed
    returns: list of EpisodeFiles
    """
    # Filter out anything that doesnt have the correct extension and
    # filter out any directories
    files = []
    for f in os.listdir(path):
        if is_valid_file(os.path.join(path, f)):
            files.append(f)
        else:
            logging.info("Invalid file: {}".format(f))

    if not files:
        logging.error("No video files were found in {}".format(path))
        return []

    cleanFiles = []
    # We are going to store the episode number and path in a tuple then sort on the
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        info = regex_search(f)

        if info:
            cleanFiles.append(episode.EpisodeFile(os.path.join(path, f), **info))

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
    sameCount = 0
    cleanFiles = []
    files = clean_filenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable
    if not files:
        logging.info("No files were able to be renamed")
        return

    for f in files:
        if f.is_ova:
            episode = show.get_special(f.special_number)
        elif f.episode_number > show.max_episode_number:
            episode = show.get_special(f.episode_number - show.max_episode_number)
        else:
            episode = show.get_episode(f.episode_number, f.season)

        if not episode:
            logging.warning("Could not find an episode for {}".format(f.name))
            continue

        # attach the episode file to the corresponding episode entry
        episode.episode_file = f

        fileName = encode(f.name)
        newName = replace_invalid_path_chars(show.formatter.display(episode) + f.ext)

        if newName == fileName:
            logging.info("File {} and Episode {} have same name".format(f.name, episode.title))
            sameCount += 1
            continue

        newName = os.path.join(path, trim_long_filename(newName))

        episode.episode_file.new_name = newName
        cleanFiles.append((f.path, newName))

    if sameCount > 0:
        msg = "1 file" if sameCount == 1 else "{} files".format(sameCount)
        logging.warning(
            "{} in this directory would have been renamed to the same filename".format(msg))

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
        try:
            os.rename(old, new)
            old_order.append((new, old))
        except OSError as e:
            errors.append((old, e))

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


def save_renamed_file_info(old_order, show_title=None):
    """
    Save the previous names from the last renaming operation to disk
    """
    logging.info("Backing up old filenames")

    if not old_order:
        return

    path = os.path.split(old_order[0][0])[0]

    # If we have a title provided by the comand line, use that otherwise fall
    # fall back on the folder name (at least it's something)
    if show_title:
        name = show_title
    else:
        name = os.path.split(path)[1]

    fmt = dict(num_files=len(old_order), file_list=old_order, name=name)
    Settings['backup_list'][path] = fmt

    with open_file_in_resources(Settings['rename_backup'], 'w') as f:
        json.dump(Settings['backup_list'], f)


def find_old_filenames(path, show_title=None):
    """
    Returns a dict with the filenames and the number of files
    """
    logging.info("Loading up old filenames")
    if 'backup_list' not in Settings:
        load_renamed_file()

    if not show_title:
        return Settings['backup_list'].get(path, dict(name="", file_list=[], num_files=0))

    try:
        return Settings['backup_list']['path']
    except KeyError:
        for d in Settings['backup_list']:
            info = Settings['backup_list'][d]
            if info['name'] == show_title:
                return info

    return {}


def load_renamed_file():
    """
    Loads the json file of renamed shows into Settings['backup_list']
    """
    logging.info("Loading the renamed episode json file")
    if not file_exists_in_resources(Settings['rename_backup']):
        logging.warn("Json file [{}] with old information could not be found".format(Settings['rename_backup']))
        Settings['backup_list'] = {}
    else:
        with open_file_in_resources(Settings['rename_backup']) as f:
            try:
                Settings['backup_list'] = json.load(f)
            except ValueError:
                logging.warning("The json file is empty")
                Settings['backup_list'] = {}


########################
## Text based functions
#######################

def trim_long_filename(name):
    if len(name) > 255:
        ext = os.path.splitext(name)[1]
        logging.error('The filename "{}" may be too long to rename, truncating'.format(name))
        offset = 255 - len(ext)
        name = name[:offset] + ext
    return name


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
    exclude = set('\\/"?<>|*:')
    path = ''.join(ch if ch not in exclude else replacement for ch in path)
    return path


if sys.platform != 'win32':
    trim_long_filename = lambda name: name


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
    for n in title:
        try:
            value = num_to_text(int(n))
            out.append(value)
        except Exception:
            out.append(n)

    return ''.join(out)


def num_to_text(num):
    """
    Converts a number up to 999 to it's English representation
    """
    # The purpose of this function is to resolve numbers to text so we don't
    # have additional entries in the database for the same show.  For example
    # The 12 kingdoms and twelve kingdoms will yield the same result in the DB

    if num < 20:
        return constants.NUM_DICT[str(num)]

    args = []
    num = str(num)

    while num:
        digit = int(num[0])
        length = len(num)

        if length == 3:
            args.append(constants.NUM_DICT[num[0]])
            args.append("hundred")
        else:
            value = str(digit * (10 ** (length - 1)))
            args.append(constants.NUM_DICT[value])

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

show_not_found = constants.SHOW_NOT_FOUND


def able_to_poll(site, delay=None, wait=False):
    """
    Prevents flooding by waiting two seconds from the last poll
    """
    if not delay:
        delay = Settings['poll_delay']

    if not Settings['access_dict']:
        Settings['access_dict'] = load_last_access_times()

    last_access = Settings['access_dict'].get(site, -1)
    now = int(time.time())

    flooding = True

    if (last_access < 0) or (now - last_access >= delay):
        Settings['access_dict'][site] = now
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
    name = os.path.join(constants.RESOURCE_PATH, name)

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
    name = os.path.join(constants.RESOURCE_PATH, name)
    return os.path.exists(name)


def save_last_access_times():
    """
    Save the last access times dictionary to a file in resources
    """
    if not Settings['access_dict']:
        return False

    with open_file_in_resources(Settings['access_time_file'], 'w') as p:
        json.dump(Settings['access_dict'], p)

    return True


def load_last_access_times():
    """
    Load the access times dictionary from the file in resource path
    """
    if not file_exists_in_resources(Settings['access_time_file']):
        return {}

    with open_file_in_resources(Settings['access_time_file']) as f:
        return json.load(f)


#################
## Creation of default functions/files functionality
#################

def init_resource_folder():
    print "[+] Creating resource path"
    print "[+] Path = {}".format(constants.RESOURCE_PATH)
    os.makedirs(constants.RESOURCE_PATH, 0755)
    print "[+] Updating the AniDb database file"
    update_db()
    print "[+] Creating a renamed file backup listing"
    create_new_backup_file()


def create_new_backup_file():
    logging.info("Creating a new rename info backup file")
    with open_file_in_resources(Settings['rename_backup'], 'w') as f:
        json.dump({}, f)


def update_db():
    logging.info("Attempting to update AniDb database file")
    one_unix_day = 24 * 60 * 60

    def _download():
        with open_file_in_resources(Settings['anidb_db_file'], 'w') as f:
            logging.info("Retrieving AniDB Database file")
            url = get_url_descriptor(Settings['anidb_db_url'])

            f.write(url.content)
        logging.info("Successfully updated anidb_db_file")

    if not file_exists_in_resources(Settings['anidb_db_file']):
        _download()
    elif able_to_poll('db_download', one_unix_day):
        _download()
    else:
        logging.error("Attempting to download the database file multiple times")
