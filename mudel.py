#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Customized db schema for Microupdater."""

from datetime import datetime, timedelta
import logging

from google.appengine.ext import db
from google.appengine.api import urlfetch

import feedparser

class Channel(db.Model):
    # About team and products. 
    producer = db.StringProperty(verbose_name='Producer')
    products = db.StringListProperty(verbose_name='Product(s)')
    location = db.PostalAddressProperty(verbose_name='Location')

    # About channel.
    url = db.LinkProperty(verbose_name='Feed URL',
	required=True)
    tags = db.ListProperty(item_type=db.Category, 
	verbose_name='Tags')
    img_src = db.LinkProperty(verbose_name='Logo')
    
    # Channel update status.
    updatable = db.BooleanProperty()
    updated = db.DateTimeProperty()
    last_fetch = db.DateTimeProperty()
    etag = db.StringProperty()
    last_modified = db.StringProperty()

    def initialize(self):
      """initialize()

      Attempt to fetch the channel url, 
      get initial etag and last-modified value.

      Returns:
        The initialized entity, if succeeded.
      """
      try:
        re = urlfetch.fetch(url=self.url)
      except:
	raise
      else:
	if re.status_code == 200:
	  pa = feedparser.parse(re.content)
	  if pa.feed:
	    if not self.producer:
	      self.producer = pa.feed.get("publisher")
	    if not self.img_src:
	      self.img_src = pa.feed.image.get("href")
	    self.updated = self.last_fetch = datetime.now()
	    self.etag = re.headers.get("etag")
	    self.last_modified = re.headers.get("last-modified")
            self.put()
	    return self

    
class Entry(db.Model):
    title = db.StringProperty(required=True)
    link = db.LinkProperty(required=True)
    summary = db.TextProperty()
    img_src = db.LinkProperty()
    updated = db.DateTimeProperty()

    channel = db.ReferenceProperty(reference_class=Channel,
	collection_name='entries',
	required=True)

    # Clear outdated entries, default saving for 30 days.
    def clear(td=timedelta(30, 0, 0)):
        """clear()

	Clear outdated entries, i.e. default 30 days since updated.
	"""
	outdated_dt = datetime.utcnow() - td
	for ent in Entry.all().order('updated'):
	    if ent.updated <= outdated_dt:
		ent.delete()
        logging.info("Entries updated before %s were cleared.",
	    outdated_dt.strftime("%c"))


class Featured(db.Model):
  """Featured status

  For channels featured on top or side. Includes start and end of being
  featured, exclusive featured on top or not, latest updated entry of 
  the channel etc.
  """
  channel = db.ReferenceProperty(reference_class=Channel, required=True)
  latest_entry = db.ReferenceProperty(reference_class=Entry)
  exclusive = db.BooleanProperty()

  # Featured time.
  start_dt = db.DateTimeProperty()
  end_dt = db.DateTimeProperty()
