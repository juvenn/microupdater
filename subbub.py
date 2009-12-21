#!/usr/bin/env python2.5
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#


import hashlib
from google.appengine.ext import db


class Subscription(db.Model):
  channel = db.ReferenceProperty(Channel, required=True)
  hub = db.LinkProperty(required=True,
      default='http://superfeedr.com/hubbub')
  status = db.StringProperty(default=None,
      choices=[None,
	'subscribing',
	'subscribed',
	'unsubscribing',
	'unsubscribed'])
  verify_token = db.StringProperty()

  def __init__(self):
    
