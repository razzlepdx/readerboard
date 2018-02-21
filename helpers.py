from model import db, connect_to_db, Account, User, Book, Review, Shelf, Challenge
import re

#==================================
# terrible form validation goes here
#==================================


def email_is_valid(email):
    """ Checks user submitted email against db and returns a Boolean. """

    try:
        Account.query.filter_by(email=email).one()

    except:
        return False

    return True


def pass_is_valid(password, email):
    """ Checks user submitted password against db and returns a Boolean. """

    if not email_is_valid(email):
        return False

    acct = Account.query.filter_by(email=email).one()

    if acct.password != password:
        return False

    return True

#====================
# db getter functions
#====================


def get_current_account(acct_id):
    """ Takes in an account id, and returns an account object. """

    acct = Account.query.get(acct_id)

    return acct


def get_user_by_acct(acct):
    """ Takes in an Account object and returns the corresponding User object. """

    return acct.user


def get_user_by_gr_id(gr_id):
    """ Takes in a goodreads id number and returns the corresponding User object."""

    user = User.query.filter_by(gr_id=gr_id).one()

    return user

#=============
# clean up xml
#=============


def clean_xml(problem_text):
    find_brackets = re.compile('<.*?>')
    cleantext = re.sub(find_brackets, ' ', problem_text)
    return cleantext
