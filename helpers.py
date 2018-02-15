from model import db, connect_to_db, User, Book, Review, Shelf, Challenge


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
