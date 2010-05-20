#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Data Model"""

import logging
import urllib
from datetime import datetime, timedelta
from google.appengine.api import urlfetch
from google.appengine.ext import db

class Channel(db.Model):
  # Class constant. PuSH verify_token 
  TOKEN = "SSBMb3ZlIFlvdSwgSm91bGUK" 

  title = db.StringProperty(required=True)
  topic = db.LinkProperty(required=True)
  # Feed's unique identifier
  uid = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  featured = db.BooleanProperty(default=False)
  logo = db.LinkProperty(required=True)
  # Subscribe status: 
  # `None` will keep channel off normal automatic sub/unsub cycle.
  status = db.StringProperty(default="unsubscribed",
      choices = [None, 
	         "subscribing",
	         "subscribed",
		 "unsubscribing",
		 "unsubscribed"])

  twitter = db.StringProperty()
  friendfeed = db.StringProperty()

  @property
  def latest_entry(self):
    q = self.entry_set.order("-updated")
    return q.get()
    
  def subscribe(self):
    self.status = "subscribing"
    self.command("subscribe")
    self.put()

  def unsubscribe(self):
    self.status = "unsubscribing"
    self.command("unsubscribe")
    self.put()

  def command(self, action):
    params = {
	"hub.mode": action,
	"hub.topic": self.topic,
	"hub.verify": "async",
	"hub.callback": "/subbub/" + self.key(),
	"hub.verify_token": TOKEN
	}
    data = urllib.urlencode(params)
    authcode = base64.urlsafe_b64encode(":".join([USER,PASSWORD]))
    headers={"Authorization": "Basic " + authcode,
	     "Content-Type": "application/x-www-form-urlencoded"}
    try:
      re = urlfetch.fetch(url=HUB,
	  payload=data,
	  method=urlfetch.POST,
	  headers=headers
	  )
    except Error, e:
      logging.error("URL fetch %s failed: %s" % (HUB, e))
      taskqueue.add(url="/subscribe/" + self.key())
      self.status = "unsubscribed" if action == "subscribe" else "subscribed"
    # 204 - Already done
    # 202 - Accepted, wait for verification
    elif re.status_code == 204:
      self.status = action + "d"
    elif re.status_code == 202:
      logging.info("The request accepted: %s to %s" % 
	  (action, self.topic))
    else:
      logging.warning("Hub %d: %s" % (re.status_code, re.content))
      taskqueue.add(url="/subscribe/" + self.key())
      self.status = "unsubscribed" if action == "subscribe" else "subscribed"



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
    """Cleanup datastore.
    Cleaup by delete old entries, default to updated 30 days ago
    """
    outdate = datetime.utcnow() - timedelta(days)
    entry_query = Entry.all().order("updated").filter("updated <=",outdate)
    entries = entry_query.fetch(100)
    db.delete(entries)
    logging.info("Entries updated before %s were succeesfully deleted." %
	outdate.isoformat())


