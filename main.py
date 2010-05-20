#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main Page Handler"""

import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from model import Entry, Channel


class MainPage(webapp.RequestHandler):
  def get(self):
    sec = {}
    query = Entry.all().order("-updated")
    entries = query.fetch(25)
    sec["entries"] = self.render_sec_entries(entries)

    sec["sponsors"] = self.render_sec_sponsors()
    path = self.template("main.html")
    self.response.out.write(template.render(path, sec))

  def render_sec_entries(self, entries):
    path = self.template("_entries.html")
    return template.render(path, {"entries":entries})

  def render_sec_sponsors(self):
    query = Channel.all().filter("featured =", True)
    featured_channels = query.fetch(6)
    entries = [ch.latest_entry for ch in featured_channels
	if ch.latest_entry]
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
