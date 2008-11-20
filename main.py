#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
from datetime import datetime
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from mudel import Channel, Entry, Featured
import updater

class MainPage(webapp.RequestHandler):
  def get(self, category):
    if category == 'web':
      entries_query = [e for e in Entry.all().order('-updated') \
	  if 'web' in e.channel.tags]
      template_values = {'webtab': 'on'}
    elif category == 'desktop':
      entries_query = [e for e in Entry.all().order('-updated') \
	  if 'desktop' in e.channel.tags]
      template_values = {'desktoptab': 'on'}
    elif category == 'mobile':
      entries_query = [e for e in Entry.all().order('-updated') \
	  if 'mobile' in e.channel.tags]
      template_values = {'mobiletab': 'on'}
    else:
      # Default for all.
      entries_query = Entry.all().order('-updated')
      template_values = {'alltab': 'on'}

    featured_entries = [f.latest_entry for f in Featured.all().filter('exclusive =', False) \
	if f.latest_entry]
    f = Featured.all().filter('exclusive =', True).get()
    if f and f.latest_entry: exclusive_entry = f.latest_entry
    else: exclusive_entry = Entry.all().order('-updated').get()

    template_values['entries'] = entries_query
    template_values['featured_entries'] = featured_entries
    template_values['exclusive_entry'] = exclusive_entry
    path = os.path.join(os.path.dirname(__file__), 'base_new.html')
    self.response.out.write(template.render(path, template_values))

# Note that one additional regex group ($|/) routed to get().
application = webapp.WSGIApplication(
    [('/($|web|desktop|mobile)', MainPage)],
    debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
  # Update db in background?
  # updater.sync()
