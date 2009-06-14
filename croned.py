#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Handling Cron-ed Jobs"""

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from google.appengine.api import memcache
from updater import Updater
from mudel import Entry

class CronedHandler(webapp.RequestHandler):
  def get(self):
    action = self.request.get("action")
    if action == "sync":
      u = Updater.get_by_key_name("reader_river")
      if u.sync(): 
	# Free memcache
	if not memcache.delete_multi(["entries", "sponsors"],
	    key_prefix="sec_"):
	  logging.warning("memcache.delete_multi not succeeded")
    elif action == "cleanup":
      Entry.cleanup()
    else: self.error(403) # access denied

application = webapp.WSGIApplication([
  ("/admin/croned*", CronedHandler),
  ]) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
