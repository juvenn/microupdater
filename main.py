#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main Page Handler"""

import os
import logging
from datetime import datetime, timedelta, time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Entry, Channel, Featured

class MainPage(webapp.RequestHandler):
  def get(self):
    sec = {}
    query = Entry.all().order("-published")
    entries = query.fetch(30)
    sec["entries"] = self.render_sec_entries(entries)

    sec["sponsors"] = self.render_sec_sponsors()
    path = self.template("main.html")
    self.response.out.write(template.render(path, sec))

  def render_sec_entries(self, entries):
    path = self.template("_entries.html")
    return template.render(path, {"entries":entries})

  def render_sec_sponsors(self):
    f_query = Featured.all().filter("enabled =", True)
    fs = f_query.fetch(6)
    cls = [f.channel for f in fs if f.channel]
    entries = []
    for cl in cls:
      e = cl.entry_set.order("-published").get()
      if e: entries.append(e)
    path = self.template("_sponsors.html")
    return template.render(path, {"entries":entries})

  def template(self, filename):
    return os.path.join(os.path.dirname(__file__), "templates", filename)


application = webapp.WSGIApplication([
  ("/*", MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
