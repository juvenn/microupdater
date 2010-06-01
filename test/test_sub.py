import unittest
from webtest import TestApp
from google.appengine.ext import db
from google.appengine.ext import webapp
from model import WORKER, HUB, Channel
from sub import PushCallback


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
