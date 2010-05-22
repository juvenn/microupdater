#!/usr/bin/env python2.5
#
# Copyright (c) 2010 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""PubSubHubbub(PuSH) subscriber

PushCallback - Listening for hub's verification or notification requests
ParseWorker - Parse queued atom/rss notifications
SubscribeWorker - Retry queued subscribe/unsubscribe commands
"""

import logging
from datetime import datetime
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from model import Entry, Channel
import feedparser

# URL end points
WORKER = {
    "subbub": "/worker/subbub/", # PubSubHubbub callback
    "parser": "/worker/parse/",
    "subscriber": "/worker/subscribe/"
    }
# PuSH hub configs
HUB = {
    "url": "http://superfeedr.com/hubbub",
    "token": "SSBMb3ZlIFlvdSwgSm91bGUK",
    "auth": ["USER", "PASSWORD"]
    }

class PushCallback(webapp.RequestHandler):
  """PuSH callback handler
  """
  # Upon verifications
  #
  # PuSH verification will come at WORKER.subbub + `key`
  #
  # Response:
  # 200: hub.challenge  
  #      We agree with the action, the token matched, the topic found.
  # 404:  
  #      Disagree with the action, please don't retry.
  # 40x:
  #      Precondition failed, token not match, broken key, or topic not
  #      found. Please retry later.
  #
  # Please check PubSubHubbub specification for references.
  def get(self):
    """Handling PuSH verification"""
    logging.info("Upon verification: %s from %s" % 
	(self.request.url, self.request.remote_addr))
    token = self.request.get("hub.verify_token")
    if token != HUB.token:
      # Unauthorized, token not match
      self.error(401)
      logging.error("Token not match: %s from %s" % 
	  (self.request.url, self.request.remote_addr))
      return # fail fast

    # path = WORKER.subbub + "key"
    key = self.request.path[len(WORKER.subbub):] 
    try:
      channel = Channel.get(key)
    except KindError:
      logging.error("Broken key: %s from %s" %
	  (self.request.path, self.request.remote_addr))
      # Precondition failed, key broken
      self.error(412)
    elif channel:
      mode = self.request.get("hub.mode")
      if mode and channel.status == mode[:-1] + "ing":
	channel.status = mode + "d"
	channel.put()
	self.response.out.write(self.request.get("hub.challenge"))
	logging.info("Verify success: %s to %s" % 
	    (channel.status, channel.topic))
      else:
	self.error(404)
    else:
      # Topic not found
      logging.error("Channel key not found: %s" % key)
      self.error(412)

  # Upon notifications
  def post(self):
    """Handle PuSH notifications

    Atom/rss feed is queued to `ParseWorker` for later parsing
    """
    type = self.request.headers["Content-Type"]
    if type == "application/atom+xml" or type == "application/rss+xml":
      key = self.request.path[len(WORKER.subbub):]
      taskqueue.add(self.request.body.decode("utf-8"),
		    url=WORKER.parser + key,
		    headers={"Content-Type": type})
      self.response.set_status(200)
      logging.info("Upon notifications: %s from %s" % 
	  (self.request.url, self.request.remote_addr))
    else:
      # Not implemented
      self.error(501)


# Queued tastks of parsing incoming notifications
class ParseWorker(webapp.RequestHandler):
  """Worker for queued parsing tasks"""
  def get(self):
    self.error(501)

  def post(self):
    """Parsing queued feeds"""
    doc = feedparser.parse(self.request.body)

    # Bozo feed handling
    # stealed from PubSubHubbub subscriber repo
    if doc.bozo:
      logging.error('Bozo feed data. %s: %r',
                     doc.bozo_exception.__class__.__name__,
                     doc.bozo_exception)
      if (hasattr(doc.bozo_exception, 'getLineNumber') and
          hasattr(doc.bozo_exception, 'getMessage')):
        line = doc.bozo_exception.getLineNumber()
        logging.error('Line %d: %s', line, doc.bozo_exception.getMessage())
        segment = self.request.body.split('\n')[line-1]
        logging.info('Body segment with error: %r', segment.decode('utf-8'))
      return # fail fast

    # WORKER.parser + `key`
    key = self.request.path[len(WORKER.parser):]
    # Try to get the channel by key;
    # fallback to feed id, if not found;
    # and at last we'll resort to entry source id,
    # to find out the associated channel
    channel = None
    uid = doc.feed.id
    try:
      channel = Channel.get(key)
    except:
      channel = Channel.all().filter("uid =", uid).get()
    elif channel and not channel.uid:
      channel.title = doc.feed.title.split(" - ")[0] 
      channel.uid = uid
      channel.put()

    updates = []
    for e in doc.entries:
      author = e.author if e.get("author") else None
      content = e.content[0].value if e.get("content") else e.summary
      # Fallback to published if no updated field.
      t = e.updated_parsed if e.get("updated_parsed") else e.published_parsed
      updated = datetime(t[0],t[1],t[2],t[3],t[4],t[5])

      # If we have this entry already in datastore, then the entry is
      # updated instead of newly published. So we update the entity 
      # instead of insert a new duplicated entity.
      ent = Entry.all().filter("uid =", e.id).get()
      if not ent:
	if not channel: 
	  uid = e.source.id
	  channel = Channel.all().filter("uid =", uid).get()
	ent = Entry(title=e.title,
		    link=e.link,
		    content=content,
		    author=author,
		    updated=updated,
		    uid=e.id,
		    channel=channel)
	logging.info("Get new entry: %s" % e.id)
      else:
	ent.title = e.title
	ent.link = e.link
	ent.content = content
	ent.author = author
	ent.updated = updated
	logging.info("Get updated entry: %s" % e.id)

      updates.append(ent)

    db.put(updates)


class SubscribeWorker(webapp.RequestHandler):
  """Worker for queued (un)subscribe tasks"""
  def get(self):
    self.error(501)

  def post(self):
    key = self.request.path[len(WORKER.subscriber):]
    try:
      channel = Channel.get(key)
    except:
      logging.error("Broken channel key: %s" % self.request.path)
      self.error(404)
      return

    action = self.request.get("hub.mode")
    if not action:
      logging.error("hub.mode not found in payload: %s from %s" % 
	  (self.request.body, self.request.url))
      self.error(404)
    if channel:
      if action == "subscribe": channel.subscribe()
      else: channel.unsubscribe()
    else:
      logging.error("Channel key not found: %s" % self.request.path)
      self.error(404)

application = webapp.WSGIApplication([
  (WORKER.subbub + "*", PushCallback),
  (WORKER.parser + "*", ParseWorker),
  (WORKER.subscriber + "*", SubscribeWorker),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
