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
from mudel import Entry, Channel, Featured, Release

class MainPage(webapp.RequestHandler):
  def get(self):
    template_values = self.get_sections()
    path = self.build_path("main.html")
    self.response.out.write(template.render(path,template_values))

  def get_sections(self):
    sec = memcache.get_multi(
	["entries",
	 "sponsors",
	 "release"],
	key_prefix="sec_")
    if not sec.get("entries"):
      sec["entries"] = self.render_sec_entries()
    if not sec.get("sponsors"):
      sec["sponsors"] = self.render_sec_sponsors()
    if not sec.get("release"):
      sec["release"] = self.render_sec_release()
    if memcache.add_multi(sec, key_prefix="sec_"):
      # Failed to cache some keys. Note that add_multi will
      # return list of keys which FAILED to cache. Ref SDK doc
      logging.warning("memcache.add_multi() not succeded.")
    return sec

  def render_sec_entries(self):
    q1 = Entry.all().order("-published")
    dt = q1.get().published
    q2 = q1.filter("published >=", dt-timedelta(2))
    entries = q2.fetch(25)
    path = self.build_path("_entries.html")
    return template.render(path, {"entries":entries})

  def render_sec_sponsors(self):
    f_query = Featured.all().filter("enabled =", True)
    fs = f_query.fetch(6)
    cls = [f.channel for f in fs if f.channel]
    entries = []
    for cl in cls:
      e = cl.entry_set.order("-published").get()
      if e: entries.append(e)
    path = self.build_path("_sponsors.html")
    return template.render(path, {"entries":entries})

  def render_sec_release(self):
    q1 = Release.all().order("-release_at")
    q2 = q1.filter("release_at >=", datetime.utcnow())
    rls = q2.fetch(5)
    path = self.build_path("_release.html")
    return template.render(path, {"rls":rls})
    

  def build_path(self, path):
    return os.path.join(os.path.dirname(__file__), path)


application = webapp.WSGIApplication([
  ("/*", MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
