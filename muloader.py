#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Bulk uploader for Microupdater.
"""

from google.appengine.ext import db
from google.appengine.ext import bulkload, search
from google.appengine.api import datastore_types

class ChannelLoader(bulkload.Loader):
  def __init__(self):
    bulkload.Loader.__init__(self, 'Channel',
	[('producer', str),
	 ('products', list),
	 ('location', datastore_types.PostalAddress),
	 ('url', datastore_types.Link),
	 ('tags', list),
	 ('updatable', bool),
	 ])

  def HandlEntity(self, entity):
    entity['tags'] = [db.Category(t) for t in entity['tags']]
    # Make entities searchable.
    ent = search.SearchableEntity(entity)
    return ent

if __name__ == '__main__':
  bulkload.main(ChannelLoader())
