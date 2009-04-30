#!/usr/bin/env INTERPRETER
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Handling cron-ed jobs"""

from google.appengine.ext import webapp
from updater import Updater
from mudel import Entry

class CronedHandler(webapp.RequestHandler):
  def get(self):
    if self.request.headers.get("X-AppEngine-Cron"):
      action = self.request.get("action")
      if action == "sync":
	u = Updater.get_by_key_name("reader_river")
	u.fetch()
      elif action == "cleanup":
	Entry.cleanup()
    self.error(403) # access denied
