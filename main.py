#!/usr/bin/env python
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

from mudel import Channel, Entry
import updater

class MainPage(webapp.RequestHandler):
  def get(self, category, no):
    if category == 'web':
      entries = Entry.all().filter("channel.is_web =", True)\
	  .order('-updated').fetch(50)
    elif category == 'desktop':
      entries = Entry.all().filter('channel.is_desktop =', True)\
	  .order('-updated').fetch(50)
    elif category == 'mobile':
      entries = Entry.all().filter('channel.is_mobile =', True)\
	  .order('-updated').fetch(50)
    else:
      # Default for all.
      entries = Entry.all().order('-updated').fetch(50)

    template_values = { 'entries': entries }

    path = os.path.join(os.path.dirname(__file__), 'base_new.html')
    self.response.out.write(template.render(path, template_values))

# Note that two additional regex group routed to get().
application = webapp.WSGIApplication(
    [('/($|web|desktop|mobile)($|/)', MainPage)],
    debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
  # Update db in background.
 # updater.sync()
