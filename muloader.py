#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Bulk data loader for Microupdater.
"""

from datetime import datetime
from google.appengine.ext import db
from google.appengine.ext import bulkload, search
from google.appengine.api import datastore_types

class ChannelLoader(bulkload.Loader):
  def __init__(self):
    bulkload.Loader.__init__(self, 'Channel',
	[('producer', str),
	 ('url', datastore_types.Link),
	 ('tags', lambda s: [db.Category(t) for t in s.split(',')])
	 ])

  def HandlEntity(self, entity):
    # Make entities searchable.
    ent = search.SearchableEntity(entity)
    return ent

class FeaturedLoader(bulkload.Loader):
  def __init__(self):
    bulkload.Loader.__init__(self, 'Featured',
	[('exclusive', bool),
	 ('channel', datastore_types.Key)])
  

if __name__ == '__main__':
  bulkload.main(ChannelLoader(), FeaturedLoader())
