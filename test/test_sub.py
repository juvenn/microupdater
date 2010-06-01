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
    app = TestApp(self.application)
    response = app.get(WORKER['subbub'] 
	+ key
	+ "?hub.mode=" + mode
	+ "&hub.topic=" + topic
	+ "&hub.challenge=" + challenge
	+ "&hub.verify_token=" + token,
	expect_errors=True)
    return response

  def testAllParamsOK(self):
    """Expect 200 OK if all params match.

    Expect hub.challenge.
    """
    challenge = "venus"
    response = self.verify()
    self.assertEqual("200 OK", response.status)
    self.assertEqual(challenge, response.body)
    # Refetch the instance from the datastore, so its attributes
    # get updated. 
    channel = Channel.get(self.channel.key())
    self.assertEqual(channel.status, "subscribed")

  def testVerifyTokenNotMatch(self):
    """Expect 404 Not Found if the verify token not match.

    The (un)subscribe request must be initiated by someone else, or the
    token is broken. Hub will not retry.
    """
    challenge = "venus"
    response = self.verify(token="brokentoken")
    self.assertEqual("404 Not Found", response.status)

  def testCallbackNotMatch(self):
    """Expect 404 Not Found if callback not found.

    The key associated with callback url could not be found in the
    datastore. Hub will not retry.
    """
    challenge = "venus"
    response = self.verify(key="randomekeystring")
    self.assertEqual("404 Not Found", response.status)

  def testTopicNotMatch(self):
    """Expect 404 Not Found if topic not match

    The topic does not match with the record in datastore. Hub will
    not retry.
    """
    challenge = "venus"
    response = self.verify(topic="http://random.dev/atom")
    self.assertEqual("404 Not Found", response.status)

