#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
import logging
from datetime import datetime
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Channel, Entry, Featured

class MainPage(webapp.RequestHandler):

  def get(self, category):
    entries = self.get_entries()
    if category == 'web':
      entries = [e for e in entries \
	  if 'web' in e.channel.tags]
      template_values = {'webtab': 'on'}
    elif category == 'desktop':
      entries = [e for e in entries \
	  if 'desktop' in e.channel.tags]
      template_values = {'desktoptab': 'on'}
    elif category == 'mobile':
      entries = [e for e in entries \
	  if 'mobile' in e.channel.tags]
      template_values = {'mobiletab': 'on'}
    else:
      # Default for all.
      template_values = {'alltab': 'on'}

    featured_entries = [f.latest_entry \
	for f in Featured.all().filter('exclusive =', False) \
	if f.latest_entry]
    F = Featured.all().filter('exclusive =', True).get()
    if F and F.latest_entry: exclusive_entry = F.latest_entry
    else: exclusive_entry = entries[0]
    template_values['entries'] = entries[:50]
    template_values['featured_entries'] = featured_entries
    template_values['exclusive_entry'] = exclusive_entry
    path = os.path.join(os.path.dirname(__file__), 'base_new.html')
    self.response.out.write(template.render(path, template_values))
    
  # Get memcached entries.
  def get_entries(self):
    chnl = Channel.all().filter('updatable =', True).order('last_fetch').get()
    entries = memcache.get("entries")
    if chnl.get_updates() or not entries:
      entries = Entry.all().order('-updated').fetch(200)
      if not memcache.set("entries", entries):
	logging.error("Memcache set failed.")
    return entries


application = webapp.WSGIApplication(
    [('/($|web|desktop|mobile)', MainPage)])

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
