#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    :platform: Unix
    :synopsis: Fetches ESGF configuration files from GitHub repository.

"""

import os
import sys
import traceback

import requests

from constants import *
from context import ProcessingContext
from esgprep.utils.misc import gh_request_content, backup, write_content, do_fetching, Print, COLORS


def run(args):
    """
    Main process that:

     * Decide to fetch or not depending on file presence/absence and command-line arguments,
     * Gets the GitHub file content from full API URL,
     * Backups old file if desired,
     * Writes response into INI file.

    :param ArgumentParser args: Parsed command-line arguments

    """
    # Init print management
    Print.init(log=args.log, debug=args.debug, cmd=args.prog)
    # Instantiate processing context manager
    with ProcessingContext(args) as ctx:
        # Print command-line
        Print.command(COLORS.OKBLUE + 'Command: ' + COLORS.ENDC + ' '.join(sys.argv))
        # Counter
        progress = 0
        for project in ctx.targets:
            try:
                # Set full url
                url = ctx.url.format(INI_FILE.format(project))
                # Set output file full path
                outfile = os.path.join(ctx.config_dir, INI_FILE.format(project))
                # Get GitHub file content
                r = gh_request_content(url=url, auth=ctx.auth)
                sha = r.json()['sha']
                content = requests.get(r.json()['download_url'], auth=ctx.auth).text
                # Fetching True/False depending on flags and file checksum
                if do_fetching(outfile, sha, ctx.keep, ctx.overwrite):
                    # Backup old file if exists
                    backup(outfile, mode=ctx.backup_mode)
                    # Write new file
                    write_content(outfile, content)
                    Print.info('\n:: FETCHED :: {} --> {}'.format(url.ljust(LEN_URL), outfile))
                else:
                    Print.info('\n:: SKIPPED :: {}'.format(url.ljust(LEN_URL)))
            except KeyboardInterrupt:
                raise
            except Exception:
                exc = traceback.format_exc().splitlines()
                msg = COLORS.HEADER + project + COLORS.ENDC + '\n'
                msg += '\n'.join(exc)
                Print.exception(msg, buffer=True)
                ctx.error = True
            finally:
                progress += 1
                percentage = int(progress.value * 100 / ctx.nfiles)
                msg = COLORS.OKBLUE + '\rFetching project(s) config: ' + COLORS.ENDC
                msg += '{}% | {}/{} files'.format(percentage, progress, ctx.nfiles)
                Print.progress(msg)
    # Flush buffer
    Print.flush()
    # Evaluate errors and exit with appropriated return code
    if ctx.error:
        sys.exit(1)
