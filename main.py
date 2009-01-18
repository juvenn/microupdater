#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
import logging
import StringIO
from datetime import datetime, timedelta

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Entry, Feed
from helper import *

class MainPage(webapp.RequestHandler):

  def get(self):
    f = Feed.get_by_id(1)
    el = ""
    if f.last_fetch - datetime.utcnow() > timedelta(0, 300) and f.get_updates():
      el = self.render_entry_list()
    else:
      el = self.get_entry_list()
    template_values = {"entry_list":el, "last_fetch":f.last_fetch}
    path = os.path.join(os.path.dirname(__file__), '_main.html')
    self.response.out.write(template.render(path, template_values))

  def get_entry_list(self):
    el = memcache.get("entry_list")
    if el: return el
    else:
      el = self.render_entry_list()
      return el
    
  def render_entry_list(self):
    # Only latest 7 days' posts fetched
    t = datetime.utcnow() - timedelta(7)
    entries = Entry.all().filter('updated >', t).order("-updated")
    output = StringIO.StringIO()
    path = os.path.join(os.path.dirname(__file__), '_entry.html')
    for e in entries:
      output.write(template.render(path, {"e":e}))
    el = output.getvalue()
    if not memcache.set(key="entry_list", value=el):
      logging.error("Memcache set failed.")
    return el

application = webapp.WSGIApplication([
  ('/*', MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
