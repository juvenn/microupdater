#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Handling scheduled tasks"""

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from model import Entry, Channel

class CronedHandler(webapp.RequestHandler):
  """Task handler"""
  def get(self):
    task = self.request.get("task")
    if task == "cleanup":
      # Remove obsolete entries
      Entry.cleanup()
    elif task == "subscribe":
      # Periodically make subscribe request
      #
      # Priorily subscribe to newly added channel (i.e. status == None);
      # if there aren't any, then confirm the least checked subscription.
      ch = Channel.all().filter("status =", None).get()
      if not ch:
	ch = Channel.all().filter("status =",
	            "subscribed").order("lastcheck").get()
      ch.subscribe()
    else: self.error(404)

application = webapp.WSGIApplication([
  ("/admin/croned*", CronedHandler),
  ]) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
