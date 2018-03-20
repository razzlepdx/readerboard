import unittest

from server import app
# from model import db, connect_to_db, User, Account


class UserSignUpTests(unittest.TestCase):
    "Tests for a new user to Readerboard."

    def setUp(self):
        """setup actions for all tests in this class."""

        self.client = app.test_client()
        app.config["TESTING"] = True

    def testHomePage(self):
        """ Tests that an unauthorized user is redirected to signup page. """
        result = self.client.get('/', follow_redirects=True)
        self.assertIn("Enter your email here", result.data)
        self.assertNotIn("Search Goodreads", result.data)

if __name__ == "__main__":
    unittest.main()
