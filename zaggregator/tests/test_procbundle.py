import unittest
from fuzzywuzzy import fuzz, StringMatcher
import zaggregator.procbundle as procbundle
import psutil
import os, sys
from multiprocessing import Process
import time
import random, string

from zaggregator import tests

class TestProcBundle(tests.TestCase):

    def test_ProcessBundle(self):
        pass

if __name__ == '__main__':
    run_test_module_by_name(__file__)
