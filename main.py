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
    template_values = self.get_sections()
    path = self.template_path("main.html")
    self.response.out.write(template.render(path,template_values))

  def get_sections(self):
    sec = memcache.get_multi(
	["entries",
	 "sponsors"],
	key_prefix="sec_")
    if not sec.get("entries"):
      sec["entries"] = self.render_sec_entries()
    if not sec.get("sponsors"):
      sec["sponsors"] = self.render_sec_sponsors()
    if memcache.set_multi(sec, key_prefix="sec_"):
      # Failed to cache some keys. Note that add_multi will
      # return list of keys which FAILED to cache. Ref SDK doc
      logging.warning("memcache.set_multi() not succeeded.")
    return sec

  def render_sec_entries(self):
    query = Entry.all().order("-published")
    entries = query.fetch(30)
    path = self.template_path("_entries.html")
    return template.render(path, {"entries":entries})

  def render_sec_sponsors(self):
    f_query = Featured.all().filter("enabled =", True)
    fs = f_query.fetch(6)
    cls = [f.channel for f in fs if f.channel]
    entries = []
    for cl in cls:
      e = cl.entry_set.order("-published").get()
      if e: entries.append(e)
    path = self.template_path("_sponsors.html")
    return template.render(path, {"entries":entries})

  def template_path(self, filename):
    return os.path.join(os.path.dirname(__file__), "template", filename)


application = webapp.WSGIApplication([
  ("/*", MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
