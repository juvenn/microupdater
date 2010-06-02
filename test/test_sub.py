import unittest
import feedparser
from webtest import TestApp
from google.appengine.ext import db
from google.appengine.ext import webapp
from model import WORKER, HUB, Channel
from sub import PushCallback, ParseWorker


class TestVerification(unittest.TestCase):
  """Verifications Handling Test Cases
  
  PubSubHubbub 0.3 Compliant, async mode only:
  2xx - Verify success, subscription confirmed
  404 - Disagree with the subscription, verify should not be retried
  xxx - Verify temporarily failed, please retry later
  """

  def setUp(self):
    self.application = webapp.WSGIApplication([
      (WORKER['subbub'] + ".*",PushCallback)
      ],debug=True)
    self.channel = Channel(title="Test Channel",
	topic="http://dummychannel.dev/atom",
	status="subscribing") 
    self.channel.put()

  def tearDown(self):
    self.channel.delete()

  def get(self,
          key=None,
	  mode=None,
	  topic=None,
	  challenge=None,
	  token=None):
    """HTTP GET a verify request"""
    url = WORKER['subbub']
    if key: url += key + "?"
    if mode: url += "hub.mode=" + mode
    if topic: url += "&hub.topic=" + topic
    if challenge: url += "&hub.challenge=" + challenge
    if token: url += "&hub.verify_token=" + token
    app = TestApp(self.application)
    return app.get(url, expect_errors=True)

  def verify(self, 
             key=None, 
	     topic=None, 
	     challenge="venus",
             mode="subscribe", 
	     token=HUB["token"]):
    """Simulate a push verify request
    """
    if not key: key = str(self.channel.key())
    if not topic: topic = self.channel.topic
    response = self.get(key=key,
	            mode=mode,
		    topic=topic,
		    challenge=challenge,
		    token=token)
    return response

  def testAllParamsOK(self):
    """Expect 200 OK if all params match.

    Expect hub.challenge.
    """
    challenge = "venus"
    response = self.verify()
    self.assertEqual("200 OK", response.status)
    self.assertEqual(challenge, response.body)
    # Refetch the instance from the datastore, 
    # so its attributes get updated. 
    channel = Channel.get(self.channel.key())
    self.assertEqual(channel.status, "subscribed")

  def testVerifyTokenNotMatch(self):
    """Expect 404 Not Found if the verify token not match.

    The (un)subscribe request must be initiated by someone else, or the
    token is broken. Hub will not retry.
    """
    response = self.verify(token="brokentoken")
    self.assertEqual("404 Not Found", response.status)

  def testCallbackNotMatch(self):
    """Expect 404 Not Found if callback not found.

    The key associated with callback url could not be found in the
    datastore. Hub will not retry.
    """
    response = self.verify(key="randomekeystring")
    self.assertEqual("404 Not Found", response.status)

  def testTopicNotMatch(self):
    """Expect 404 Not Found if topic not match

    The topic does not match with the record in datastore. Hub will
    not retry.
    """
    response = self.verify(topic="http://random.dev/atom")
    self.assertEqual("404 Not Found", response.status)

  def testModeNotMatch(self):
    """Expect 404 Not Found if hub.mode not match
    """
    response = self.verify(mode="unsubscribe")
    self.assertEqual("404 Not Found", response.status)


