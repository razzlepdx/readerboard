from model import db, connect_to_db, Account, User
from flask import Flask, render_template, request, session, redirect, flash  # will need jsonify later
from flask_celery import make_celery
import os
from rauth.service import OAuth1Service
from helpers import email_is_valid, pass_is_valid
from parser import book_search_results, get_book_details, get_acct_id, get_user_friends

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'amqp://0.0.0.0//'
app.config['CELERY_BACKEND'] = 'db+postgresql:///readerboard'
app.secret_key = "secretssssssssss"

celery = make_celery(app)

GR_KEY = os.environ["GR_KEY"]
GR_SECRET = os.environ["GR_SECRET"]

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
        return render_template("index.html")

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

    return render_template("index.html", books=books)


@app.route("/book_detail/<book_id>")
def show_book_details(book_id):
    """ Displays details about a book and options to shelve, review, and see
    availability. """

    book = get_book_details(book_id, GR_KEY)

    return render_template("book_detail.html", book=book)

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
    gr_id, gr_url = get_acct_id(acct, GR_KEY, GR_SECRET)
    acct.user.gr_id = gr_id
    acct.user.gr_url = gr_url
    # commit changes to db.
    db.session.commit()

    return redirect("/")


#===============================
# Get friends, shelves and books
#===============================


@app.route("/get_friends")
def get_friends():
    """ Using session data, populates db with user friends. """

    acct = Account.query.get(session["acct"])
    get_user_friends(acct, GR_KEY, GR_SECRET)

    return render_template("index.html", friends=acct.user.friends)


@app.route("/get_shelves/<gr_id>")
def get_shelves(gr_id):
    """ Using account in session, populates db with user's shelves. """
    user = User.query.filter_by(gr_id=gr_id).one()
    get_user_shelves(gr_id, key)

    return render_template("index.html", shelves=user.shelves)
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
    app.run(host="0.0.0.0")
