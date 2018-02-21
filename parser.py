import untangle
import requests
import math
import time
import datetime
import distutils
from rauth.service import OAuth1Session
from flask import flash
from model import User, Friendship, Format, Shelf, db
from helpers import get_user_by_gr_id, clean_xml

#==================================
# Book search/book details requests
#==================================


def book_search_results(key, title):
    """Parses xml data from book.search call, and returns a list of book objects to display."""

    payload = {"key": key, "q": title}
    query = requests.get("https://www.goodreads.com/search.xml", params=payload)

    doc = untangle.parse(query.content)

    results = doc.GoodreadsResponse.search.results

    books = []

    if len(results) > 0:
        for work in results.work:
            book = {}

            book['title'] = work.best_book.title.cdata.encode('utf8')
            book['book_id'] = int(work.best_book.id.cdata.encode('utf8'))
            book['author_id'] = int(work.best_book.author.id.cdata.encode('utf8'))
            book['author_fname'] = work.best_book.author.name.cdata
            book['image_url'] = work.best_book.image_url.cdata.encode('utf8')
            books.append(book)

    return books


def get_book_details(book_id, key):
    """ Takes in a Goodreads book id and returns a Book object. """

    # call goodreads search method with book id here
    payload = {"key": key}

    query = requests.get("https://www.goodreads.com/book/show/{}.json".format(book_id), params=payload)
    # parse response to get data needed to create a book object

    doc = untangle.parse(query.content)
    book_data = doc.GoodreadsResponse.book
    book = {}

    # create dictionary of book object data, subdictionary of edition data

    # book info
    #==========
    book["title"] = book_data.title.cdata.encode("utf8")
    book["author_name"], book["author_gr_id"] = get_author_data(book_data.authors)
    book["description"] = clean_xml(book_data.description.cdata)

    # edition info
    #=============
    book["edition"] = {}
    book["edition"]["ed_id"] = book_data.isbn.cdata.encode("utf8")
    book["edition"]["format_id"] = get_format_id(book_data.format.cdata.encode("utf8"))
    book["edition"]["pic_url"] = book_data.image_url.cdata.encode("utf8")
    book["edition"]["publisher"] = book_data.publisher.cdata.encode("utf8")
    book["edition"]["num_pages"] = book_data.num_pages.cdata.encode("utf8")
    year = int(book_data.work.original_publication_year.cdata.encode("utf8"))
    month = int(book_data.work.original_publication_month.cdata.encode("utf8"))
    day = int(book_data.work.original_publication_day.cdata.encode("utf8"))
    book["edition"]["date"] = datetime.date(year, month, day)
    book["edition"]["gr_url"] = book_data.url.cdata.encode("utf8")
    book["edition"]["gr_id"] = book_data.id.cdata.encode("utf8")

    return book


def get_format_id(gr_format):
    """ Takes in a goodreads assigned format and returns an integer - format ID."""

    try:
        format = Format.query.filter_by(book_format=gr_format).one()
    except:
        format = Format(book_format=gr_format)
        db.session.add(format)
        db.session.commit()

    return format.format_id


def get_author_data(authors):
    """ Takes in author data from GR and returns the name of a single author. """

    try:
        author = authors.author.name.cdata.encode("utf8")
        author_id = int(authors.author.id.cdata.encode("utf8"))
    except:  # FIXME: running into errors when book has multiple authors
        author = authors.author[0].cdata.encode("utf8")
        author_id = authors.author[0].cdata.encode("utf8")

    return (author, author_id)

#======================
# User account requests
#======================


def get_acct_id(acct, KEY, SECRET):
    """ Takes in an account and developer keys and returns a list containing
    the goodreads id and url for the requested user. """

    new_gr_session = OAuth1Session(
        consumer_key=KEY,
        consumer_secret=SECRET,
        access_token=acct.access_token,
        access_token_secret=acct.access_token_secret,
    )

    response = new_gr_session.get('https://www.goodreads.com/api/auth_user')

    doc = untangle.parse(response.content)
    response = doc.GoodreadsResponse.user
    gr_id = int(response["id"].encode('utf8'))
    gr_url = response.link.cdata.encode('utf8')

    return [gr_id, gr_url]

#=========================
# Shelves related requests
#=========================


def get_shelves_query(user_id, key):
    """ Makes a request to GR API for a user's shelves and returns the parsed response. """

    url = 'https://www.goodreads.com/shelf/list.xml'
    params = {"user_id": user_id, "key": key}
    query = requests.get(url, params=params)
    response = untangle.parse(query.content)

    return response


