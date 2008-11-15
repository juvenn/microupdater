#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Update engine of Microupdater

Traverse all channels, check remote server for any updates, fetch from the channel if updates available, parse it by feedparser, and put optional parsednodes to db.

"""

# Import from standard Python library.
import logging
from datetime import datetime, timedelta

# Import from google appengine.
from google.appengine.api import urlfetch

# Universal Feed Parser. Copyright (c) Mark Pilgrim.
# Visit http://feedparser.org
import feedparser
# Import from user-defined modules.
from mudel import Channel, Entry, Featured
from helper import timetuple_dt

# URLFetch timedelta(days, fracseconds, fracmicroseconds). 
# Intended urlfetch.fetch() will be ignored within a FETCH_TD cycle.
FETCH_TD = timedelta(0, 300, 0) 

def sync():
    for chnl in Channel.all().filter("updatable =", True):
	# Check if chnl was urlfetched in last FETCH_TD.seconds.
	tmnow = datetime.utcnow()
	if tmnow-chnl.last_fetch >= FETCH_TD:
	    # Construct etag or last_modifed headers.
	    h = {}
	    if chnl.etag: h["If-None-Match"] = chnl.etag
	    if chnl.last_modified: 
	        h["If-Modified-Since"] = chnl.last_modified

	    try:
	      re = urlfetch.fetch(url=chnl.url, headers=h)
	      chnl.last_fetch = tmnow
	    except InvalidURLError:
	      logging.error("InvalidURLError: %s is invalid. " \
		  "Only http or https allowed.", 
		  chnl.url)
	    except DownloadError:
	      logging.error("DownloadError: " \
		  "attempt to fetch from %s failed.", \
		  chnl.url)
	    except ResponseTooLargeError:
	      logging.error("ResponseTooLargeError: %s", chnl.url)

	    else:
	      if re.status_code == 200:
		pa = feedparser.parse(re.content)

                if pa.feed:
		  try:
		    # Turn the parsed timetuple into datetime type.
		    update_dt = timetuple_dt(pa.feed.updated_parsed)
		  except:
		    # Get the chnl's last build date from 
		    # latest of entries's build date.
		    # Here assumed entry has updated_parsed attribute,
		    # attention should be paid.
		    dts = [e.updated_parsed for e in pa.entries]
		    dts.sort()
		    dts.reverse()
		    update_dt = timetuple_dt(dts[0])

		  if update_dt > chnl.updated:
		    updated_tt = chnl.updated.utctimetuple()
		    update_entries = [e for e in pa.entries \
			if e.updated_parsed > updated_tt]
		    for e in update_entries:
			e_update_dt = timetuple_dt(e.updated_parsed)
			ent = Entry(author = e.get("author"),
			    title=e.title,
			    link=e.link,
			    updated=e_update_dt,
			    channel=chnl)
			# Update entry summary.
			if e.has_key("content"): ent.summary = e.content
			elif e.has_key("summary"): ent.summary = e.summary
		        else: ent.summary = e.title

			ent.put()

		    # Update the chnl.updated datetime.
		    chnl.updated = update_dt

		  # Update etag and modified of the channel.
		  chnl.etag = re.headers.get("etag")
		  chnl.last_modified = re.headers.get("last-modified")

	      # For permanetly removed channel, stop to update. 
	      elif re.status_code == 410:
		chnl.updatable = False
		logging.warning("http status 410: " \
		    "content is permanetly removed from %s.\n" \
		    "Updatable set to false.\n",
		    chnl.url)

	      chnl.put()

	      # Get latest entry for featured channel.
	      # Note that f is a list.
	      f = chnl.featured_set.fetch(1)
	      if f:
	        f[0].latest_entry = chnl.entries.order('-updated')[0] 
