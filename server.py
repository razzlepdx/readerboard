from model import db, connect_to_db, User, Book, Review, Shelf, Challenge
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

connect_to_db(app)

# routes


if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0")