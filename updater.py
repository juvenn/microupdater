#!/usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Update engine of Microupdater

Traverse all channels, check remote server for any updates, fetch from the channel if updates available, parse it by feedparser, and put optional parsednodes to db.

"""

# Import from standard Python library.
from datetime import datetime, timedelta

# Import from google appengine.
from google.appengine.api import urlfetch

# Universal Feed Parser. Copyright (c) Mark Pilgrim.
# Visit http://feedparser.org
import feedparser
# Import from user-defined modules.
from dbmodel import Channel, Entry
from helper import timetuple_dt

# URLFetch timedelta(days, fracseconds, fracmicroseconds). Intended urlfetch.fetch() will be ignored within a FETCH_TD cycle.
FETCH_TD = timedelta(0, 300, 0) 
# The number of character truncated in entry.summary
CONTENT_TRUNC = 200 

def sync():
    for chnl in Channel.all().filter("is_approved =", True):
	# Check if chnl was urlfetched in last FETCH_TD.seconds.
	tmnow = datetime.utcnow()
	if tmnow-chnl.last_fetch >= FETCH_TD:
	    # Construct etag or last_modifed headers.
	    h = {}
	    if chnl.etag: h["If-None-Match"] = chnl.etag
	    if chnl.last_modified: 
	        h["If-Modified-Since"] = chnl.last_modified
	    re = urlfetch.fetch(url=chnl.link, headers=h)
			
	    # Parse the fetched content.
	    if re.status_code == 200:
		pa = feedparser.parse(re.content)

		# Turn the parsed timetuple into datetime type.
		updated_dt = timetuple_dt(pa.entries[0].updated_parsed)

		# Update db if updates available.
		if updated_dt > chnl.updated:
		    # Put updated entries into db. 
		    updated_entries = [e for e in pa.entries if e.updated_parsed > chnl.updated.utctimetuple()]
		    for e in updated_entries:
			e_updated_dt = timetuple_dt(e.updated_parsed)
			ent = Entry(title=e.title,
				link=e.link,
				updated=e_updated_dt,
				channel=chnl.key())
			# Feed may have no author attribute (e.g.twitter).
			ent.author = e.get("author")
			# Update entry summary.
			if e.has_key("content"): ent.summary = e.content
			elif e.has_key("summary"): ent.summary = e.summary

			ent.put()

		    # Update the chnl.updated datetime.
		    chnl.updated = updated_dt

		# Update etag and modified of the channel.
		chnl.etag = re.headers.get("etag")
		chnl.last_modified = re.headers.get("last-modified")

	    # For permanetly removed channel, stop to update. 
	    # TODO: notify admin for channel update.
	    elif re.status_code == 410:
		chnl.is_approved = False

	chnl.last_fetch = tmnow
	chnl.put()
