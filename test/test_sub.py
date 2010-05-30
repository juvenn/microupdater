import unittest
from webtest import TestApp
from google.appengine.ext import db
from google.appengine.ext import webapp
from model import WORKER, HUB, Channel
from sub import PushCallback


class TestVerification(unittest.TestCase):
  """Test Verifications Handling
  
  PubSubHubbub 0.3 Compliant
  """

  def setUp(self):
    self.application = webapp.WSGIApplication([
      (WORKER['subbub'] + ".*",PushCallback)
      ],debug=True)
    self.channel = Channel(title="Test Channel",
	topic="http://dummychannel.dev/atom",
	status="subscribing") 
    self.channel.put()

  def testVerifySuccess(self):
    """Test verify success"""
    app = TestApp(self.application)
    challenge = "venus"
    response = app.get(WORKER['subbub'] 
	+ str(self.channel.key())
	+ "?hub.mode=subscribe"
	+ "&hub.topic=" + self.channel.topic
	+ "&hub.challenge=" + challenge
	+ "&hub.verify_token=" + HUB['token'])
    self.assertEqual("200 OK", response.status)
    self.assertEqual(challenge, response.body)
    self.assertEqual(self.channel.status, "subscribed")

  def testBadVerifyToken(self):
    """Test bad verify_token

    The (un)subscribe request must be initiated by someone else, or the
    token is broken. Hub should not retry the verification, i.e. 404
    Not Found should be responded.
    """
    app = TestApp(self.application)
    challenge = "venus"
    response = app.get(WORKER['subbub']
	+ str(self.channel.key())
	+ "?hub.mode=subscribe"
	+ "&hub.topic=" + self.channel.topic
	+ "&hub.challenge=" + challenge
	+ "&hub.verify_token=" + "brokentoken")
    self.assertEqual("404 Not Found", response.status)

  def tearDown(self):
    self.channel.delete()
