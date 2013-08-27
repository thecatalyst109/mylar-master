#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import os, sys, subprocess

import threading
import webbrowser
import sqlite3
import itertools
import csv
import shutil

from lib.apscheduler.scheduler import Scheduler
from lib.configobj import ConfigObj

import cherrypy

from mylar import versioncheck, logger, version

FULL_PATH = None
PROG_DIR = None

ARGS = None
SIGNAL = None

SYS_ENCODING = None

VERBOSE = 1
DAEMON = False
PIDFILE= None

SCHED = Scheduler()

INIT_LOCK = threading.Lock()
__INITIALIZED__ = False
started = False

DATA_DIR = None

CONFIG_FILE = None
CFG = None
CONFIG_VERSION = None

DB_FILE = None

LOG_DIR = None
LOG_LIST = []

CACHE_DIR = None
SYNO_FIX = False

PULLNEW = None

HTTP_PORT = None
HTTP_HOST = None
HTTP_USERNAME = None
HTTP_PASSWORD = None
HTTP_ROOT = None
LAUNCH_BROWSER = False
LOGVERBOSE = 1
GIT_PATH = None
INSTALL_TYPE = None
CURRENT_VERSION = None
LATEST_VERSION = None
COMMITS_BEHIND = None
USER_AGENT = None
SEARCH_DELAY = 1

CHECK_GITHUB = False
CHECK_GITHUB_ON_STARTUP = False
CHECK_GITHUB_INTERVAL = None

DESTINATION_DIR = None
CHMOD_DIR = None
CHMOD_FILE = None
USENET_RETENTION = None

ADD_COMICS = False
COMIC_DIR = None
LIBRARYSCAN = False
IMP_MOVE = False
IMP_RENAME = False
IMP_METADATA = False

SEARCH_INTERVAL = 360
NZB_STARTUP_SEARCH = False
LIBRARYSCAN_INTERVAL = 300
DOWNLOAD_SCAN_INTERVAL = 5
INTERFACE = None

PREFERRED_QUALITY = None
PREFERRED_CBR = None
PREFERRED_CBZ = None
PREFERRED_WE = None
CORRECT_METADATA = False
MOVE_FILES = False
RENAME_FILES = False
BLACKHOLE = False
BLACKHOLE_DIR = None
FOLDER_FORMAT = None
FILE_FORMAT = None
REPLACE_SPACES = False
REPLACE_CHAR = None
ZERO_LEVEL = False
ZERO_LEVEL_N = None
LOWERCASE_FILENAME = False
USE_MINSIZE = False
MINSIZE = 10
USE_MAXSIZE = False
MAXSIZE = 60
AUTOWANT_UPCOMING = True
AUTOWANT_ALL = False
COMIC_COVER_LOCAL = False
ADD_TO_CSV = True
PROWL_ENABLED = False
PROWL_PRIORITY = 1
PROWL_KEYS = None
PROWL_ONSNATCH = False
NMA_ENABLED = False
NMA_APIKEY = None
NMA_PRIORITY = None
NMA_ONSNATCH = None
PUSHOVER_ENABLED = False
PUSHOVER_PRIORITY = 1
PUSHOVER_APIKEY = None
PUSHOVER_USERKEY = None
PUSHOVER_ONSNATCH = False
SKIPPED2WANTED = False
CVINFO = False
LOG_LEVEL = None
POST_PROCESSING = 1

USE_SABNZBD = True
SAB_HOST = None
SAB_USERNAME = None
SAB_PASSWORD = None
SAB_APIKEY = None
SAB_CATEGORY = None
SAB_PRIORITY = None
SAB_DIRECTORY = None

USE_NZBGET = False
NZBGET_HOST = None
NZBGET_PORT = None
NZBGET_USERNAME = None
NZBGET_PASSWORD = None
NZBGET_PRIORITY = None
NZBGET_CATEGORY = None

NZBSU = False
NZBSU_APIKEY = None

DOGNZB = False
DOGNZB_APIKEY = None

NZBX = False

NEWZNAB = False
NEWZNAB_HOST = None
NEWZNAB_APIKEY = None
NEWZNAB_ENABLED = False
EXTRA_NEWZNABS = []
NEWZNAB_EXTRA = None

RAW = False
RAW_PROVIDER = None
RAW_USERNAME = None
RAW_PASSWORD = None
RAW_GROUPS = None

EXPERIMENTAL = False

COMIC_LOCATION = None
QUAL_ALTVERS = None
QUAL_SCANNER = None
QUAL_TYPE = None
QUAL_QUALITY = None

ENABLE_EXTRA_SCRIPTS = 1
EXTRA_SCRIPTS = None

ENABLE_PRE_SCRIPTS = 1
PRE_SCRIPTS = None

COUNT_COMICS = 0
COUNT_ISSUES = 0
COUNT_HAVES = 0

COMICSORT = None
ANNUALS_ON = 0
CV_ONLY = 1
CV_ONETIMER = 1
GRABBAG_DIR = None
HIGHCOUNT = 0
READ2FILENAME = 0
STORYARCDIR = 0
CVAPIFIX = 0
CVURL = None
WEEKFOLDER = 0
LOCMOVE = 0
NEWCOM_DIR = None
FFTONEWCOM_DIR = 0
OLDCONFIG_VERSION = None

