import os
import logging
from model import (db,
                   connect_to_db,
                   Account,
                   User,
                   Friendship,
                   Shelf,
                   ShelfBook,
                   Edition,
                   Book,
                   Review)
from flask_celery import make_celery

from rauth.service import OAuth1Service, OAuth1Session
from flask import (Flask,
                   render_template,
                   request, session,
                   redirect,
                   flash,
                   jsonify)
from helpers import (email_is_valid,
                     pass_is_valid,
                     get_current_account,
                     get_user_by_acct,
                     check_ovrdrv_token,
                     get_lib_products,
                     search_lib_for_copies,
                     get_library_details,
                     get_challenge_data
                     )

from parser import (book_search_results,
                    get_book_details,
                    get_acct_id,
                    get_user_friends,
                    get_all_shelves,
                    get_all_books_for_user,
                    get_all_books_from_friends
                    )

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://0.0.0.0//'
app.config['CELERY_BACKEND'] = 'db+postgresql:///readerboard'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "secretssssssssss"

celery = make_celery(app)

GR_KEY = os.environ["GR_KEY"]
GR_SECRET = os.environ["GR_SECRET"]
OVRDRV_KEY = os.environ["OVRDRV_KEY"]
OVRDRV_SECRET = os.environ["OVRDRV_SECRET"]
WCCLS = os.environ["WCCLS_ID"]

goodreads = OAuth1Service(
    consumer_key=GR_KEY,
    consumer_secret=GR_SECRET,
    name='goodreads',
    request_token_url='https://www.goodreads.com/oauth/request_token',
    authorize_url='https://www.goodreads.com/oauth/authorize',
    access_token_url='https://www.goodreads.com/oauth/access_token',
    base_url='https://www.goodreads.com/'
    )

#=============
# Landing page
#=============


@app.route("/")
def landing_page():
    """ Displays user data, or redirects to sign up form. """

    print session

    if 'acct' in session:
        acct = get_current_account(session['acct'])
        search = False
        return render_template("index.html", acct=acct, search=search)

    else:
        return redirect("/signup")

#==================================
# signup, signin, and logout routes
#==================================


@app.route("/signup", methods=['GET', 'POST'])
def user_signup():
    """ Displays a signup form for new users. """

    if request.method == "GET":
        return render_template("signup_form.html")

    # post request logic starts here
    email = request.form.get("email")
    password = request.form.get("password")

    if email_is_valid(email):

        flash("It looks like you are already signed up for Readerboard!  Try signing in instead.")
        return redirect("/signin")

    else:

        new_user = User()
        db.session.add(new_user)
        db.session.commit()
        new_acct = Account(user_id=new_user.user_id, email=email, password=password)
        db.session.add(new_acct)

        db.session.commit()
        session['acct'] = new_acct.acct_id

        return redirect("/auth/goodreads")


@app.route("/signin", methods=['GET', 'POST'])
def user_signin():
    """ Displays a form for users to sign in with an existing account. """

    if request.method == "GET":
        return render_template("signin_form.html")

    # post request logic starts here
    email = request.form.get("email")
    password = request.form.get("password")

    valid_email = email_is_valid(email)
    valid_pass = pass_is_valid(password, email)

    if valid_email and valid_pass:
        acct = Account.query.filter_by(email=email).one()
        session["acct"] = acct.acct_id
        flash("Welcome back! You are now signed in.")
        return redirect("/")
    else:
        flash("There was a problem with your login credentials.  Please try signing in again.")
        return redirect("/signin")


@app.route("/logout")
def logout_user():
    """ Removes user from session and redirects to login page. """

    session.clear()

    return redirect("/")
#===========================================
# book search results and book detail routes
#===========================================


@app.route("/book_search", methods=["POST"])
def search_book():
    """ Processes a user's book search from main search bar and displays results. """

    title = request.form.get("search")
    books = book_search_results(GR_KEY, title)
    acct = get_current_account(session['acct'])
    search = True

    return render_template("index.html", books=books, acct=acct, search=search)


