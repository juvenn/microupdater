#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Handling Cron-ed Jobs"""

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from model import Entry

class CronedHandler(webapp.RequestHandler):
  def get(self):
    action = self.request.get("action")
    if action == "cleanup":
      Entry.cleanup()
    else: self.error(403) # access denied

application = webapp.WSGIApplication([
  ("/admin/croned*", CronedHandler),
  ]) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