def CheckSection(sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        CFG[sec] = {}
        return False

################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):
    try:
        my_val = config[cfg_name][item_name]
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    if log:
        logger.debug(item_name + " -> " + my_val)
    else:
        logger.debug(item_name + " -> ******")
    return my_val
    

def initialize():

    with INIT_LOCK:
    
        global __INITIALIZED__, FULL_PATH, PROG_DIR, VERBOSE, DAEMON, COMICSORT, DATA_DIR, CONFIG_FILE, CFG, CONFIG_VERSION, LOG_DIR, CACHE_DIR, LOGVERBOSE, OLDCONFIG_VERSION, \
                HTTP_PORT, HTTP_HOST, HTTP_USERNAME, HTTP_PASSWORD, HTTP_ROOT, LAUNCH_BROWSER, GIT_PATH, \
                CURRENT_VERSION, LATEST_VERSION, CHECK_GITHUB, CHECK_GITHUB_ON_STARTUP, CHECK_GITHUB_INTERVAL, USER_AGENT, DESTINATION_DIR, \
                DOWNLOAD_DIR, USENET_RETENTION, SEARCH_INTERVAL, NZB_STARTUP_SEARCH, INTERFACE, AUTOWANT_ALL, AUTOWANT_UPCOMING, ZERO_LEVEL, ZERO_LEVEL_N, COMIC_COVER_LOCAL, HIGHCOUNT, \
                LIBRARYSCAN, LIBRARYSCAN_INTERVAL, DOWNLOAD_SCAN_INTERVAL, USE_SABNZBD, SAB_HOST, SAB_USERNAME, SAB_PASSWORD, SAB_APIKEY, SAB_CATEGORY, SAB_PRIORITY, SAB_DIRECTORY, BLACKHOLE, BLACKHOLE_DIR, ADD_COMICS, COMIC_DIR, IMP_MOVE, IMP_RENAME, IMP_METADATA, \
                USE_NZBGET, NZBGET_HOST, NZBGET_PORT, NZBGET_USERNAME, NZBGET_PASSWORD, NZBGET_CATEGORY, NZBGET_PRIORITY, NZBSU, NZBSU_APIKEY, DOGNZB, DOGNZB_APIKEY, NZBX,\
                NEWZNAB, NEWZNAB_HOST, NEWZNAB_APIKEY, NEWZNAB_ENABLED, EXTRA_NEWZNABS, NEWZNAB_EXTRA, \
                RAW, RAW_PROVIDER, RAW_USERNAME, RAW_PASSWORD, RAW_GROUPS, EXPERIMENTAL, \
                PROWL_ENABLED, PROWL_PRIORITY, PROWL_KEYS, PROWL_ONSNATCH, NMA_ENABLED, NMA_APIKEY, NMA_PRIORITY, NMA_ONSNATCH, PUSHOVER_ENABLED, PUSHOVER_PRIORITY, PUSHOVER_APIKEY, PUSHOVER_USERKEY, PUSHOVER_ONSNATCH, LOCMOVE, NEWCOM_DIR, FFTONEWCOM_DIR, \
                PREFERRED_QUALITY, MOVE_FILES, RENAME_FILES, LOWERCASE_FILENAMES, USE_MINSIZE, MINSIZE, USE_MAXSIZE, MAXSIZE, CORRECT_METADATA, FOLDER_FORMAT, FILE_FORMAT, REPLACE_CHAR, REPLACE_SPACES, ADD_TO_CSV, CVINFO, LOG_LEVEL, POST_PROCESSING, SEARCH_DELAY, GRABBAG_DIR, READ2FILENAME, STORYARCDIR, CVURL, CVAPIFIX, \
                COMIC_LOCATION, QUAL_ALTVERS, QUAL_SCANNER, QUAL_TYPE, QUAL_QUALITY, ENABLE_EXTRA_SCRIPTS, EXTRA_SCRIPTS, ENABLE_PRE_SCRIPTS, PRE_SCRIPTS, PULLNEW, COUNT_ISSUES, COUNT_HAVES, COUNT_COMICS, SYNO_FIX, CHMOD_FILE, CHMOD_DIR, ANNUALS_ON, CV_ONLY, CV_ONETIMER, WEEKFOLDER
                
        if __INITIALIZED__:
            return False

        # Make sure all the config sections exist
        CheckSection('General')
        CheckSection('SABnzbd')
        CheckSection('NZBGet')
        CheckSection('NZBsu')
        CheckSection('DOGnzb')
        CheckSection('Raw')
        CheckSection('Experimental')        
        CheckSection('Newznab')
        # Set global variables based on config file or use defaults
        try:
            HTTP_PORT = check_setting_int(CFG, 'General', 'http_port', 8090)
        except:
            HTTP_PORT = 8090
            
        if HTTP_PORT < 21 or HTTP_PORT > 65535:
            HTTP_PORT = 8090
            
        CONFIG_VERSION = check_setting_str(CFG, 'General', 'config_version', '')
        HTTP_HOST = check_setting_str(CFG, 'General', 'http_host', '0.0.0.0')
        HTTP_USERNAME = check_setting_str(CFG, 'General', 'http_username', '')
        HTTP_PASSWORD = check_setting_str(CFG, 'General', 'http_password', '')
        HTTP_ROOT = check_setting_str(CFG, 'General', 'http_root', '/')
        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'General', 'launch_browser', 1))
        LOGVERBOSE = bool(check_setting_int(CFG, 'General', 'logverbose', 1))
        GIT_PATH = check_setting_str(CFG, 'General', 'git_path', '')
        LOG_DIR = check_setting_str(CFG, 'General', 'log_dir', '')
        if not CACHE_DIR:
            CACHE_DIR = check_setting_str(CFG, 'General', 'cache_dir', '')
        
        CHECK_GITHUB = bool(check_setting_int(CFG, 'General', 'check_github', 1))
        CHECK_GITHUB_ON_STARTUP = bool(check_setting_int(CFG, 'General', 'check_github_on_startup', 1))
        CHECK_GITHUB_INTERVAL = check_setting_int(CFG, 'General', 'check_github_interval', 360)
        
        DESTINATION_DIR = check_setting_str(CFG, 'General', 'destination_dir', '')
        CHMOD_DIR = check_setting_str(CFG, 'General', 'chmod_dir', '0777')
        CHMOD_FILE = check_setting_str(CFG, 'General', 'chmod_file', '0660')
        USENET_RETENTION = check_setting_int(CFG, 'General', 'usenet_retention', '1500')
        
        SEARCH_INTERVAL = check_setting_int(CFG, 'General', 'search_interval', 360)
        NZB_STARTUP_SEARCH = bool(check_setting_int(CFG, 'General', 'nzb_startup_search', 0))
        LIBRARYSCAN = bool(check_setting_int(CFG, 'General', 'libraryscan', 1))
        LIBRARYSCAN_INTERVAL = check_setting_int(CFG, 'General', 'libraryscan_interval', 300)
        ADD_COMICS = bool(check_setting_int(CFG, 'General', 'add_comics', 0))
        COMIC_DIR = check_setting_str(CFG, 'General', 'comic_dir', '')
        IMP_MOVE = bool(check_setting_int(CFG, 'General', 'imp_move', 0))
        IMP_RENAME = bool(check_setting_int(CFG, 'General', 'imp_rename', 0))
        IMP_METADATA = bool(check_setting_int(CFG, 'General', 'imp_metadata', 0))
        DOWNLOAD_SCAN_INTERVAL = check_setting_int(CFG, 'General', 'download_scan_interval', 5)
        INTERFACE = check_setting_str(CFG, 'General', 'interface', 'default')
        AUTOWANT_ALL = bool(check_setting_int(CFG, 'General', 'autowant_all', 0))
        AUTOWANT_UPCOMING = bool(check_setting_int(CFG, 'General', 'autowant_upcoming', 1))
        COMIC_COVER_LOCAL = bool(check_setting_int(CFG, 'General', 'comic_cover_local', 0))
        PREFERRED_QUALITY = bool(check_setting_int(CFG, 'General', 'preferred_quality', 0))
        CORRECT_METADATA = bool(check_setting_int(CFG, 'General', 'correct_metadata', 0))
        MOVE_FILES = bool(check_setting_int(CFG, 'General', 'move_files', 0))
        RENAME_FILES = bool(check_setting_int(CFG, 'General', 'rename_files', 0))
        FOLDER_FORMAT = check_setting_str(CFG, 'General', 'folder_format', '$Series ($Year)')
        FILE_FORMAT = check_setting_str(CFG, 'General', 'file_format', '$Series $Issue ($Year)')
        BLACKHOLE = bool(check_setting_int(CFG, 'General', 'blackhole', 0))
        BLACKHOLE_DIR = check_setting_str(CFG, 'General', 'blackhole_dir', '')
        REPLACE_SPACES = bool(check_setting_int(CFG, 'General', 'replace_spaces', 0))
        REPLACE_CHAR = check_setting_str(CFG, 'General', 'replace_char', '')
        ZERO_LEVEL = bool(check_setting_int(CFG, 'General', 'zero_level', 0))
        ZERO_LEVEL_N = check_setting_str(CFG, 'General', 'zero_level_n', '')
        LOWERCASE_FILENAMES = bool(check_setting_int(CFG, 'General', 'lowercase_filenames', 0))
        SYNO_FIX = bool(check_setting_int(CFG, 'General', 'syno_fix', 0))
        SEARCH_DELAY = check_setting_int(CFG, 'General', 'search_delay', 1)
        GRABBAG_DIR = check_setting_str(CFG, 'General', 'grabbag_dir', '')
        if not GRABBAG_DIR:
            #default to ComicLocation
            GRABBAG_DIR = DESTINATION_DIR
        WEEKFOLDER = bool(check_setting_int(CFG, 'General', 'weekfolder', 0))
        CVAPIFIX = bool(check_setting_int(CFG, 'General', 'cvapifix', 0))
        if CVAPIFIX is None:
            CVAPIFIX = 0
        LOCMOVE = bool(check_setting_int(CFG, 'General', 'locmove', 0))
        if LOCMOVE is None:
            LOCMOVE = 0
        NEWCOM_DIR = check_setting_str(CFG, 'General', 'newcom_dir', '')
        FFTONEWCOM_DIR = bool(check_setting_int(CFG, 'General', 'fftonewcom_dir', 0))
        if FFTONEWCOM_DIR is None:
            FFTONEWCOM_DIR = 0
        HIGHCOUNT = check_setting_str(CFG, 'General', 'highcount', '')
        if not HIGHCOUNT: HIGHCOUNT = 0
        READ2FILENAME = bool(check_setting_int(CFG, 'General', 'read2filename', 0))
        STORYARCDIR = bool(check_setting_int(CFG, 'General', 'storyarcdir', 0))
        PROWL_ENABLED = bool(check_setting_int(CFG, 'Prowl', 'prowl_enabled', 0))
        PROWL_KEYS = check_setting_str(CFG, 'Prowl', 'prowl_keys', '')
        PROWL_ONSNATCH = bool(check_setting_int(CFG, 'Prowl', 'prowl_onsnatch', 0))
        PROWL_PRIORITY = check_setting_int(CFG, 'Prowl', 'prowl_priority', 0)

        NMA_ENABLED = bool(check_setting_int(CFG, 'NMA', 'nma_enabled', 0))
        NMA_APIKEY = check_setting_str(CFG, 'NMA', 'nma_apikey', '')
        NMA_PRIORITY = check_setting_int(CFG, 'NMA', 'nma_priority', 0)
        NMA_ONSNATCH = bool(check_setting_int(CFG, 'NMA', 'nma_onsnatch', 0))

        PUSHOVER_ENABLED = bool(check_setting_int(CFG, 'PUSHOVER', 'pushover_enabled', 0))
        PUSHOVER_APIKEY = check_setting_str(CFG, 'PUSHOVER', 'pushover_apikey', '')
        PUSHOVER_USERKEY = check_setting_str(CFG, 'PUSHOVER', 'pushover_userkey', '')
        PUSHOVER_PRIORITY = check_setting_int(CFG, 'PUSHOVER', 'pushover_priority', 0)
        PUSHOVER_ONSNATCH = bool(check_setting_int(CFG, 'PUSHOVER', 'pushover_onsnatch', 0))

        USE_MINSIZE = bool(check_setting_int(CFG, 'General', 'use_minsize', 0))
        MINSIZE = check_setting_str(CFG, 'General', 'minsize', '')
        USE_MAXSIZE = bool(check_setting_int(CFG, 'General', 'use_maxsize', 0))
        MAXSIZE = check_setting_str(CFG, 'General', 'maxsize', '')
        ADD_TO_CSV = bool(check_setting_int(CFG, 'General', 'add_to_csv', 1))
        CVINFO = bool(check_setting_int(CFG, 'General', 'cvinfo', 0))
        ANNUALS_ON = bool(check_setting_int(CFG, 'General', 'annuals_on', 0))
        if not ANNUALS_ON:
            #default to on
            ANNUALS_ON = 0
        CV_ONLY = bool(check_setting_int(CFG, 'General', 'cv_only', 1))
        if not CV_ONLY:
            #default to on
            CV_ONLY = 1
        CV_ONETIMER = bool(check_setting_int(CFG, 'General', 'cv_onetimer', 1))
        if not CV_ONETIMER:
            CV_ONETIMER = 1
        LOG_LEVEL = check_setting_str(CFG, 'General', 'log_level', '')
        ENABLE_EXTRA_SCRIPTS = bool(check_setting_int(CFG, 'General', 'enable_extra_scripts', 0))
        EXTRA_SCRIPTS = check_setting_str(CFG, 'General', 'extra_scripts', '')

        ENABLE_PRE_SCRIPTS = bool(check_setting_int(CFG, 'General', 'enable_pre_scripts', 0))
        PRE_SCRIPTS = check_setting_str(CFG, 'General', 'pre_scripts', '')
        POST_PROCESSING = bool(check_setting_int(CFG, 'General', 'post_processing', 1))

        USE_SABNZBD = bool(check_setting_int(CFG, 'SABnzbd', 'use_sabnzbd', 0))
        SAB_HOST = check_setting_str(CFG, 'SABnzbd', 'sab_host', '')
        SAB_USERNAME = check_setting_str(CFG, 'SABnzbd', 'sab_username', '')
        SAB_PASSWORD = check_setting_str(CFG, 'SABnzbd', 'sab_password', '')
        SAB_APIKEY = check_setting_str(CFG, 'SABnzbd', 'sab_apikey', '')
        SAB_CATEGORY = check_setting_str(CFG, 'SABnzbd', 'sab_category', '')
        SAB_DIRECTORY = check_setting_str(CFG, 'SABnzbd', 'sab_directory', '')
        SAB_PRIORITY = check_setting_str(CFG, 'SABnzbd', 'sab_priority', '')
        if SAB_PRIORITY.isdigit():
            if SAB_PRIORITY == "0": SAB_PRIORITY = "Default"
            elif SAB_PRIORITY == "1": SAB_PRIORITY = "Low"
            elif SAB_PRIORITY == "2": SAB_PRIORITY = "Normal"
            elif SAB_PRIORITY == "3": SAB_PRIORITY = "High"
            elif SAB_PRIORITY == "4": SAB_PRIORITY = "Paused"
            else: SAB_PRIORITY = "Default"

        USE_NZBGET = bool(check_setting_int(CFG, 'NZBGet', 'use_nzbget', 0))
        NZBGET_HOST = check_setting_str(CFG, 'NZBGet', 'nzbget_host', '')
        NZBGET_PORT = check_setting_str(CFG, 'NZBGet', 'nzbget_port', '')
        NZBGET_USERNAME = check_setting_str(CFG, 'NZBGet', 'nzbget_username', '')
        NZBGET_PASSWORD = check_setting_str(CFG, 'NZBGet', 'nzbget_password', '')
        NZBGET_CATEGORY = check_setting_str(CFG, 'NZBGet', 'nzbget_category', '')
        NZBGET_PRIORITY = check_setting_str(CFG, 'NZBGet', 'nzbget_priority', '')

        NZBSU = bool(check_setting_int(CFG, 'NZBsu', 'nzbsu', 0))
        NZBSU_APIKEY = check_setting_str(CFG, 'NZBsu', 'nzbsu_apikey', '')

        DOGNZB = bool(check_setting_int(CFG, 'DOGnzb', 'dognzb', 0))
        DOGNZB_APIKEY = check_setting_str(CFG, 'DOGnzb', 'dognzb_apikey', '')

        NZBX = bool(check_setting_int(CFG, 'nzbx', 'nzbx', 0))

        RAW = bool(check_setting_int(CFG, 'Raw', 'raw', 0))
        RAW_PROVIDER = check_setting_str(CFG, 'Raw', 'raw_provider', '')
        RAW_USERNAME = check_setting_str(CFG, 'Raw', 'raw_username', '')
        RAW_PASSWORD  = check_setting_str(CFG, 'Raw', 'raw_password', '')
        RAW_GROUPS = check_setting_str(CFG, 'Raw', 'raw_groups', '')

        EXPERIMENTAL = bool(check_setting_int(CFG, 'Experimental', 'experimental', 0))

        NEWZNAB = bool(check_setting_int(CFG, 'Newznab', 'newznab', 0))

        if CONFIG_VERSION:
            NEWZNAB_HOST = check_setting_str(CFG, 'Newznab', 'newznab_host', '')
            NEWZNAB_APIKEY = check_setting_str(CFG, 'Newznab', 'newznab_apikey', '')
            NEWZNAB_ENABLED = bool(check_setting_int(CFG, 'Newznab', 'newznab_enabled', 1))

        # Need to pack the extra newznabs back into a list of tuples
        flattened_newznabs = check_setting_str(CFG, 'Newznab', 'extra_newznabs', [], log=False)
        EXTRA_NEWZNABS = list(itertools.izip(*[itertools.islice(flattened_newznabs, i, None, 3) for i in range(3)]))

        #to counteract the loss of the 1st newznab entry because of a switch, let's rewrite to the tuple
        if NEWZNAB_HOST and CONFIG_VERSION:
            EXTRA_NEWZNABS.append((NEWZNAB_HOST, NEWZNAB_APIKEY, int(NEWZNAB_ENABLED)))
            # Need to rewrite config here and bump up config version
            CONFIG_VERSION = '3'
            config_write()        
         
        # update folder formats in the config & bump up config version
        if CONFIG_VERSION == '0':
            from mylar.helpers import replace_all
            file_values = { 'issue':  'Issue', 'title': 'Title', 'series' : 'Series', 'year' : 'Year' }
            folder_values = { 'series' : 'Series', 'publisher':'Publisher', 'year' : 'Year', 'first' : 'First', 'lowerfirst' : 'first' }
            FILE_FORMAT = replace_all(FILE_FORMAT, file_values)
            FOLDER_FORMAT = replace_all(FOLDER_FORMAT, folder_values)
            
            CONFIG_VERSION = '1'
            
        if CONFIG_VERSION == '1':

            from mylar.helpers import replace_all

            file_values = { 'Issue':        '$Issue',
                            'Title':        '$Title',
                            'Series':       '$Series',
                            'Year':         '$Year',
                            'title':        '$title',
                            'series':       '$series',
                            'year':         '$year'
                            }
            folder_values = {   'Series':       '$Series',
                                'Publisher':    '$Publisher',
                                'Year':         '$Year',
                                'First':        '$First',
                                'series':       '$series',
                                'publisher':    '$publisher',
                                'year':         '$year',
                                'first':        '$first'
                            }   
            FILE_FORMAT = replace_all(FILE_FORMAT, file_values)
            FOLDER_FORMAT = replace_all(FOLDER_FORMAT, folder_values)
            
            CONFIG_VERSION = '2'

        if 'http://' not in SAB_HOST[:7] and 'https://' not in SAB_HOST[:8]:
            SAB_HOST = 'http://' + SAB_HOST
            #print ("SAB_HOST:" + SAB_HOST)

        if not LOG_DIR:
            LOG_DIR = os.path.join(DATA_DIR, 'logs')

        if not os.path.exists(LOG_DIR):
            try:
                os.makedirs(LOG_DIR)
            except OSError:
                if VERBOSE:
                    print 'Unable to create the log directory. Logging to screen only.'

        # Start the logger, silence console logging if we need to
        logger.mylar_log.initLogger(verbose=VERBOSE)

        # Put the cache dir in the data dir for now
        if not CACHE_DIR:
            CACHE_DIR = os.path.join(str(DATA_DIR), 'cache')
        #logger.info("cache set to : " + str(CACHE_DIR))
        if not os.path.exists(CACHE_DIR):
            try:
               os.makedirs(CACHE_DIR)
            except OSError:
                logger.error('Could not create cache dir. Check permissions of datadir: ' + DATA_DIR)

        # Sanity check for search interval. Set it to at least 6 hours
        if SEARCH_INTERVAL < 360:
            logger.info("Search interval too low. Resetting to 6 hour minimum")
            SEARCH_INTERVAL = 360


        # Initialize the database
        logger.info('Checking to see if the database has all tables....')
        try:
            dbcheck()
        except Exception, e:
            logger.error("Can't connect to the database: %s" % e)

        # With the addition of NZBGet, it's possible that both SAB and NZBget are unchecked initially.
        # let's force default SAB.
        if USE_NZBGET == 0 and USE_SABNZBD == 0 :
            logger.info("No Download Server option given - defaulting to SABnzbd.")
            USE_SABNZBD = 1

        # Get the currently installed version - returns None, 'win32' or the git hash
        # Also sets INSTALL_TYPE variable to 'win', 'git' or 'source'
        CURRENT_VERSION = versioncheck.getVersion()
        if CURRENT_VERSION is not None:
            hash = CURRENT_VERSION[:7]
        else:
            hash = "unknown"

        if version.MYLAR_VERSION == 'master':
            vers = 'M'
        else:
           vers = 'D'

        USER_AGENT = 'Mylar/'+str(hash)+'('+vers+') +http://www.github.com/evilhero/mylar/'

        # Check for new versions
        if CHECK_GITHUB_ON_STARTUP:
            try:
                LATEST_VERSION = versioncheck.checkGithub()
            except:
                LATEST_VERSION = CURRENT_VERSION
        else:
            LATEST_VERSION = CURRENT_VERSION

        #check for syno_fix here
        if SYNO_FIX:
            parsepath = os.path.join(DATA_DIR, 'bs4', 'builder', '_lxml.py')
            if os.path.isfile(parsepath):
                print ("found bs4...renaming appropriate file.")
                src = os.path.join(parsepath)
                dst = os.path.join(DATA_DIR, 'bs4', 'builder', 'lxml.py')
                try:
                    shutil.move(src, dst)
                except (OSError, IOError):
                    logger.error("Unable to rename file...shutdown Mylar and go to " + src.encode('utf-8') + " and rename the _lxml.py file to lxml.py")
                    logger.error("NOT doing this will result in errors when adding / refreshing a series")
            else:
                logger.info("Synology Parsing Fix already implemented. No changes required at this time.")

        #CV sometimes points to the incorrect DNS - here's the fix.
        if CVAPIFIX == 1:
            CVURL = 'http://beta.comicvine.com/api/'
            logger.info("CVAPIFIX enabled: ComicVine set to beta API site")
        else:
            CVURL = 'http://api.comicvine.com/'
            logger.info("CVAPIFIX disabled: Comicvine set to normal API site")

        if LOCMOVE:
            helpers.updateComicLocation()

        #Ordering comics here
        logger.info("Remapping the sorting to allow for new additions.")
        COMICSORT = helpers.ComicSort(sequence='startup')
                                    
        __INITIALIZED__ = True
        return True

