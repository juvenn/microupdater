#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
import logging
from datetime import datetime, timedelta, time

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Entry, Channel

class MainPage(webapp.RequestHandler):
  def get(self):
    sec_entry = self.get_sec_entry()
    path = os.path.join(os.path.dirname(__file__), "main.html")
    self.response.out.write(template.render(path, 
      {"sec_entry":sec_entry}))

  def get_sec_entry(self, from_date=datetime.utcnow().date()):
    """Get html rendered entries
     
    Check against memcache if any new entries in datastore not cached:
    if do, refetch entries from datastore, and cache it use from_date
    as the key; return the cached value, if not.

    Args:
      from_date, the entries published on from_date and from_date-1 
                 will be fetched and cached.

    Returns:
      A slice of HTML containing entries.
    """
    datestamp = from_date.strftime("%Y%m%d")
    cached = memcache.get(datestamp, namespace="entry")

    max_dt = datetime.combine(from_date, time.max)
    min_dt = datetime.combine(from_date-timedelta(1), time.min)
    # Filter for min_dt<=published>=max_dt,
    # splitted for readablity.
    q = Entry.all().order("-published").filter("published <=",max_dt)
    entries_query = q.filter("published >=", min_dt)
    # Get the updated time of the date
    updated = entries_query.get().published
    if cached and (cached["updated_at"] >= updated):
      return cached["sec_entry"]
    else:
      sec_entry = self.render_sec_entry(entries_query, from_date)
      cache_item = {"updated_at":updated,
	  "sec_entry":sec_entry}
      # Use datestamp for key, in convinience of get
      # cached for 24 hours
      if not memcache.set(datestamp,cache_item,
	  time=86400,namespace='entry'):
	logging.error("%s -entry memcache failed." % datestamp)
      return sec_entry

  def render_sec_entry(self, query, from_date):
    """Render the queried entries

    Render entries from query, from_date's entries (em_entries) will
    be more in detail, compared to from_date-1 's.

    Returns: a html slice containing rendered entries
    """
    entries = query.fetch(100)
    em_entries = []
    for e in entries:
      if e.pub_date == from_date:
	entries.remove(e)
	em_entries.append(e)

    path = os.path.join(os.path.dirname(__file__), "_entry.html")
    rendered = template.render(path,
	{"from_date":from_date, 
	 "em_entries":em_entries,
	 "entries":entries}
	)
    return rendered


application = webapp.WSGIApplication([
  ("/*", MainPage),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
