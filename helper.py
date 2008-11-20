#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Miscellaneous methods for Microupdater."""

from datetime import datetime, timedelta
from time import time

# Turn timetuple into datetime.
# TODO: rare case leap seconds(61) need to be handled.
def timetuple2datetime(tp):
    return datetime(tp[0], tp[1], tp[2], tp[3], tp[4], tp[5])