def daemonize():

    if threading.activeCount() != 1:
        logger.warn('There are %r active threads. Daemonizing may cause \
                        strange behavior.' % threading.enumerate())
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Do first fork
    try:
        pid = os.fork()
        if pid == 0:
            pass
        else:
            # Exit the parent process
            logger.debug('Forking once...')
            os._exit(0)
    except OSError, e:
        sys.exit("1st fork failed: %s [%d]" % (e.strerror, e.errno))
        
    os.setsid()

    # Do second fork
    try:
        pid = os.fork()
        if pid > 0:
            logger.debug('Forking twice...')
            os._exit(0) # Exit second parent process
    except OSError, e:
        sys.exit("2nd fork failed: %s [%d]" % (e.strerror, e.errno))

    os.chdir("/")
    os.umask(0)
    
    si = open('/dev/null', "r")
    so = open('/dev/null', "a+")
    se = open('/dev/null', "a+")
    
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    pid = os.getpid()
    logger.info('Daemonized to PID: %s' % pid)
    if PIDFILE:
        logger.info('Writing PID %s to %s' % (pid, PIDFILE))
        file(PIDFILE, 'w').write("%s\n" % pid)

def launch_browser(host, port, root):

    if host == '0.0.0.0':
        host = 'localhost'
    
    try:    
        webbrowser.open('http://%s:%i%s' % (host, port, root))
    except Exception, e:
        logger.error('Could not launch browser: %s' % e)

