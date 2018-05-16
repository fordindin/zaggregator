import unittest
from fuzzywuzzy import fuzz, StringMatcher
import zaggregator.procbundle as procbundle
import psutil
import os, sys
from multiprocessing import Process
import time
import random, string

from zaggregator import tests

class TestProcBundle(unittest.TestCase):

    def test_ProcessBundle(self):
        pass


if __name__ == '__main__':
    unittest.main()
