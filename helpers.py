from model import Account, User
from base64 import b64encode, b64decode
from werkzeug.contrib.cache import SimpleCache
import requests
cache = SimpleCache()

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


#===================================
# Overdrive helpers - Setup requests
#===================================


def request_ovr_tkn(key, secret):
    """ Requests a temporary authorization token from Overdrive API """

    dev_keys = key + ":" + secret
    b64_keys = b64encode(dev_keys)
    params = {"grant_type": "client_credentials"}
    r = requests.post('https://oauth.overdrive.com/token',
                      headers={"Authorization": "Basic %s" % b64_keys,
                               "Content-Type": "application/x-www-form-urlencoded"},
                      data=params)
    r = r.json()
    # tkn_type = r["token_type"]  # should always be type "bearer"
    access_tkn = r["access_token"]

    return access_tkn


def check_ovrdrv_token(key, secret):
    """ Checks for valid auth token before submitting Overdrive requests -
    refreshes and resets token with ~ 1hr time limit if not found, and returns
    a valid token. """

    token = cache.get('ovr_tkn')
    if token is None:
        token = request_ovr_tkn(key, secret)
        cache.set('ovr_tkn', token, timeout=60 * 60)  # set cache to expire in 1 hr.

    return token


def get_lib_products(lib_id, key, secret):
    """ """

    token = check_ovrdrv_token(key, secret)
    url = 'https://api.overdrive.com/v1/libraries/' + lib_id

    response = requests.get(url,
                            headers={"User-Agent": "Readerboard",
                                     "Authorization": "Bearer %s" % token,
                                     "Content-Type": "application/json",
                                     "X-Forwarded-For": "0.0.0.0:5000"})
    r = response.json()
    products_url = r["links"]["products"]["href"]

    return products_url

#==============================================
# Search and Availability Overdrive API helpers
#==============================================


def search_lib_for_copies(product_url, book, key, secret):
    """ Accesses the Overdrive Search API endpoint with a query containing the ISBN
    of the book selected by the user. Returns the Availability API endpoint and
    calls the get_availability function. """

    token = check_ovrdrv_token(key, secret)
    url = product_url + "?limit=50&q=" + book['title'] + "&identifiers=" + str(book['edition']['isbn'])
    response = requests.get(url,
                            headers={"User-Agent": "Readerboard",
                                     "Authorization": "Bearer %s" % token,
                                     "Content-Type": "application/json"})
    response = response.json()
    for product in response['products']:
        if product['title'] == book['title']:
            avail_url = product['links']['availability']['href']
            availability = get_lib_availability(avail_url, key, secret)

            return availability

    return None


def get_lib_availability(url, key, secret):
    """ Get availability information for a given book, if any copies are found
    in the library collection. """

    token = check_ovrdrv_token(key, secret)

    response = requests.get(url,
                            headers={"User-Agent": "Readerboard",
                                     "Authorization": "Bearer %s" % token,
                                     "Content-Type": "application/json"})

    response = response.json()
    availability = {"copies": response['copiesOwned'],
                    "available": response['copiesAvailable'],
                    "holds": response['numberOfHolds'],
                    "avail_type": response['availabilityType']}

    return availability