def config_write():
    new_config = ConfigObj()
    new_config.filename = CONFIG_FILE
    new_config['General'] = {}
    new_config['General']['config_version'] = CONFIG_VERSION
    new_config['General']['http_port'] = HTTP_PORT
    new_config['General']['http_host'] = HTTP_HOST
    new_config['General']['http_username'] = HTTP_USERNAME
    new_config['General']['http_password'] = HTTP_PASSWORD
    new_config['General']['http_root'] = HTTP_ROOT
    new_config['General']['launch_browser'] = int(LAUNCH_BROWSER)
    new_config['General']['log_dir'] = LOG_DIR
    new_config['General']['logverbose'] = int(LOGVERBOSE)
    new_config['General']['git_path'] = GIT_PATH
    new_config['General']['cache_dir'] = CACHE_DIR
    new_config['General']['annuals_on'] = int(ANNUALS_ON)
    new_config['General']['cv_only'] = int(CV_ONLY)
    new_config['General']['cv_onetimer'] = int(CV_ONETIMER)
    new_config['General']['cvapifix'] = int(CVAPIFIX)    
    new_config['General']['check_github'] = int(CHECK_GITHUB)
    new_config['General']['check_github_on_startup'] = int(CHECK_GITHUB_ON_STARTUP)
    new_config['General']['check_github_interval'] = CHECK_GITHUB_INTERVAL

    new_config['General']['destination_dir'] = DESTINATION_DIR
    new_config['General']['chmod_dir'] = CHMOD_DIR
    new_config['General']['chmod_file'] = CHMOD_FILE
    new_config['General']['usenet_retention'] = USENET_RETENTION

    new_config['General']['search_interval'] = SEARCH_INTERVAL
    new_config['General']['nzb_startup_search'] = int(NZB_STARTUP_SEARCH)
    new_config['General']['libraryscan'] = int(LIBRARYSCAN)
    new_config['General']['libraryscan_interval'] = LIBRARYSCAN_INTERVAL
    new_config['General']['add_comics'] = int(ADD_COMICS)
    new_config['General']['comic_dir'] = COMIC_DIR
    new_config['General']['imp_move'] = int(IMP_MOVE)
    new_config['General']['imp_rename'] = int(IMP_RENAME)
    new_config['General']['imp_metadata'] = int(IMP_METADATA)
    new_config['General']['download_scan_interval'] = DOWNLOAD_SCAN_INTERVAL
    new_config['General']['interface'] = INTERFACE
    new_config['General']['autowant_all'] = int(AUTOWANT_ALL)
    new_config['General']['autowant_upcoming'] = int(AUTOWANT_UPCOMING)
    new_config['General']['preferred_quality'] = int(PREFERRED_QUALITY)
    new_config['General']['comic_cover_local'] = int(COMIC_COVER_LOCAL)
    new_config['General']['correct_metadata'] = int(CORRECT_METADATA)
    new_config['General']['move_files'] = int(MOVE_FILES)
    new_config['General']['rename_files'] = int(RENAME_FILES)
    new_config['General']['folder_format'] = FOLDER_FORMAT
    new_config['General']['file_format'] = FILE_FORMAT
    new_config['General']['blackhole'] = int(BLACKHOLE)
    new_config['General']['blackhole_dir'] = BLACKHOLE_DIR
    new_config['General']['replace_spaces'] = int(REPLACE_SPACES)
    new_config['General']['replace_char'] = REPLACE_CHAR
    new_config['General']['zero_level'] = int(ZERO_LEVEL)
    new_config['General']['zero_level_n'] = ZERO_LEVEL_N
    new_config['General']['lowercase_filenames'] = int(LOWERCASE_FILENAMES)
    new_config['General']['syno_fix'] = int(SYNO_FIX)
    new_config['General']['search_delay'] = SEARCH_DELAY
    new_config['General']['grabbag_dir'] = GRABBAG_DIR
    new_config['General']['highcount'] = HIGHCOUNT
    new_config['General']['read2filename'] = int(READ2FILENAME)
    new_config['General']['storyarcdir'] = int(STORYARCDIR)
    new_config['General']['use_minsize'] = int(USE_MINSIZE)
    new_config['General']['minsize'] = MINSIZE
    new_config['General']['use_maxsize'] = int(USE_MAXSIZE)
    new_config['General']['maxsize'] = MAXSIZE
    new_config['General']['add_to_csv'] = int(ADD_TO_CSV)
    new_config['General']['cvinfo'] = int(CVINFO)
    new_config['General']['log_level'] = LOG_LEVEL
    new_config['General']['enable_extra_scripts'] = int(ENABLE_EXTRA_SCRIPTS)
    new_config['General']['extra_scripts'] = EXTRA_SCRIPTS
    new_config['General']['enable_pre_scripts'] = int(ENABLE_PRE_SCRIPTS)
    new_config['General']['pre_scripts'] = PRE_SCRIPTS
    new_config['General']['post_processing'] = int(POST_PROCESSING)
    new_config['General']['weekfolder'] = int(WEEKFOLDER)
    new_config['General']['locmove'] = int(LOCMOVE)
    new_config['General']['newcom_dir'] = NEWCOM_DIR
    new_config['General']['fftonewcom_dir'] = int(FFTONEWCOM_DIR)

    new_config['SABnzbd'] = {}
    new_config['SABnzbd']['use_sabnzbd'] = int(USE_SABNZBD)
    new_config['SABnzbd']['sab_host'] = SAB_HOST
    new_config['SABnzbd']['sab_username'] = SAB_USERNAME
    new_config['SABnzbd']['sab_password'] = SAB_PASSWORD
    new_config['SABnzbd']['sab_apikey'] = SAB_APIKEY
    new_config['SABnzbd']['sab_category'] = SAB_CATEGORY
    new_config['SABnzbd']['sab_priority'] = SAB_PRIORITY
    new_config['SABnzbd']['sab_directory'] = SAB_DIRECTORY

    new_config['NZBGet'] = {}
    new_config['NZBGet']['use_nzbget'] = int(USE_NZBGET)
    new_config['NZBGet']['nzbget_host'] = NZBGET_HOST
    new_config['NZBGet']['nzbget_port'] = NZBGET_PORT
    new_config['NZBGet']['nzbget_username'] = NZBGET_USERNAME
    new_config['NZBGet']['nzbget_password'] = NZBGET_PASSWORD
    new_config['NZBGet']['nzbget_category'] = NZBGET_CATEGORY
    new_config['NZBGet']['nzbget_priority'] = NZBGET_PRIORITY


    new_config['NZBsu'] = {}
    new_config['NZBsu']['nzbsu'] = int(NZBSU)
    new_config['NZBsu']['nzbsu_apikey'] = NZBSU_APIKEY

    new_config['DOGnzb'] = {}
    new_config['DOGnzb']['dognzb'] = int(DOGNZB)
    new_config['DOGnzb']['dognzb_apikey'] = DOGNZB_APIKEY

    new_config['nzbx'] = {}
    new_config['nzbx']['nzbx'] = int(NZBX)

    new_config['Experimental'] = {}
    new_config['Experimental']['experimental'] = int(EXPERIMENTAL)

    new_config['Newznab'] = {}
    new_config['Newznab']['newznab'] = int(NEWZNAB)

    # Need to unpack the extra newznabs for saving in config.ini
    flattened_newznabs = []
    for newznab in EXTRA_NEWZNABS:
        for item in newznab:
            flattened_newznabs.append(item)

    new_config['Newznab']['extra_newznabs'] = flattened_newznabs

    new_config['Prowl'] = {}
    new_config['Prowl']['prowl_enabled'] = int(PROWL_ENABLED)
    new_config['Prowl']['prowl_keys'] = PROWL_KEYS
    new_config['Prowl']['prowl_onsnatch'] = int(PROWL_ONSNATCH)
    new_config['Prowl']['prowl_priority'] = int(PROWL_PRIORITY)

    new_config['NMA'] = {}
    new_config['NMA']['nma_enabled'] = int(NMA_ENABLED)
    new_config['NMA']['nma_apikey'] = NMA_APIKEY
    new_config['NMA']['nma_priority'] = NMA_PRIORITY
    new_config['NMA']['nma_onsnatch'] = int(NMA_ONSNATCH)

    new_config['PUSHOVER'] = {}
    new_config['PUSHOVER']['pushover_enabled'] = int(PUSHOVER_ENABLED)
    new_config['PUSHOVER']['pushover_apikey'] = PUSHOVER_APIKEY
    new_config['PUSHOVER']['pushover_userkey'] = PUSHOVER_USERKEY
    new_config['PUSHOVER']['pushover_priority'] = PUSHOVER_PRIORITY
    new_config['PUSHOVER']['pushover_onsnatch'] = int(PUSHOVER_ONSNATCH)

    new_config['Raw'] = {}
    new_config['Raw']['raw'] = int(RAW)
    new_config['Raw']['raw_provider'] = RAW_PROVIDER
    new_config['Raw']['raw_username'] = RAW_USERNAME
    new_config['Raw']['raw_password'] = RAW_PASSWORD
    new_config['Raw']['raw_groups'] = RAW_GROUPS

    new_config.write()
    