@app.route("/book_detail/<book_id>")
def show_book_details(book_id):
    """ Displays details about a book and options to shelve, review, and see
    availability. """

    book = get_book_details(book_id, GR_KEY)
    acct = get_current_account(session["acct"])
    user = get_user_by_acct(acct)
    # query to get all friends of the current user that have read any edition of
    # the currently displayed book.
    friend_matches = db.session.query(Shelf, Edition, ShelfBook, Friendship) \
        .filter(Friendship.user_id == user.user_id) \
        .filter(Shelf.user_id == Friendship.friend_id) \
        .filter(ShelfBook.shelf_id == Shelf.shelf_id) \
        .filter(ShelfBook.ed_id == Edition.ed_id) \
        .filter(Edition.book_id == Book.book_id) \
        .filter(Book.gr_work_id == book['work_id'])\
        .all()

    matches = set()  # create set to prevent duplicate matches (caused by rereading)

    if friend_matches:
        for match in friend_matches:
            user = User.query.get(match.Shelf.user_id)
            matches.add((user.image_url, user.gr_name, match.Shelf.name, user.gr_url))

    matches = list(matches)  # cast matches to a list for iteration in html
    PRODUCT_URL = get_lib_products(WCCLS, OVRDRV_KEY, OVRDRV_SECRET)
    lib_copies = search_lib_for_copies(PRODUCT_URL, book, OVRDRV_KEY, OVRDRV_SECRET)

    return render_template("book_detail.html",
                           book=book,
                           acct=acct,
                           user=user,
                           matches=matches,
                           lib_copies=lib_copies)


#====================
# Shelf detail routes
#====================


@app.route("/view_shelf", methods=['POST'])
def view_user_shelf():
    """ Responds to post request from landing page form and renders a list of
    all books on the selected shelf for an authorized user. """

    # FIXME - running into encoding errors with certain shelves - WHY?
    shelf_name = request.form.get('shelf')
    acct = get_current_account(session['acct'])
    user = get_user_by_acct(acct)
    shelf = db.session.query(Shelf).filter(Shelf.name == shelf_name, Shelf.user_id == user.user_id).first()
    shelfbooks = shelf.editions

    return render_template("index.html", acct=acct, search=False, shelfbooks=shelfbooks)

#==================================
# Routes for initial OAuth approval
#==================================


@app.route("/auth/goodreads", methods=["GET"])
def get_oauth():
    """ Processes signup form and makes request for GR user authorization token. """

    # initial app authorization request - not tied to specific user
    request_token, request_token_secret = goodreads.get_request_token(header_auth=True)

    # assign request tokens to session for future use
    session['request_token'] = request_token
    session['request_token_secret'] = request_token_secret

    # url takes user to Goodreads and presents them with option to authorize readerboard
    authorize_url = goodreads.get_authorize_url(request_token)

    # send user to goodreads
    return redirect(authorize_url)


@app.route("/auth/goodreads/callback", methods=['GET', 'POST'])
def get_oauth_token():
    """ Callback URL for goodreads oauth process. """

    # make a request to goodreads authorization url, and pass in request tokens
    gr_session = goodreads.get_auth_session(session['request_token'],
                                            session['request_token_secret'])

    ACCESS_TOKEN = gr_session.access_token
    ACCESS_TOKEN_SECRET = gr_session.access_token_secret

    # add OAuth tokens to Account object.
    acct = Account.query.get(session["acct"])
    acct.access_token = ACCESS_TOKEN
    acct.access_token_secret = ACCESS_TOKEN_SECRET
    # get goodreads ID and url for a user and assign to user record.
    gr_id, gr_url, name, image_url = get_acct_id(acct, GR_KEY, GR_SECRET)
    acct.user.gr_id = gr_id
    acct.user.gr_url = gr_url
    acct.user.gr_name = name
    acct.user.image_url = image_url
    # commit changes to db.
    db.session.commit()

    return redirect("/")

#=========================
# Submit information to GR
#=========================


@app.route("/shelve_book", methods=['POST'])
def shelve_book_on_gr():
    """ Creates a post request to Goodreads so that the user-selected book can
    be added to their shelves, both within Readerboard and on GR. """

    acct = get_current_account(session['acct'])
    book_id = request.form.get('book')
    shelf = request.form.get('shelf')

    url = 'https://www.goodreads.com/shelf/add_to_shelf.xml'
    params = {'name': shelf, 'book_id': book_id}

    gr_session = OAuth1Session(
        consumer_key=GR_KEY,
        consumer_secret=GR_SECRET,
        access_token=acct.access_token,
        access_token_secret=acct.access_token_secret,
    )

    shelf_request = gr_session.post(url, data=params)

    # TODO: Create a book/edition/shelfbook object and add them to db.
    # book = get_book_details(book_id, GR_KEY)
    # create_books_editions([book], acct.user.gr_id, GR_KEY)

    flash("A book has been added to your " + shelf + " shelf!")
    return render_template("index.html", acct=acct, search=False)

