# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import re
import pickle
import requests
import requests.exceptions

import Constants
import Episode

from Logger import get_logger
from Settings import Settings


def get_URL_descriptor(url):
    """
    Returns an url descriptor or None
    """
    try:
        resp = requests.get(url)
    except requests.exceptions.ConnectionError:
        get_logger().error("Error connecting to {}".format(url))
        return None

    if resp.ok:
        return resp

    return None


def is_valid_file(filename):
    """
    Returns true if the filename is a valid video file
    """
    ext = os.path.splitext(filename)[1].lower()

    return os.path.isfile(filename) and ext in Constants.VIDEO_EXTENSIONS


##############################
## Renaming utility functions
##############################

def extract_file_info(episode_filename):
    result = regex_search(episode_filename)
    info_dict = {}

    if not result or 'junk' in result.groupdict():
        get_logger().info("Could not find file information for: {}".format(episode_filename))
        return info_dict

    res_dict = result.groupdict()
    get_logger().debug(res_dict)

    if 'special' in result.groupdict():
        info_dict['special_number'] = int(res_dict['special'])
        info_dict['special_type'] = res_dict.get('type', 'OVA')
    else:
        info_dict['episode_number'] = int(res_dict['episode'])
        info_dict['season'] = int(res_dict.get('season', -1))

    info_dict['checksum'] = int(res_dict.get('sum', '0'), base=16)

    return info_dict


def clean_filenames(path):
    """
    Attempts to extract order information about the files passed
    returns: list of EpisodeFiles
    """
    # Filter out anything that doesnt have the correct extension and
    # filter out any directories
    files = os.listdir(path)
    files = filter(lambda x: is_valid_file(os.path.join(path, x)), files)

    if not files:
        get_logger().error("No video files were found in {}".format(path))
        return []

    _compile_regexs()
    cleanFiles = []
    # We are going to store the episode number and path in a tuple then sort on the
    # episodes number.  Special episodes will be appended to the end of the clean list
    for f in files:
        info = extract_file_info(f)

        if not info:
            continue

        cleanFiles.append(Episode.EpisodeFile(os.path.join(path, f), **info))

    if not cleanFiles:
        get_logger().error("The files could not be matched")
        return cleanFiles

    get_logger().info("Successfully cleaned the file names")

    return cleanFiles


def _compile_regexs():
    """
    This function will only compile the regexs once.
    """
    if not Constants.regexList:
        for r in Constants.REGEX:
            Constants.regexList.append(re.compile(r, re.I))
    return Constants.regexList


def regex_search(filename):
    """
    Compare the filename to each of the regular expressions for a match
    """
    for count, regex in enumerate(_compile_regexs()):
        result = regex.search(filename)
        if result:
            get_logger().info("Regex #{} matched {}".format(count, filename))
            return result

    return None


def prepare_filenames(path, show):
    """
    Rename the files located in 'path' to those in the list 'show'
    """
    path = os.path.abspath(path)
    sameCount = 0

    files = clean_filenames(path)
    #Match the list of EpisodeFiles to the list of shows in the 'show' variable
    if not files:
        get_logger().info("No files were able to be renamed")
        return

    for f in files:

        if f.is_ova:
            episode = show.get_special(f.special_number)
        else:
            episode = show.get_episode(f.season, f.episode_number)

        if f.episode_number > show.maxEpisodeNumber:
            episode = show.get_special(f.episode_number - show.maxEpisodeNumber)

        if not episode:
            get_logger().warning("Could not find an episode for {}".format(f.name))
            continue

        episode.episode_file = f

        fileName = encode(f.name)
        newName = replace_invalid_path_chars(show.formatter.display(episode) + f.ext)

        if newName == fileName:
            get_logger().info("File {} and Episode {} have same name".format(f.name, episode.title))
            sameCount += 1
            continue

        episode.episode_file.new_name = newName

        name = os.path.join(path, newName)
        if len(name) > 256:
            get_logger().error('The filename "{}" may be too long to rename, truncating'.format(newName))
            offset = 255 - len(f.ext)
            name = name[:offset] + f.ext

    if sameCount > 0:
        msg = "1 file" if sameCount == 1 else "{} files".format(sameCount)
        get_logger().warning(
            "{} in this directory would have been renamed to the same filename".format(msg))


def rename(files, resp=""):
    """
    Performs the actual renaming of the files, returns a list of file that weren't able to be renamed
    """
    errors = []
    if resp == '':
        resp = raw_input("\nDo you wish to rename these files [y|N]: ").lower()

    if not resp.startswith('y'):
        get_logger().info("Changes were not committed to the files")
        return errors

    old_order = []

    for old, new in files:
        try:
            os.rename(old, new)
            old_order.append((new, old))
        except Exception as e:
            errors.append((old, e))

    save_renamed_file_info(old_order)

    if errors:
        for e in errors:
            get_logger().error("File {} could not be renamed: {}".format(os.path.split(e[0])[1], e[1]))
    else:
        get_logger().info("Files were successfully renamed")

    return errors


def save_last_access_times():
    """
    Save the last access times dictionary to a file in resources
    """
    if not Settings['access_dict']:
        return False

    with open(os.path.join(Constants.RESOURCE_PATH, Settings['access_time_file']), 'w') as p:
        pickle.dump(Settings['access_dict'], p)

    return True


def load_last_access_times():
    """
    Load the access times dictionary from the file in resource path
    """
    name = os.path.join(Constants.RESOURCE_PATH, Settings['access_time_file'])
    if os.path.exists(name):
        with open(name, 'r') as p:
            data = p.readlines()

        return pickle.loads(''.join(data))
    else:
        return {}


def save_renamed_file_info(old_order):
    """
    Save the previous names from the last renaming operation to disk
    """
    get_logger().info("Backing up old filenames")
    with open(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup']), 'w') as f:
        pickle.dump(old_order, f)


def load_last_renamed_files():
    """
    Restore the previous names from the last renaming operation
    """
    get_logger().info("Loading up old filenames")
    if not os.path.exists(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup'])):
        get_logger().warn("There seems to be no files to be un-renamed")
        return []

    with open(os.path.join(Constants.RESOURCE_PATH, Settings['rename_backup'])) as f:
        data = f.readlines()

    # Data will be in the form of a list of tuples
    # [ (new1, old1), ..., (newN, oldN) ]
    return pickle.loads(''.join(data))


########################
## Text based functions
#######################


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


def prepare_title(title):
    """
    Remove any punctuation and whitespace from the title
    """
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
        return Constants.NUM_DICT[str(num)]

    args = []
    num = str(num)

    while num:
        digit = int(num[0])
        length = len(num)

        if length == 3:
            args.append(Constants.NUM_DICT[num[0]])
            args.append("hundred")
        else:
            value = str(digit * (10 ** (length - 1)))
            args.append(Constants.NUM_DICT[value])

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
