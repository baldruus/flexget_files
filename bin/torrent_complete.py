#!/usr/bin/python -O
import sys
import os
import logging, logging.handlers
from subprocess import call

LOG_FILE='/home/bsmith/.flexget/bin/torrent_complete.log'
DOWNLOAD_PATH='/home/bsmith/Downloads/completed'
STAGING_PATH='/home/bsmith/Downloads/staging/'
# If you're using a local checkout of Flexget, use flexget_vanilla.
# Otherwise use the one in your system
FLEXGET_COMMAND='flexget --logfile /home/bsmith/.flexget/flexget-sorting.log'
FLEXGET_SORTING_CONFIG='/home/bsmith/.flexget/sort.yml'
FLEXGET_TASK_PREFIX='Sort_Unpacked_'

XBMC_LIST = ["192.168.1.4","192.168.1.15","192.168.1.20","openelec","192.168.1.8","dsgburg-cgq63q1"]

FLEXGET_PATH_TASK={
    '/Movies/': 'Movies',
    '/TvShows/': 'TV_Shows',
    }

log = logging.getLogger("torrent_complete")
log.setLevel(logging.DEBUG)
logformat = logging.Formatter("%(levelname)s\t%(asctime)s\t%(message)s")

logfile = logging.FileHandler(LOG_FILE)
logfile.setFormatter(logformat)
logfile.setLevel(logging.INFO)
log.addHandler(logfile)

# Log to stdout and increase logging level if run from a console
if os.isatty(sys.stdin.fileno()):
    ch = logging.StreamHandler()
    ch.setFormatter(logformat)
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)
    FLEXGET_COMMAND += ' --debug'

if len(sys.argv) != 4:
    log.error('%s called with %d arguments, it requires 3.' % (sys.argv[0],(len(sys.argv)-1)))
    log.error('%s' % (sys.argv[2]))
    sys.exit(-1)

torrent_id=sys.argv[1]
torrent_name=sys.argv[2]
torrent_path=sys.argv[3]

log.debug("%s called with torrent_id='%s', torrent_name='%s', torrent_path='%s'." % (sys.argv[0],
    torrent_id, torrent_name, torrent_path))

def chain():
    log.debug("Updating XBMC Library")
    for xbmc in XBMC_LIST:
        ret=call('/usr/bin/xbmc-send --host='+xbmc+' --action="XBMC.updatelibrary(video)"', shell=True)
    sys.exit(0)

if DOWNLOAD_PATH not in torrent_path:
    log.debug("Torrent '%s' path (%s) not in %s, skipping unrar" % (torrent_name,torrent_path,DOWNLOAD_PATH))
    chain()


for path, task in FLEXGET_PATH_TASK.items():
    if DOWNLOAD_PATH+path in torrent_path:
        log.info('Processing %s as part of task %s.' % (torrent_name,task))
        for root, dirs, files in os.walk(torrent_path+'/'+torrent_name, topdown=False):
            cmd='find "'+root+'" -type f -regex ".*\.\(\part[0-9]+\.\)?r\([0-9]+\|ar\)$" | head -1 | xargs -I {} unrar x -o+ "{}" '+STAGING_PATH+path+torrent_id+'/'
            log.debug('Shelling out: %s' % cmd)
            ret = call(cmd, shell=True)
            if ret != 0:
                log.warning('Unrar command returned non-zero value %d.' % ret)

        cmd=FLEXGET_COMMAND+' -c '+FLEXGET_SORTING_CONFIG+' execute --task '+FLEXGET_TASK_PREFIX + task + (' --disable-advancement' if 'tv' in path else '')
        log.debug('Shelling out: %s' % cmd)
        ret = call(cmd, shell=True)
        if ret != 0:
            log.warning('Flexget command returned non-zero value %d.' % ret)

chain()