# FIXME - review submission on hold while finishing styling
# @app.route("/review_book", methods=['POST'])
# def submit_book_review():
#     """ Takes in user submitted review data, creates a new Review object, and when
#     appropriate, submits a review to GR. """

#     acct = get_current_account(session['acct'])
#     user = acct.user

#     book = get_book_details(request.form.get('book'), GR_KEY)

#     text = request.form.get('text')
#     rating = request.form.get('star_rating')
#     start_read = make_datetime(request.form.get('start_read'))
#     end_read = make_datetime(request.form.get('end_read'))
#     private = review_is_private(request.form.get('private'))

#     # TODO: add challenge points functionality here

#     new_review = Review(user_id=user.user_id,
#                         book_id=int(book_id),
#                         text=text,
#                         star_rating=int(rating),
#                         start_read_date=start_read,
#                         end_read_date=end_read,
#                         private=private)

#     db.session.add(new_review)
#     print new_review
#     db.session.commit()

#     return redirect("/book_detail/" + book_id)


#===============================
# Get friends, shelves and books
#===============================


@app.route("/get_friends")
def get_friends():
    """ Using session data, populates db with user friends. """

    acct = get_current_account(session["acct"])
    get_user_friends(acct, GR_KEY, GR_SECRET)
    search = False

    return render_template("index.html", acct=acct, search=search)


@app.route("/get_shelves/<gr_id>")
def get_shelves(gr_id):
    """ Using account in session, populates db with user's shelves. """

    acct = get_current_account(session['acct'])  # send current account for template
    # user = get_user_by_gr_id(gr_id)
    get_all_shelves(gr_id, GR_KEY)
    search = False
    return render_template("index.html", acct=acct, search=search)


@app.route("/get_books")
def get_books():
    """ Using account in session, populates db with all books from the current
    user's shelves. """

    acct = get_current_account(session['acct'])
    user = get_user_by_acct(acct)
    search = False
    get_all_books_for_user(user, GR_KEY)

    return render_template("index.html", acct=acct, search=search)


@app.route("/get_friend_books")
def get_friend_books():
    """ Using the account data from the session, populates db with books for each
    friend in the user's friend list. """

    acct = get_current_account(session['acct'])
    user = get_user_by_acct(acct)
    search = False

    get_all_books_from_friends(user, GR_KEY, GR_SECRET)
    flash("imported all books from your friends!")

    return render_template("index.html", acct=acct, search=search)

#==============================
# Library Selection and Details
#==============================


@app.route("/library", methods=['GET', 'POST'])
def display_library_details():
    """ Displays a page for users to select and view details about their home
    library system. """

    acct = get_current_account(session['acct'])
    if request.method == "POST":
        # post request response goes here
        library = request.form.get("library_id")
        session['lib'] = library
        flash("Thanks for selecting your library system!")
        return redirect("/library")

    else:
        if 'lib' in session:
            lib = session['lib']
            library = get_library_details(lib, OVRDRV_KEY, OVRDRV_SECRET)

        else:
            library = None

        return render_template("library_info.html", library=library, acct=acct)

#===========================
# User Challenge Detail Page
#===========================


@app.route('/challenges', methods=['GET', 'POST'])
def display_chal_info():
    """ Displays user specific info about current challenges, and allows
    a user to create new personal reading challenges. """

    acct = get_current_account(session['acct'])
    user = acct.user

    if request.method == "POST":
        flash("New challenge created!")
        return redirect("/")

    return render_template("challenges.html", user=user, acct=acct)


@app.route("/challenge-progress/<ch_id>.json")
def display_challenge_graphs(ch_id):
    """ Returns data about user challenge progress. """

    acct = get_current_account(session['acct'])
    user = acct.User
    challenge_data = get_challenge_data(ch_id, user)

    return jsonify(challenge_data)
#=============
# Celery Tasks
#=============


@celery.task(name="server.hello_world")
def hello_world():
    """ Tests celery integration and returns 'Hello, world' """

    return "Hello World"

#========
# run app
#========

if __name__ == "__main__":

    app.debug = True
    connect_to_db(app)

    # logger setup
    logging.basicConfig(filename='error.log', level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # run app, populate cache with temp token
    app.run(host="0.0.0.0")
    check_ovrdrv_token(OVRDRV_KEY, OVRDRV_SECRET)
