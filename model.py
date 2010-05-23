#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Models"""

import logging
import urllib
from datetime import datetime, timedelta
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext import db

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

class Channel(db.Model):
  title = db.StringProperty()
  topic = db.LinkProperty(required=True)
  # Feed's unique identifier
  uid = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  featured = db.BooleanProperty(default=False)
  logo = db.LinkProperty()
  # Last confirming of the subscription
  lastcheck = db.DateTimeProperty(auto_now=True)
  # Subscribe status: 
  status = db.StringProperty(default=None,
      choices = [None,
	         "subscribing",
	         "subscribed",
		 "unsubscribing",
		 "unsubscribed"])

  @property
  def latest_entry(self):
    q = self.entry_set.order("-updated")
    return q.get()

  # Last update time of the channel,
  # seed on 2010-05-27 if not updated.
  @property
  def updated(self):
    entry = self.latest_entry()
    return entry.updated if entry else datetime(2010, 5, 27)
    
  def subscribe(self):
    """PuSH subscribe"""
    self.status = "subscribing"
    self.command("subscribe")

  def unsubscribe(self):
    """PuSH unsubscribe"""
    self.status = "unsubscribing"
    self.command("unsubscribe")

  def command(self, action):
    """Issue async commands

    action - `subscribe` or `unsubscribe`.

    Send async command to hub. If failed, the command will be queued
    for later trying.
    """
    params = {
	"hub.mode": action,
	"hub.topic": self.topic,
	"hub.verify": "async",
	"hub.callback": WORKER.subbub + self.key(),
	"hub.verify_token": HUB.token
	}
    data = urllib.urlencode(params)
    headers={"Content-Type": "application/x-www-form-urlencoded"}

    # Basic authorization
    if HUB.get("auth"):
      authcode = base64.urlsafe_b64encode(":".join(HUB.auth))
      headers["Authorization"] = "Basic " + authcode
    try:
      re = urlfetch.fetch(url=HUB.url,
	  payload=data,
	  method=urlfetch.POST,
	  headers=headers
	  )
    except Error, e:
      logging.error("URL fetch %s failed: %s" % (HUB.url, e))
      taskqueue.add("hub.mode="+action,
	            url=WORKER.subscriber+self.key())
      self.status = "unsubscribed" if action == "subscribe" else "subscribed"
    else:
      # 204 - Already done
      # 202 - Accepted, wait for verification
      if re.status_code == 204:
	self.status = action + "d"
      elif re.status_code == 202:
	logging.info("The request accepted: %s to %s" % 
	    (action, self.topic))
      else:
	logging.warning("Hub %d: %s" % (re.status_code, re.content))
	taskqueue.add("hub.mode="+action,
		      url=WORKER.subscriber+self.key())
	self.status = "unsubscribed" if action == "subscribe" else "subscribed"

    self.put()



class Entry(db.Model):
  author = db.StringProperty()
  title = db.StringProperty(required=True)
  # Entry's unique identifier 
  uid = db.StringProperty(required=True)
  link = db.LinkProperty(required=True)
  content = db.TextProperty()
  updated = db.DateTimeProperty(required=True)
  channel = db.ReferenceProperty(Channel,required=True)

  @property
  def date(self):
    return self.updated.date()

  @staticmethod
  def cleanup(days=30):
    """Cleanup entry table.

    Delete older (default >= 30 days) entries
    """
    outdate = datetime.utcnow() - timedelta(days)
    entry_query = Entry.all().order("updated").filter("updated <=",outdate)
    entries = entry_query.fetch(100)
    db.delete(entries)
    logging.info("Entries updated before %s were succeesfully deleted." %
	outdate.isoformat())


