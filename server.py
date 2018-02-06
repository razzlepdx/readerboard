from model import db, connect_to_db, User, Book, Review, Shelf, Challenge
from flask import Flask, render_template, request, session, redirect, jsonify
import os


app = Flask(__name__)
app.secret_key = "secretssssssssss"

connect_to_db(app)

GR_KEY = os.environ["GR_KEY"]
GR_SECRET = os.environ["GR_SECRET"]


@app.route("/")
def landing_page():
    """ Prompts user to authorize GR account, or, if already in session, displays user data.  """

    # session["user"] = "wejrklejkslajfkele;wrjaekls;f"

    return render_template("index.html")


@app.route("/auth/goodreads/callback", methods=['GET', 'POST'])
def get_oauth():
    """ Callback URL for goodreads oauth process. """

    return None


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")
