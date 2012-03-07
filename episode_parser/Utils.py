# -*- coding: utf-8 -*-
__author__ = 'Dan Tracy'
__email__ = 'djt5019 at gmail dot com'

import os
import re
import time
import pickle
import requests
import requests.exceptions

import Constants
import Episode
import Exceptions

from tempfile import TemporaryFile

from Logger import get_logger
from Settings import Settings


def get_url_descriptor(url):
    """
    Returns an url descriptor or None on failure
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


def write_config(config, name):
    with open(os.path.join(Constants.RESOURCE_PATH, name), 'w') as f:
        f.write(config)


##############################
## Renaming utility functions
##############################

def extract_file_info(episode_filename):
    result = regex_search(episode_filename)
    info_dict = {}

    if not result or 'junk' in result:
        get_logger().info("Could not find file information for: {}".format(episode_filename))
        return info_dict

    get_logger().debug(result)

    if 'special' in result:
        info_dict['special_number'] = int(result['special'])
        info_dict['special_type'] = result.get('type', 'OVA')
    else:
        info_dict['episode_number'] = int(result['episode'])
        info_dict['season'] = int(result.get('season', -1))

    checksum = result.get('sum', '0')

    info_dict['checksum'] = int(checksum, base=16)

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


def regex_search(filename):
    """
    Compare the filename to each of the regular expressions for a match
    """

    # deal with anything in brackets ourselves, they tend to throw off the regexes
    checksum = Constants.checksum_regex.search(filename)
    filename = Constants.checksum_regex.sub("", filename)
    season = Constants.bracket_season_regex.search(filename)

    filename = Constants.remove_junk_regex.sub("", filename)

    for count, regex in enumerate(Constants.regexList):
        result = regex.search(filename)
        if result:
            get_logger().info("Regex #{} matched {}".format(count, filename))
            break

    result = result.groupdict()
    if checksum:
        result['sum'] = checksum.group('sum')

    if season:
        result['season'] = season.group('season')
        result['episode'] = season.group('episode')

    return result


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
        get_logger().info("No files were able to be renamed")
        return

    for f in files:
        if f.is_ova:
            episode = show.get_special(f.special_number)
        elif f.episode_number > show.maxEpisodeNumber:
            episode = show.get_special(f.episode_number - show.maxEpisodeNumber)
        else:
            episode = show.get_episode(f.season, f.episode_number)

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

        newName = os.path.join(path, newName)
        if len(newName) > 256:
            get_logger().error('The filename "{}" may be too long to rename, truncating'.format(newName))
            offset = 255 - len(f.ext)
            newName = newName[:offset] + f.ext

        cleanFiles.append((f.path, newName))

    if sameCount > 0:
        msg = "1 file" if sameCount == 1 else "{} files".format(sameCount)
        get_logger().warning(
            "{} in this directory would have been renamed to the same filename".format(msg))

    return cleanFiles


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


###############################
##  Web Source Functionality
###############################

show_not_found = Constants.SHOW_NOT_FOUND


def able_to_poll(site, delay=None):
    """
    Prevents flooding by waiting two seconds from the last poll
    """
    if not delay:
        delay = Settings['poll_delay']

    if not Settings['access_dict']:
        Settings['access_dict'] = load_last_access_times()

    last_access = Settings['access_dict'].get(site, -1)
    now = int(time.time())

    if last_access < 0:
        Settings['access_dict'][site] = now
        return True

    if now - last_access >= int(delay):
        Settings['access_dict'][site] = now
        return True

    return False


def open_file_in_resources(name, mode='r'):
    """
    Returns a file object if the filename exists in the resources directory
    """
    name = os.path.split(name)[1]
    name = os.path.join(Constants.RESOURCE_PATH, name)

    if mode in ('w', 'wb'):
        return open(name, mode)

    if file_exists_in_resources(name):
        return open(name, mode)

    raise Exceptions.API_FileNotFoundException()


def file_exists_in_resources(name):
    """
    Returns true if the filename exists in the resources directory
    """
    name = os.path.split(name)[1]
    name = os.path.join(Constants.RESOURCE_PATH, name)
    return os.path.exists(name)


def regex_compile(regex):
    """
    Returns a compiled regex instance, ignore case and verbose are activated by default
    """
    return re.compile(regex, re.I | re.X)


def regex_sub(pattern, replacement, target):
    """
    Substitutes the replacement in the target if it matches the pattern
    """
    return re.sub(pattern, replacement, target)


def temporary_file(suffix):
    """
    Returns a file object to a temporary file
    """
    return TemporaryFile(suffix=suffix)


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
