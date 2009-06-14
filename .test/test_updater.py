#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#

"""Test Module for Updater"""

import unittest
from datetime import datetime
import updater

class TestDataStore(unittest.TestCase):
  pass

class TestMethods(unittest.TestCase):
  def setUp(self):
    u = updater.Updater(key_name="test_url",
	url="")
    self.u = u.put()

  def tearDown(self):
    self.u.delete()

  def testLast_fetched(self):
    self.assertEqual(datetime, type(self.u.last_fetched),
	"last_fetched should return datetime object")

  def testFetch(self):
    response = self.u.fetch()
    self.assertEqual("200", response.status_code)
    self.assertEqual(1, response.content.find("<feed"),
	"fetched content should be in feed format")
