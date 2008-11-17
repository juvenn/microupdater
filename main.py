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
  def get(self, category, no):
    if category == 'web':
      entries_query = Entry.all().filter('channel.tags =', 'web')
    elif category == 'desktop':
      entries_query = Entry.all().filter('channel.tags =', 'desktop')
    elif category == 'mobile':
      entries_query = Entry.all().filter('channel.tags =', 'mobile')
    else:
      # Default for all.
      entries_query = Entry.all()

    template_values = { 
	'entries': entries_query.order('-updated').fetch(50) }

    path = os.path.join(os.path.dirname(__file__), 'base_new.html')
    self.response.out.write(template.render(path, template_values))

# Note that one additional regex group ($|/) routed to get().
application = webapp.WSGIApplication(
    [('/($|web|desktop|mobile)($|/)', MainPage)],
    debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
  # Update db in background?
  updater.sync()
