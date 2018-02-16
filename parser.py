import untangle
import requests
import math
import time
from rauth.service import OAuth1Session

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
    results = doc.GoodreadsResponse.search.results

    print results


    # book
    #=====
    # book_id
    # title
    # author name
    # author_gr_id


    # edition
    #========
    # ed_id = ISBN
    # format_id
    # book_id
    # pic_url
    # publisher
    # num_pages
    # date
    # gr_id

    # create dictionary of book object data, subdictionary of edition data

    # return book

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
    url = 'https://www.goodreads.com/friend/user'
    params = {'id': user_id, 'format': 'xml', 'page': current_page}
    response = new_gr_session.get(url, params=params)

    # print response.content
    doc = untangle.parse(response.content)
    total = int(doc.GoodreadsResponse.friends['total'])
    # friends requests return a list of 30 at a time
    # get total number of pages required.
    total_pages = int(math.ceil(total / float(30)))

    # add_user_friends(friends, acct)
    if total_pages > 1:
        for i in range(2, total_pages + 1):

            current_page = i
            # wait 1 second between calls, per GR policy
            time.sleep(1.00)
            # create new query with updated current_page
            new_query = new_gr_session.get(url, params=params)
            # parse response
            doc = untangle.parse(new_query.content)
            friends = doc.GoodreadsResponse.friends

            for user in friends.user:
                print user.id.cdata.encode('utf8')
                print user.link.cdata.encode('utf8')