def start():
    
    global __INITIALIZED__, started
    
    if __INITIALIZED__:
    
        # Start our scheduled background tasks
        #from mylar import updater, searcher, librarysync, postprocessor

        from mylar import updater, search, weeklypull

        SCHED.add_interval_job(updater.dbUpdate, hours=48)
        SCHED.add_interval_job(search.searchforissue, minutes=SEARCH_INTERVAL)
        #SCHED.add_interval_job(librarysync.libraryScan, minutes=LIBRARYSCAN_INTERVAL)

        #weekly pull list gets messed up if it's not populated first, so let's populate it then set the scheduler.
        logger.info("Checking for existance of Weekly Comic listing...")
        PULLNEW = 'no'  #reset the indicator here.
        threading.Thread(target=weeklypull.pullit).start()
        #now the scheduler (check every 24 hours)
        SCHED.add_interval_job(weeklypull.pullit, hours=24)
        
        #let's do a run at the Wanted issues here (on startup) if enabled.
        if NZB_STARTUP_SEARCH:
            threading.Thread(target=search.searchforissue).start()

        if CHECK_GITHUB:
            SCHED.add_interval_job(versioncheck.checkGithub, minutes=CHECK_GITHUB_INTERVAL)
        
        #SCHED.add_interval_job(postprocessor.checkFolder, minutes=DOWNLOAD_SCAN_INTERVAL)

        SCHED.start()
        
        started = True
    
