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

class FeedLoader(bulkload.Loader):
  def __init__(self):
    bulkload.Loader.__init__(self, 'Feed',
	[('key_name', str),
	 ('url', datastore_types.Link)
	 ])

  def HandleEntity(self, entity):
    # Make entities searchable.
    ent = search.SearchableEntity(entity)
    ent['updated'] = datetime(2009, 1, 1)
    return ent


if __name__ == '__main__':
  bulkload.main(FeedLoader())
