#!/usr/bin/env python2.5
#
# Copyright (c) 2010 Juvenn Woo.
# http://twitter.com/juvenn.
#

import logging
from datetime import datetime
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from model import Entry, Channel

# PubSubHubbub callback handler
class PushCallback(webapp.RequestHandler):
  # Upon verifications
  #
  # PuSH verification will come at `/subbub/object_key`
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
    logging.info("Upon verifycation: %s from %s" % 
	(self.request.url, self.request.remote_addr))
    token = self.request.get("hub.verify_token")
    if token != Channel.TOKEN:
      # Unauthorized, token not match
      self.error(401)
      logging.error("Token not match: %s from %s" % 
	  (self.request.url, self.request.remote_addr))
      return # fail fast

    # path = "/subbub/key"
    key = self.request.path[8:] 
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
    type = self.request.headers["Content-Type"]
    if type == "application/atom+xml" or type == "application/rss+xml":
      key = self.request.path[8:]
      taskqueue.add(self.request.body.decode("utf-8"),
		    url="/parse/" + key,
		    headers={"Content-Type": type})
      self.response.set_status(200)
      logging.info("Upon notifications: %s from %s" % 
	  (self.request.url, self.request.remote_addr))
    else:
      # Not implemented
      self.error(501)


# Queued tastks of parsing incoming notifications
class ParseWorker(webapp.RequestHandler):
  def get(self):
    self.error(501)

  def post(self):
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

    # `/parse/key`
    key = self.request.path[7:]
    # Try to get the channel by key;
    # fallback to feed id, if not found;
    # and at last we'll resort to entry source id,
    # to find out the associated channel
    channel = None
    try:
      channel = Channel.get(key)
    except:
      uid = doc.feed.id
      channel = Channel.all().filter("uid =", uid).get()

    updates = []
    for e in doc.entries:
      author = e.author if e.get("author") else None
      content = e.content[0].value if e.get("content") else e.summary
      # Fallback to published if no updated field.
      t = e.updated_parsed if e.get("updated_parsed") else e.published_parsed
      updated = datetime(t[0],t[1],t[2],t[3],t[4],t[5])

      # If we have this entry already in datastore, then the entry is
      # updated instead of new published. So we update the entity 
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


application = webapp.WSGIApplication([
  ("/subbub/*", PushCallback),
  ("/parse/*", ParseWorker),
  ])

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
