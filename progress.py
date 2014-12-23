#!/usr/bin/env python3.4

import sys

def startprogress(title):
    """Creates a progress bar 40 chars long on the console
    and moves cursor back to beginning with BS character"""
    global progress_x
    sys.stdout.write(title + ": [" + "-" * 40 + "]" + chr(8) * 41)
    sys.stdout.flush()
    progress_x = 0


def progress(x):
    """Sets progress bar to a certain percentage x.
    Progress is given as whole percentage, i.e. 50% done
    is given by x = 50"""
    global progress_x
    x = int(x * 40 // 100)
    sys.stdout.write("#" * x + "-" * (40 - x) + "]" + chr(8) * 41)
    sys.stdout.flush()
    progress_x = x


def endprogress():
    """End of progress bar;
    Write full bar, then move to next line"""
    sys.stdout.write("#" * 40 + "]\n")
    sys.stdout.flush()
