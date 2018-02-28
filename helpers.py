from model import Account, User


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


def date_is_valid(xml):
    """ Takes in a piece of XML and returns an int/default value to be used as
    part of a book's publishing date. """

    try:
        date = int(xml)
    except:
        date = 1

    return date


def valid_isbn(xml):
    """ Takes in an ISBN xml value and returns an int, or None if no ISBN was found. """

    try:
        isbn = int(xml)
    except:
        isbn = None

    return isbn


def valid_page_count(xml):
    """ Takes in page count and returns an int or default value. """

    try:
        page_count = int(xml)
    except:
        page_count = 0

    return page_count