def get_all_shelves(gr_id, KEY):
    ''' Requests all shelves from GR for an authorized user. '''

    response = get_shelves_query(gr_id, KEY)
    # total is needed for testing purposes only TODO: DELETE THIS LATER
    total_shelves = response.GoodreadsResponse.shelves['total']
    print "*****you have this many shelves, you dummo: " + total_shelves

    shelves = response.GoodreadsResponse.shelves.user_shelf
    shelf_url_base = 'https://www.goodreads.com/review/list/'
    query_param = '?shelf='

    for shelf in shelves:
        a_shelf = {}
        a_shelf['gr_id'] = int(shelf.id.cdata.encode('utf8'))
        a_shelf['name'] = shelf.name.cdata.encode('utf8')
        a_shelf['gr_url'] = (shelf_url_base + str(gr_id) + query_param + a_shelf['name']).encode('utf8')
        a_shelf['exclusive'] = shelf.exclusive_flag.cdata.encode('utf8')
        create_shelf(gr_id, a_shelf)

    db.session.commit()
    print "ADDED SOME SHELVES TO THE DB OR SOMETHING"


def create_shelf(gr_id, shelf):
    ''' Creates an individual shelf object for an account. '''
    exclusive = distutils.util.strtobool(shelf['exclusive'])
    user = get_user_by_gr_id(gr_id)
    print exclusive
    new_shelf = Shelf(user_id=user.user_id,
                      gr_shelf_id=shelf['gr_id'],
                      name=shelf['name'],
                      gr_url=shelf['gr_url'],
                      exclusive=exclusive
                      )

    db.session.add(new_shelf)


# get books on a shelf
# FIXME:  THIS IS STILL BROKEN
def get_books_from_shelf(gr_id, KEY):
    """ Takes in a user's GR id, the name of a shelf, and dev key, and returns a
    list of book_ids that correspond to that shelf. """

    params = {'v': 2, 'key': KEY, 'per_page': 200, 'page': 1}
    url = 'https://www.goodreads.com/review/list/' + str(gr_id) + ".xml"
    response = requests.get(url, params=params)
    doc = untangle.parse(response.content)

    # print "****** total is: " + total
    num_pages = doc.GoodreadsResponse.books['numpages']
    print "****** this person is a monster and has " + num_pages + " of books."
    books = doc.GoodreadsResponse.books
    for book in books:
        print book.title.cdata.encode('utf8')



#=========================
# Friends related requests
#=========================


def get_friends_page(session, user_id, page):
    """ Returns a tuple with the total number of friends and the xml response. """

    url = 'https://www.goodreads.com/friend/user'
    params = {'id': user_id, 'format': 'xml', 'page': page}
    response = session.get(url, params=params)

    doc = untangle.parse(response.content)
    total = int(doc.GoodreadsResponse.friends['total'])
    friends = doc.GoodreadsResponse.friends

    return (total, friends)


def get_user_friends(acct, KEY, SECRET):
    """ Takes in an account and developer keys and returns a list of friends for
    a given user. """

    new_gr_session = OAuth1Session(
        consumer_key=KEY,
        consumer_secret=SECRET,
        access_token=acct.access_token,
        access_token_secret=acct.access_token_secret
    )

    user_id = str(acct.user.gr_id)
    current_page = 1

    total, friends = get_friends_page(new_gr_session, user_id, current_page)

    # check for no friends first
    if len(friends) == 0:
        flash("No Goodreads friends found.")
        print "No friends!"

    # friends requests return a list of 30 at a time
    # get total number of pages required.
    total_pages = int(math.ceil(total / float(30)))
    # creates new users and adds friendship relationships to db
    add_user_friendships(friends, acct)

    # check for more than 30 friends
    if total_pages > 1:

        current_page = 2
        while current_page <= total_pages:

            print "******YOU HAVE MORE FRIENDS*******"

            # wait 1 second between calls, per GR policy
            time.sleep(1.00)
            # create new query with updated current_page
            total, friends = get_friends_page(new_gr_session, user_id, current_page)
            add_user_friendships(friends, acct)
            current_page += 1

    return None


def add_user_friendships(friend_page, acct):
    """ Creates new users and adds friendships with existing accounts based on GR_id"""

    friends_list = []  # becomes a list of User objects

    for friend in friend_page.user:  # loops over page of 30 friends
        gr_id = int(friend.id.cdata.encode('utf8'))
        gr_url = friend.link.cdata.encode('utf8')

        try:
            # if user is already in db, add friendship only
            existing_user = User.query.filter_by(gr_id=gr_id).one()
            friends_list.append(existing_user)
        except:
            new_user = User(gr_id=gr_id, gr_url=gr_url)
            db.session.add(new_user)
            print "added new friend: " + friend.name.cdata.encode('utf8')
            friends_list.append(new_user)

    print friends_list
    db.session.commit()

    # after adding missing users to db, add friendship between authorized account
    # and all friends
    for friend in friends_list:

        new_friend = Friendship(user_id=acct.user.user_id, friend_id=friend.user_id)
        old_friend = Friendship(user_id=friend.user_id, friend_id=acct.user.user_id)
        db.session.add(new_friend)
        db.session.add(old_friend)
        print "Added friendship!"

    db.session.commit()