class TestNotification(unittest.TestCase):
  """Notification Test Cases

  PubSubHubbub 0.3:
  202 - Notification accepted, added to taskqueue
  204 - Ignored, Payload not valid
  2xx - General notify success
  xxx - Fail, please retry the notification later

  "Subscribers SHOULD respond to notifications as quickly as possible;
  their success response code SHOULD only indicate receipt of the
  message, not acknowledgment that it was successfully processed by the
  subscriber." 
    -- Section 7.3, PubSubHubbub Core 0.3
  """
  def setUp(self):
    self.application = webapp.WSGIApplication([
      (WORKER['subbub'] + ".*",PushCallback)
      ],debug=True)
    self.channel = Channel(title="Test Channel",
	topic="http://dummychannel.dev/atom",
	status="subscribed") 
    self.channel.put()
    self.atom = open("test/atom.xml", "r").read()

  def tearDown(self):
    self.channel.delete()

  def notify(self, key, type, body):
    """HTTP POST notification
    """
    app = TestApp(self.application)
    if type == "rss":
      ct = "application/rss+xml" 
    elif type == "atom":
      ct = "application/atom+xml"
    else:
      ct = type
    response = app.post(WORKER["subbub"] + key,
             params=body,
	     content_type=ct,
	     expect_errors=True)
    return response

  def testNotifyAtomAsAtom(self):
    """Expect 202 Accepted if notify atom as atom
    """
    response = self.notify(str(self.channel.key()), "atom", self.atom)
    self.assertEqual("202 Accepted", response.status)

  def testNotifyAtomAsRss(self):
    """Expect 202 Accepted if notify atom as rss

    Success regardless of content-type not match.
    """
    response = self.notify(str(self.channel.key()), "rss", self.atom)
    self.assertEqual("202 Accepted", response.status)

  def testNotifyKeyBroken(self):
    """Expect 204 No Content if the notify key broken

    We do not support aggregated atom feeds for now.
    """
    response = self.notify("brokenkeystring", "atom", self.atom)
    self.assertEqual("204 No Content", response.status)

  def testNotifyKeyMissing(self):
    """Expect 204 No Content if the notify key missing
    """
    response = self.notify("", "atom", self.atom)
    self.assertEqual("204 No Content", response.status)

  def testNotifyEmptyPayload(self):
    """Expect 204 No Content if the notify payload empty
    """
    response = self.notify(str(self.channel.key()), "atom", "")
    self.assertEqual("204 No Content", response.status)

  def testBadContentType(self):
    """Expect 204 No Content if notify content type not match
    """
    response = self.notify(str(self.channel.key()),
	"application/x-www-form-urlencoded",
	self.atom)
    self.assertEqual("204 No Content", response.status)

  def testMissingContentType(self):
    """Expect 204 No Content if notify content type missing
    """
    response = self.notify(str(self.channel.key()), "", self.atom)
    self.assertEqual("204 No Content", response.status)


class TestParseWorker(unittest.TestCase):
  """Parsing task handler test cases
  """

  def setUp(self):
    self.application = webapp.WSGIApplication([
      (WORKER['parser'] + ".*",ParseWorker)
      ],debug=True)
    self.channel = Channel(title="Test Channel",
	topic="http://monica-ping.tumblr.com/rss",
	status="subscribed") 
    self.channel.put()

  def tearDown(self):
    pass

  def testParseAtom(self):
    """Datastore should have updated if everything goes well"""
    app = TestApp(self.application)
    atom = open("test/atom.xml", "r").read()
    doc = feedparser.parse(atom)
    response = app.post(WORKER["parser"] + str(self.channel.key()),
             params=atom,
	     content_type="application/atom+xml")
    channel = Channel.get(self.channel.key())

    self.assertEqual(doc.feed.title, channel.title)
    self.assertEqual(doc.feed.id, channel.uid)
    self.assertEqual(len(doc.entries), channel.entry_set.count())

    for e in doc.entries:
      entry = channel.entry_set.filter("uid =", e.id).get()
      self.assertEqual(e.title, entry.title)
      self.assertEqual(e.id, entry.uid)

  def testParseRecurrentAtom(self):
    """Override entity when an entry being parsed more than once

    The entry existed in the datastore should be updated, instead of
    inserted. We simply assert the counts of the entries not changed.
    """
    app = TestApp(self.application)
    atom = open("test/atom.xml", "r").read()
    doc = feedparser.parse(atom)
    key = self.channel.key()
    response = app.post(WORKER["parser"] + str(key),
             params=atom,
	     content_type="application/atom+xml")
    oldcount = Channel.get(key).entry_set.count()

    # Rework the parsing task
    response = app.post(WORKER["parser"] + str(key),
             params=atom,
	     content_type="application/atom+xml")
    newcount = Channel.get(key).entry_set.count()

    self.assertEqual(oldcount, newcount)
