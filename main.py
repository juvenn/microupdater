#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
import logging
import StringIO
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Entry, Feed
from helper import *

class MainPage(webapp.RequestHandler):

  def get(self):
    template_values = self.get_tv()
    path = os.path.join(os.path.dirname(__file__), '_main.html')
    self.response.out.write(template.render(path, template_values))
    
  # Get template values.
  def get_tv(self):
    tv = memcache.get("tv")
    if tv: return tv
    else:
      entry_list = self.render_entry_list()
      last_fetch = Feed.get_by_id(1).last_fetch
      tv = {
	  "entry_list": entry_list,
	  "last_fetch": last_fetch,
	  }
      if not memcache.set(key="tv", value=tv, time=300):
	logging.error("Memcache set failed.")
      return tv

  def render_entry_list(self):
    f = Feed.get_by_id(1)
    f.get_updates()
    entries = Entry.all().order("-updated").fetch(200)
    output = StringIO.StringIO()
    path = os.path.join(os.path.dirname(__file__), '_entry.html')
    for e in entries:
      output.write(template.render(path, {"e":e}))
    return output.getvalue()

application = webapp.WSGIApplication([
  ('/*', MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
