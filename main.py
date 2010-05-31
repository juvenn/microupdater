#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Page handlers"""

import os
import logging

from datetime import datetime
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from model import Entry, Channel

# Entries per page
PAGESIZE = 25

def templatepath(filename):
  """Build template path

  templates directory default to `./templates/`
  """
  return os.path.join(os.path.dirname(__file__), "templates", filename)

class MainPage(webapp.RequestHandler):
  """Home page handler"""

  def get(self):
    context = {}
    query = Entry.all().order("-updated")
    next = self.request.get("next")
    if next:
      dt = datetime.strptime(next, "%Y-%m-%dT%H:%M:%S")
      entries = query.filter("updated <=",
	  dt).fetch(PAGESIZE + 1)
      if len(entries) == PAGESIZE + 1:
	context["next"] = entries[-1].updated.isoformat("T")
      else:
	context["next"] = None
      context["entries"] = entries[:PAGESIZE]
      self.response.out.write(self.render_sec_entries(context))
      return
    else:
      sec = {}
      entries = query.fetch(PAGESIZE + 1)
      if len(entries) == PAGESIZE + 1:
	context["next"] = entries[-1].updated.isoformat("T")
      else:
	context["next"] = None
      context["entries"] = entries[:PAGESIZE]
      sec["entries"] = self.render_sec_entries(context)

      sec["featured"] = self.render_sec_featured()
      path = templatepath("main.html")
      self.response.out.write(template.render(path, sec))

  def render_sec_entries(self, context):
    """Render entries section"""
    path = templatepath("_entries.html")
    return template.render(path, context)

  def render_sec_featured(self):
    """Render featured section"""
    query = Channel.all().filter("featured =", True)
    featured_channels = query.fetch(6)
    entries = [ch.latest_entry for ch in featured_channels
	if ch.latest_entry]
    path = templatepath("_featured.html")
    return template.render(path, {"entries":entries})


class FollowingPage(webapp.RequestHandler):
  """List Fowllowing Channels
  """
  def get(self):
    context = {}
    context['channels'] = Channel.all().fetch(1000)
    path = templatepath("following.html")
    self.response.out.write(template.render(path, context))


application = webapp.WSGIApplication([
  ("/", MainPage),
  ("/following", FollowingPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
