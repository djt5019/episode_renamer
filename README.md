Episode Renamer v0.1
====================

This utility allows you to easily rename your messy episode files.  It will allow
you to easily rename your files with custom formatting, generate checksums, and
verify file integrity.  Extracts information by making use of the AniDB api,
TheTvDb api, and by scraping epguides.

Options
-------
* -h/--help             Display the help message and exit the program
* -d/--display-header   Display some descriptive information about the show
* -v/--verbose          Enables extra output to see whats going on
* -s/--season           Filters the episodes that are in the season range passed
* -e/--episodes         Filters the episodes that are in the range range passed
* -f/--format           Uses the format string passed to present the show titles
* -g/--gui-enabled      Uses a PySide gui rather than a CLI, currently unstable
* -r/--rename           Attempts to rename the episodes in the directory passed
* -u/--undo-rename      Will attempt to undo the last renaming operation in the current directory
* --delete-cache        Destroys and then recreates the episode database
* --update-db           Downloads an updated listing from AniDB
* --verify              Will try to verify the integrity of the episodes by checking the crc32 sum (if present)
* --filter              Filters the episodes show by type (episodes, specials, or both)

Usage
-----

    eplist "Cheers" --season 3 --episode 2
    performs a search for the show "Cheers", then returns the second episode from the third season

    eplist pwd --season 1 --rename .
    uses the current folders name to search for the show, the attempts to rename the episodes from the first season

    eplist "Cheers" -r . --format "<series:proper> - <type> <episode:pad> - <title> [<hash>]"
    renames the episodes in the current directory using show information from cheers using a custom format

Formatting
----------
This program allows you to use custom formatting to rename your episode files.
The tags can be changed by editing the dictionary in the Settings.py file.

-   episode_name_tags: Will replace the tag with the episodes name
-   episode_number_tags: Replaces the tag with the episodes number in the season
-   episode_count_tags: Replaces the tag with the episodes total overall number in the series
-   series_name_tags: Replaces the tag with the series name
-   season_number_tags: Replaces the tag with the episodes season
-   hash_tags: If you are renaming files it will replace the tag with the checksum (if it was not previously present in the filename then it will compute it)
-   type_tags: Replaces the tag with the episodes type, eg. Episode, DVD, OVA, etc


in addition to the formatting, this program allows you to modify the results of the tags with some
basic text modifiers.  You modify the tag by using <tagname:mod1:mod2:...:modN>

-   pad: If the output is an integer it will automatically pad zeros
-   upper: Capitalize the resulting string
-   lower: Convert the string to lower case
-   proper: Converts the string to a representation with proper capitalization.
