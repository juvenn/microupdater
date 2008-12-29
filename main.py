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
    path = os.path.join(os.path.dirname(__file__), '_main.html')
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
      path = os.path.join(os.path.dirname(__file__), 'u_edit.html')
      template_values = {}
      url = self.request.get("url")
      if not url:
	template_values["flash"] = "Seems you have not offered feed url. Do you?"
      else:
	chnl = Channel.all().filter("url =", url).get()
	if not chnl: 
	 try:
	  chnl = Channel(url=url)
	  chnl.initialize()
	 except:
	   template_values["flash"] = "Sorry, but we could not fetch your feed. Feel free to contact me for your error."
	   template_values["urlfield"] = chnl.url
	 else:
	   template_values["titlefield"] = chnl.title
	   template_values["urlfield"] = chnl.url
	else:
	  template_values["titlefield"] = chnl.title
	  if chnl.producer:
	   template_values["teamfield"] = chnl.producer.name
	   template_values["locationfield"] = chnl.producer.location
	   template_values["emailfield"] = chnl.producer.email

      self.response.out.write(template.render(path, template_values))
    elif action == 'save':
      self.put()
    else: self.get(action)

  def put(self):
    self.request.get
    # TODO: parse self.request and put entities into db.
    # out.write succees.

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/u/(add|edit|save)', EditPage)
  ])

def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