def dbcheck():

    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS comics (ComicID TEXT UNIQUE, ComicName TEXT, ComicSortName TEXT, ComicYear TEXT, DateAdded TEXT, Status TEXT, IncludeExtras INTEGER, Have INTEGER, Total INTEGER, ComicImage TEXT, ComicPublisher TEXT, ComicLocation TEXT, ComicPublished TEXT, LatestIssue TEXT, LatestDate TEXT, Description TEXT, QUALalt_vers TEXT, QUALtype TEXT, QUALscanner TEXT, QUALquality TEXT, LastUpdated TEXT, AlternateSearch TEXT, UseFuzzy TEXT, ComicVersion TEXT, SortOrder INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS issues (IssueID TEXT, ComicName TEXT, IssueName TEXT, Issue_Number TEXT, DateAdded TEXT, Status TEXT, Type TEXT, ComicID, ArtworkURL Text, ReleaseDate TEXT, Location TEXT, IssueDate TEXT, Int_IssueNumber INT, ComicSize TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS snatched (IssueID TEXT, ComicName TEXT, Issue_Number TEXT, Size INTEGER, DateAdded TEXT, Status TEXT, FolderName TEXT, ComicID TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS upcoming (ComicName TEXT, IssueNumber TEXT, ComicID TEXT, IssueID TEXT, IssueDate TEXT, Status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS nzblog (IssueID TEXT, NZBName TEXT, SARC TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS weekly (SHIPDATE text, PUBLISHER text, ISSUE text, COMIC VARCHAR(150), EXTRA text, STATUS text)')
#    c.execute('CREATE TABLE IF NOT EXISTS sablog (nzo_id TEXT, ComicName TEXT, ComicYEAR TEXT, ComicIssue TEXT, name TEXT, nzo_complete TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS importresults (impID TEXT, ComicName TEXT, ComicYear TEXT, Status TEXT, ImportDate TEXT, ComicFilename TEXT, ComicLocation TEXT, WatchMatch TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS readlist (IssueID TEXT, ComicName TEXT, Issue_Number TEXT, Status TEXT, DateAdded TEXT, Location TEXT, inCacheDir TEXT, SeriesYear TEXT, ComicID TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS annuals (IssueID TEXT, Issue_Number TEXT, IssueName TEXT, IssueDate TEXT, Status TEXT, ComicID TEXT, GCDComicID TEXT)')
    conn.commit
    c.close
    #new

    csv_load()

    
    #add in the late players to the game....
    try:
        c.execute('SELECT LastUpdated from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN LastUpdated TEXT')

    try:
        c.execute('SELECT QUALalt_vers from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN QUALalt_vers TEXT')
    try:
        c.execute('SELECT QUALtype from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN QUALtype TEXT')
    try:
        c.execute('SELECT QUALscanner from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN QUALscanner TEXT')
    try:
        c.execute('SELECT QUALquality from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN QUALquality TEXT')

    try:
        c.execute('SELECT AlternateSearch from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN AlternateSearch TEXT')

    try:
        c.execute('SELECT ComicVersion from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN ComicVersion TEXT')

    try:
        c.execute('SELECT SortOrder from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN SortOrder INTEGER')

    try:
        c.execute('SELECT ComicSize from issues')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE issues ADD COLUMN ComicSize TEXT')

    try:
        c.execute('SELECT UseFuzzy from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN UseFuzzy TEXT')

    try:
        c.execute('SELECT WatchMatch from importresults')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE importresults ADD COLUMN WatchMatch TEXT')

    try:
        c.execute('SELECT IssueCount from importresults')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE importresults ADD COLUMN IssueCount TEXT')

    try:
        c.execute('SELECT ComicLocation from importresults')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE importresults ADD COLUMN ComicLocation TEXT')

    try:
        c.execute('SELECT ComicFilename from importresults')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE importresults ADD COLUMN ComicFilename TEXT')

    try:
        c.execute('SELECT impID from importresults')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE importresults ADD COLUMN impID TEXT')

    try:
        c.execute('SELECT inCacheDir from issues')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE issues ADD COLUMN inCacheDIR TEXT')

    try:
        c.execute('SELECT inCacheDIR from readlist')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE readlist ADD COLUMN inCacheDIR TEXT')

    try:
        c.execute('SELECT Location from readlist')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE readlist ADD COLUMN Location TEXT')

    try:
        c.execute('SELECT IssueDate from readlist')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE readlist ADD COLUMN IssueDate TEXT')

    try:
        c.execute('SELECT SeriesYear from readlist')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE readlist ADD COLUMN SeriesYear TEXT')

    try:
        c.execute('SELECT ComicID from readlist')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE readlist ADD COLUMN ComicID TEXT')

    try:
        c.execute('SELECT DetailURL from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN DetailURL TEXT')

    try:
        c.execute('SELECT ComicID from weekly')
    except:
        c.execute('ALTER TABLE weekly ADD COLUMN ComicID TEXT')

    try:
        c.execute('SELECT implog from importresults')
    except:
        c.execute('ALTER TABLE importresults ADD COLUMN implog TEXT')

    try:
        c.execute('SELECT SARC from nzblog')
    except:
        c.execute('ALTER TABLE nzblog ADD COLUMN SARC TEXT')


    #if it's prior to Wednesday, the issue counts will be inflated by one as the online db's everywhere
    #prepare for the next 'new' release of a series. It's caught in updater.py, so let's just store the 
    #value in the sql so we can display it in the details screen for everyone to wonder at.
    try:
        c.execute('SELECT not_updated_db from comics')
    except sqlite3.OperationalError:
        c.execute('ALTER TABLE comics ADD COLUMN not_updated_db TEXT')

# -- not implemented just yet ;)

    # for metadata...
    # MetaData_Present will be true/false if metadata is present
    # MetaData will hold the MetaData itself in tuple format
#    try:
#        c.execute('SELECT MetaData_Present from comics')
#    except sqlite3.OperationalError:
#        c.execute('ALTER TABLE importresults ADD COLUMN MetaData_Present TEXT')

#    try:
#        c.execute('SELECT MetaData from importresults')
#    except sqlite3.OperationalError:
#        c.execute('ALTER TABLE importresults ADD COLUMN MetaData TEXT')

    #let's delete errant comics that are stranded (ie. Comicname = Comic ID: )
    c.execute("DELETE from COMICS WHERE ComicName='None' OR ComicName LIKE 'Comic ID%' OR ComicName is NULL")
    logger.info(u"Ensuring DB integrity - Removing all Erroneous Comics (ie. named None)")

    logger.info(u"Correcting Null entries that make the main page break on startup.")
    c.execute("UPDATE Comics SET LatestDate='Unknown' WHERE LatestDate='None' or LatestDate is NULL")
        

    conn.commit()
    c.close()

def csv_load():
    # for redudant module calls..include this.
    conn=sqlite3.connect(DB_FILE)
    c=conn.cursor()

    c.execute('DROP TABLE IF EXISTS exceptions')

    c.execute('CREATE TABLE IF NOT EXISTS exceptions (variloop TEXT, ComicID TEXT, NewComicID TEXT, GComicID TEXT)')

    # for Mylar-based Exception Updates....
    i = 0
    EXCEPTIONS = []
    EXCEPTIONS.append('exceptions.csv')
    EXCEPTIONS.append('custom_exceptions.csv')

    while (i <= 1):
    #EXCEPTIONS_FILE = os.path.join(DATA_DIR, 'exceptions.csv')
        EXCEPTIONS_FILE = os.path.join(DATA_DIR, EXCEPTIONS[i])

        if not os.path.exists(EXCEPTIONS_FILE):
            try:
                csvfile = open(str(EXCEPTIONS_FILE), "rb")
            except (OSError,IOError):
                if i == 1:
                    logger.info("No Custom Exceptions found - Using base exceptions only. Creating blank custom_exceptions for your personal use.")
                    try:
                        shutil.copy(os.path.join(DATA_DIR,"custom_exceptions_sample.csv"), EXCEPTIONS_FILE)
                    except (OSError,IOError):
                        logger.error("Cannot create custom_exceptions.csv in " + str(DATA_DIR) + ". Make sure _sample.csv is present and/or check permissions.")
                        return  
                else:
                    logger.error("Could not locate " + str(EXCEPTIONS[i]) + " file. Make sure it's in datadir: " + DATA_DIR)
                break
        else:
            csvfile = open(str(EXCEPTIONS_FILE), "rb")
        if i == 0:
            logger.info(u"Populating Base Exception listings into Mylar....")
        elif i == 1:
            logger.info(u"Populating Custom Exception listings into Mylar....")

        creader = csv.reader(csvfile, delimiter=',')

        for row in creader:
            try:
                c.execute("INSERT INTO exceptions VALUES (?,?,?,?);", row)
            except Exception, e:
                #print ("Error - invald arguments...-skipping")
                pass
                pass
        csvfile.close()
        i+=1

    conn.commit()
    c.close()    

def shutdown(restart=False, update=False):

    cherrypy.engine.exit()
    SCHED.shutdown(wait=False)
    
    config_write()

    if not restart and not update:
        logger.info('Mylar is shutting down...')
    if update:
        logger.info('Mylar is updating...')
        try:
            versioncheck.update()
        except Exception, e:
            logger.warn('Mylar failed to update: %s. Restarting.' % e) 

    if PIDFILE :
        logger.info ('Removing pidfile %s' % PIDFILE)
        os.remove(PIDFILE)
        
    if restart:
        logger.info('Mylar is restarting...')
        popen_list = [sys.executable, FULL_PATH]
        popen_list += ARGS
        if '--nolaunch' not in popen_list:
            popen_list += ['--nolaunch']
        logger.info('Restarting Mylar with ' + str(popen_list))
        subprocess.Popen(popen_list, cwd=os.getcwd())
        
    os._exit(0)
