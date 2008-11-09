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

from dbmodel import Channel, Entry
import updater

class MainPage(webapp.RequestHandler):
  def get(self):
    entries_query = Entry.all().order('-updated')
    entries = entries_query.fetch(1000)
    items = [e for e in entries ]

    template_values = { 'items': items }

    path = os.path.join(os.path.dirname(__file__), 'view/index.html')
    self.response.out.write(template.render(path, template_values))

# Route incoming requests to MainPage.
application = webapp.WSGIApplication(
    [('/', MainPage)],
    debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
  # Update db in background.
 # updater.sync()
