from model import db, connect_to_db, User, Book, Review, Shelf, Challenge
from flask import Flask, render_template, request, session, redirect, flash  # will need jsonify later
import os
from rauth.service import OAuth1Service, OAuth1Session
from helpers import email_is_valid, pass_is_valid

app = Flask(__name__)
app.secret_key = "secretssssssssss"

connect_to_db(app)

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


@app.route("/")
def landing_page():
    """ Displays user data, or redirects to sign up form. """

    if "user" in session:
        return render_template("index.html")

    else:
        return redirect("/signup")


@app.route("/signup", methods=['GET', 'POST'])
def user_signup():
    """ Displays a signup form for new users. """

    if request.method == "GET":
        return render_template("signup_form.html")

    # this code runs for post requests
    email = request.form.get("email")
    password = request.form.get("password")

    if email_is_valid(email):
        flash("It looks like you are already signed up for Readerboard!  Try signing in instead. ")
        return redirect("/signin")
    else:
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["user"] = new_user.user_id
        return redirect("/auth/goodreads")


@app.route("/signin", methods=['GET', 'POST'])
def user_signin():
    """ Displays a form for users to sign in with an existing account. """

    if request.method == "GET":
        return render_template("signin_form.html")

    #code for post requests to this route
    email = request.form.get("email")
    password = request.form.get("password")

    valid_email = email_is_valid(email)
    valid_pass = pass_is_valid(password, email)

    if valid_email and valid_pass:
        user = User.query.filter_by(email=email).one()
        session["user"] = user.user_id
        flash("Welcome back! You are now signed in.")
        return redirect("/")
    else:
        flash("There was a problem with your login credentials.  Please try signing in again.")
        return redirect("/signin")


@app.route("/auth/goodreads", methods=["POST"])
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

    gr_session = goodreads.get_auth_session(session['request_token'], session['request_token_secret'])
    print gr_session
    ACCESS_TOKEN = gr_session.access_token
    print ACCESS_TOKEN
    ACCESS_TOKEN_SECRET = gr_session.access_token_secret
    print ACCESS_TOKEN_SECRET

    return redirect("/")


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")
