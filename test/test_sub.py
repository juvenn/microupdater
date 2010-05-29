import unittest
from webtest import TestApp
from google.appengine.ext import db
from model import Channel
from sub import WORKER, HUB, PushCallback


class TestVerification(unittest.TestCase):
  """Test Verifications Handling
  
  PubSubHubbub 0.3 Compliant
  """

  def setUp(self):
    self.application = webapp.WSGIApplication([
      (WORKER.subbub + "*",PushCallback)
      ],debug=True)
    ch = Channel(title="Test Channel",
	topic="http://dummychannel.dev/atom",
	status="subscribing") 
    self.channel = Channel.put()

  def test_challenge_code(self):
    app = TestApp(self.application)
    challenge = "venus"
    response = app.get(WORKER.subbub 
	+ self.channel
	+ "?hub.mode=subscribe"
	+ "&hub.topic=" + self.channel.topic
	+ "&hub.challenge=" + challenge
	+ "&hub.verify_token=" + HUB.token)
    self.assertEqual(challenge, response.body)

  def tearDown(self):
    Channel.delete(self.channel)