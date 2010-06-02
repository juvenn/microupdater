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
from model import Entry, Channel, WORKER, HUB
import feedparser


class PushCallback(webapp.RequestHandler):
  """PuSH callback handler

  PubSubHubbub 0.3 spec
  """
  def get(self):
    """Handling PuSH verification

    Response:
    2xx hub.challenge  
        We agree with the action, the token matched, the topic found.
    404  
        Disagree with the action, please don't retry.
    4xx / 5xx
        Temporary failure, please retry later.
    """
    logging.info("Upon verification: %s from %s" % 
	(self.request.url, self.request.remote_addr))
    token = self.request.get("hub.verify_token")
    if token != HUB['token']:
      # token not match
      self.error(404)
      logging.error("Token not match: %s from %s" % 
	  (self.request.url, self.request.remote_addr))
      return # fail fast

    # PuSH verification will come at WORKER['subbub'] + `key`
    # path = WORKER['subbub'] + "key"
    key = self.request.path[len(WORKER['subbub']):] 
    try:
      channel = Channel.get(key)
    except:
      logging.error("Broken key: %s from %s" %
	  (self.request.path, self.request.remote_addr))
      self.error(404)
    else:
      if channel:
	mode = self.request.get("hub.mode")
	topic = self.request.get("hub.topic")
	if (mode and topic and channel.status == mode[:-1] + "ing"  
	         and channel.topic == topic):
	  channel.status = mode + "d"
	  channel.put()
	  logging.info("Verify success: %s to %s" % 
	      (channel.status, channel.topic))
	  self.response.out.write(self.request.get("hub.challenge"))
	else:
	  logging.error("Status or topic not match: %s" %
	      self.request.url)
	  self.error(404)
      else:
	# Topic not found
	logging.error("Channel key not found: %s" % key)
	self.error(412)

  # Upon notification
  def post(self):
    """Handle PuSH notifications

    Response:
    2xx 
        Notification received
    3xx / 4xx / 5xx
        Fail, please retry the notification later

    Atom/rss feed is queued to `ParseWorker` for later parsing
    """
    type = self.request.headers["Content-Type"]

    # Content-Type not match, respond fast
    if type not in ["application/atom+xml","application/rss+xml"]:
      self.response.headers.__delitem__("Content-Type")
      self.error(204)
      return

    try:
      key = self.request.path[len(WORKER['subbub']):]
      ch = Channel.get(key)
    except (db.KindError, db.BadKeyError):
      logging.error("Broken Key at notification: %s" % 
	  self.request.url)
      self.response.headers.__delitem__("Content-Type")
      self.response.set_status(204)
    except:
      # Datastore Error, please retry notification
      self.error(500)
    else:
      body = self.request.body.decode("utf-8")
      if not (ch and body):
	if not ch: 
	  logging.error("Key Not Found at notification: %s" % 
	    self.request.url) 
	self.response.headers.__delitem__("Content-Type")
	self.response.set_status(204)
      else:
	taskqueue.Task(body,
	    url=WORKER['parser'] + key,
	    headers={"Content-Type": type}).add(queue_name="parse")
	logging.info("Upon notifications: %s from %s" % 
	    (self.request.url, self.request.remote_addr))
	self.response.set_status(202)


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

    # WORKER['parser'] + `key`
    key = self.request.path[len(WORKER['parser']):]
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
    else:
      # First time get the notification,
      # so update channel's properties 
      if channel and not channel.uid:
	channel.title = doc.feed.title.split(" - ")[0] 
	channel.uid = uid
	# Fallback to topic feed, if no link found
	channel.link = doc.feed.get("link", channel.topic)
	channel.put()

    updates = []
    for e in doc.entries:
      author = e.author if e.get("author") else None
      content = e.content[0].value if e.get("content") else e.summary
      # Fallback to published if no updated field.
      t = e.updated_parsed if e.get("updated_parsed") else e.published_parsed
      updated = datetime(t[0],t[1],t[2],t[3],t[4],t[5])

      # If we have this entry already in datastore, then the entry 
      # should be updated instead of inserted.
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
    key = self.request.path[len(WORKER['subscriber']):]
    try:
      channel = Channel.get(key)
    except:
      logging.error("Broken channel key: %s" % self.request.path)
      return

    action = self.request.get("hub.mode")
    if not action:
      logging.error("hub.mode not found in payload: %s from %s" % 
	  (self.request.body, self.request.url))
      self.error(204)
    if channel:
      if action == "subscribe": channel.subscribe()
      else: channel.unsubscribe()
    else:
      logging.error("Channel key not found: %s" % self.request.path)
      self.error(204)

application = webapp.WSGIApplication([
  (WORKER['subbub'] + ".*", PushCallback),
  (WORKER['parser'] + ".*", ParseWorker),
  (WORKER['subscriber'] + ".*", SubscribeWorker),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
