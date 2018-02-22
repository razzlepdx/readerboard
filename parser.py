import untangle
import requests
import math
import time
import datetime
import distutils
from rauth.service import OAuth1Session
from flask import flash
from model import User, Friendship, Format, Shelf, Book, Edition, db
from helpers import (get_user_by_gr_id,
                     date_is_valid,
                     valid_isbn,
                     valid_page_count)

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
    book["description"] = book_data.description.cdata

    # edition info
    #=============
    book["edition"] = {}
    book["edition"]["isbn"] = valid_isbn(book_data.isbn.cdata.encode("utf8"))
    book["edition"]["format_id"] = get_format_id(book_data.format.cdata.encode("utf8"))
    book["edition"]["pic_url"] = book_data.image_url.cdata.encode("utf8")
    book["edition"]["publisher"] = book_data.publisher.cdata.encode("utf8")
    book["edition"]["num_pages"] = valid_page_count(book_data.num_pages.cdata.encode("utf8"))
    year = date_is_valid(book_data.work.original_publication_year.cdata.encode("utf8"))
    month = date_is_valid(book_data.work.original_publication_month.cdata.encode("utf8"))
    day = date_is_valid(book_data.work.original_publication_day.cdata.encode("utf8"))
    book["edition"]["date"] = datetime.date(year, month, day)
    book["edition"]["gr_url"] = book_data.url.cdata.encode("utf8")
    book["edition"]["gr_id"] = int(book_data.id.cdata.encode("utf8"))

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

#===================
# Books from shelves
#===================



def get_books_page(gr_id, page_num, shelf_name, KEY):
    """ Given a goodreads id, dev key, shelf, and page number, returns the xml response
    and total number of books on a particular shelf for that user. """

    params = {'v': 2, 'key': KEY, 'shelf': shelf_name, 'per_page': 200, 'page': page_num}
    url = 'https://www.goodreads.com/review/list/' + str(gr_id) + ".xml"
    response = requests.get(url, params=params)
    doc = untangle.parse(response.content)
    num_books = int(doc.GoodreadsResponse.reviews['total'])

    return (doc, num_books)


def get_books_from_shelf(gr_id, shelf_name, KEY):
    """ Takes in a user's GR id, the name of a shelf, and dev key, and returns a
    list of book_ids that correspond to that shelf. """

    page_num = 1
    response, num_books = get_books_page(gr_id, page_num, shelf_name, KEY)
    total_pages = int(math.ceil(num_books / float(200)))
    print "******** TOTAL PAGES ARE " + str(total_pages) + "*********"
    print "****** this person is a monster and has", num_books, "books on their", shelf_name, "shelf."
    books = []
    books = make_books_dicts(response, books)

    if total_pages > 1:
        page_num = 2
        while page_num <= total_pages:
            print "*****YOU HAVE MORE BOOKS*****"
            # pause between calls
            time.sleep(1.00)

            # make new request with updated page number here
            response, num_books = get_books_page(gr_id, page_num, shelf_name, KEY)
            books = make_books_dicts(response, books)
            page_num += 1

    create_books_editions(books, gr_id, shelf_name)
    return books


def make_books_dicts(xml, book_list):
    """ Takes in an xml response with up to 200 books and the current book list
    for a particular shelf, and returns the updated book list. """

    books_response = xml.GoodreadsResponse.reviews.review
    for book in books_response:
        a_book = {}
        a_book['title'] = book.book.title.cdata.encode('utf8')
        a_book['author_name'] = book.book.authors.author.name.cdata.encode('utf8')
        a_book['author_gr_id'] = int(book.book.authors.author.id.cdata.encode('utf8'))
        a_book['description'] = book.book.description.cdata

        a_book['edition'] = {}
        a_book['edition']['isbn'] = valid_isbn(book.book.isbn.cdata.encode('utf8'))
        a_book['edition']['format_id'] = get_format_id(book.book.format.cdata.encode('utf8'))
        a_book['edition']['pic_url'] = book.book.image_url.cdata.encode('utf8')
        a_book['edition']['publisher'] = book.book.publisher.cdata.encode('utf8')
        a_book['edition']['gr_url'] = book.book.link.cdata.encode('utf8')
        a_book['edition']['gr_id'] = int(book.book.id.cdata.encode('utf8'))
        year = date_is_valid(book.book.publication_year.cdata.encode("utf8"))
        month = date_is_valid(book.book.publication_month.cdata.encode("utf8"))
        day = date_is_valid(book.book.publication_day.cdata.encode("utf8"))
        a_book['edition']['date'] = datetime.date(year, month, day)
        a_book['edition']['num_pages'] = valid_page_count(book.book.num_pages.cdata.encode('utf8'))
        book_list.append(a_book)

    print "*******THERE ARE " + str(len(book_list)) + " ON THIS SHELF*******"

    return book_list


def create_books_editions(books, gr_id, shelf_name):
    """ Takes in a list of book/edition dictionaries and creates the corresponding
    Book/Edition objects as needed. """

    books_to_shelve = []
    # write query to get shelf_id from gr_id and shelf_name
    user = get_user_by_gr_id(gr_id)
    shelf = db.session.query(Shelf).filter(Shelf.name == shelf_name, Shelf.user == user).one()
    print shelf

    for book in books:
        try:
            # do book title and author_name pairing exist in db?
            book_match = db.session.query(Book).filter(Book.title == book['title'], Book.author_gr_id == book['author_gr_id']).one()
            books_to_shelve.append(book_match.book_id)
            print "book found!  added id to shelving list."
        except:
            # create new Book object
            new_book = Book(title=book['title'],
                            author_name=book['author_name'],
                            author_gr_id=book['author_gr_id'],
                            description=book['description'])
            # add book to db.session
            db.session.add(new_book)
            # print "added new book, " + new_book.title
            # add book_id to books_to_shelve list
            books_to_shelve.append(new_book.book_id)

    # after creating book objects and adding all book_ids to list
    db.session.commit()

    for edition in books:
        # check if edition_gr_id is already in db
        book_match = db.session.query(Book).filter(Book.title == book['title'], Book.author_gr_id == book['author_gr_id']).one()
        try:
            edition_match = db.session.query(Edition).filter(Edition.gr_id == book['edition']['gr_id']).one()
        except:
            new_edition = Edition(format_id=edition['edition']['format_id'],
                                  book_id=book_match.book_id,
                                  isbn=edition['edition']['isbn'],
                                  pic_url=edition['edition']['pic_url'],
                                  publisher=edition['edition']['publisher'],
                                  date=edition['edition']['date'],
                                  gr_url=edition['edition']['gr_url'],
                                  gr_id=edition['edition']['gr_id'],
                                  num_pages=edition['edition']['num_pages'])
            db.session.add(new_edition)
            # print "added new edition for " + new_edition.book.title

    db.session.commit()
    print "DONE"
    add_shelf_books(books_to_shelve, shelf)


def add_shelf_books(books, shelf):
    """ Takes in a list of book_id numbers, and a shelf object, and creates
    Shelfbook objects. """

    for book in books:
        try:
            shelfbook_match = db.session.query(Shelfbook).filter(Shelfbook.book_id==book.book_id, Shelfbook.shelf_id==shelf.shelf_id).one()
            print "This shelfbook already exists!"
        except:
            new_shelfbook = Shelfbook(book_id=book.book_id, shelf_id=shelf.shelf_id)
            db.session.add(new_shelfbook)

    db.session.commit()



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
    a given user. """  # this isn't true - evaluate what needs to be returned tomorrow.

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
