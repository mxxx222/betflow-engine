"""
Test module for the main application.
"""

import os
import sys
import unittest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import greet


class TestMain(unittest.TestCase):
    """Test cases for main module functionality."""
    
    def test_greet_with_name(self):
        """Test greeting with a specific name."""
        result = greet("Developer")
        expected = "Hello, Developer! Ready to work with Flipper RF tools?"
        self.assertEqual(result, expected)
    
    def test_greet_without_name(self):
        """Test greeting without a name."""
        result = greet()
        expected = "Hello! Ready to work with Flipper RF tools?"
        self.assertEqual(result, expected)
    
    def test_greet_with_none(self):
        """Test greeting with None as name."""
        result = greet(None)
        expected = "Hello! Ready to work with Flipper RF tools?"
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()