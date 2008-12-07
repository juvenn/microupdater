#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Main routine of Microupdater."""

import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from mudel import Channel, Entry, Featured
from helper import *

class MainPage(webapp.RequestHandler):

  def get(self):
    entries = Entry.all().order('-updated')#TODO:self.get_entries()
    featured_entries = [f.latest_entry \
	for f in Featured.all()	if f.latest_entry]
    template_values = {
	'entries': entries[:50],
	'featured_entries': featured_entries}
    path = os.path.join(os.path.dirname(__file__), '_home.html')
    self.response.out.write(template.render(path, template_values))
    
  # Get memcached entries.
  def get_entries(self):
    updatable_channels = Channel.all.filter('updatable =', True)
    chnl = updatable_channels.order('last_fetch').get()
    if not chnl:
      # Get a randomized channel.
      rd = randum(updatable_channels.count())
      chnl = updatable_channels[rd-1]

    entries = memcache.get("entries")
    if chnl.get_updates() or not entries:
      entries = Entry.all().order('-updated').fetch(200)
      if not memcache.set("entries", entries):
	logging.error("Memcache set failed.")
    return entries


class EditPage(webapp.RequestHandler):

  def get(self, action):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'u_edit.html')
    self.response.out.write(template.render(path, template_values))

  def post(self, action):
    if action == 'edit':
      pass
      # TODO: out.write edit template
      # validate url
      # try initialize and catch exceptions
      # return a form with initialized data, if succeeded.
      # report error to user, else.
    elif action == 'save':
      self.put()
    else: self.get(action)

  def put(self):
    pass
    # TODO: parse self.request and put entities into db.

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/u/(add|edit|save)', EditPage)
  ])

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
