from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Account(db.Model):
    """ Account model. """

    __tablename__ = "accounts"

    acct_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(30), nullable=False)
    access_token = db.Column(db.String(100), nullable=True)
    access_token_secret = db.Column(db.String(100), nullable=True)

    user = db.relationship("User", backref="account")

    def __repr__(self):
        """ Provides helpful info when printing an Account object. """

        return "<Account acct_id={}, email={}, user_id={}>".format(self.acct_id,
                                                                   self.email,
                                                                   self.user_id)


class User(db.Model):
    """ User model. """

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    gr_url = db.Column(db.String(150), nullable=True)
    gr_id = db.Column(db.Integer, nullable=True)

    friends = db.relationship("User",  # have to add in both directions - 2 adds to db for each friendship
                              secondary="friendships",
                              primaryjoin="User.user_id==Friendship.user_id",
                              secondaryjoin="User.user_id==Friendship.friend_id")

    def __repr__(self):
        """ Provides helpful info when printing a User object. """

        return "<User user_id={}, gr_id={}>".format(self.user_id,
                                                    self.gr_id)


class Friendship(db.Model):
    """ Friendship association table. """

    __tablename__ = "friendships"

    friendship_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)


class Book(db.Model):
    """ Book model. """

    __tablename__ = "books"

    book_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author_fname = db.Column(db.String(25), nullable=True)
    author_lname = db.Column(db.String(25), nullable=True)
    author_gr_id = db.Column(db.Integer, unique=True, nullable=False)

    def __repr__(self):
        """ Provides helpful info when printing a Book object. """

        return "<Book book_id={}, title={}, author={} {}>".format(self.book_id,
                                                                  self.title,
                                                                  self.author_fname,
                                                                  self.author_lname)


class Review(db.Model):
    """ Review model. """

    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    text = db.Column(db.UnicodeText, nullable=True)
    star_rating = db.Column(db.Integer, nullable=True)
    review_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_read_date = db.Column(db.DateTime, nullable=True)
    end_read_date = db.Column(db.DateTime, nullable=True)
    gr_url = db.Column(db.String(150), unique=True, nullable=True)  # TODO: find out if this returns URL
    private = db.Column(db.Boolean, default=False, nullable=False)

    book = db.relationship("Book", backref="reviews")
    user = db.relationship("User", backref="reviews")

    def __repr__(self):
        """ Provides helpful info when printing a Review object. """

        return "<Review review_id={}, book={}, user={}, stars={}, private={}>".format(self.review_id,
                                                                                      self.book.name,
                                                                                      self.user_id,
                                                                                      self.star_rating,
                                                                                      self.private)


class Shelf(db.Model):
    """ Shelf model. """

    __tablename__ = "shelves"

    shelf_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    gr_url = db.Column(db.String(150), nullable=True)  # TODO find out about this
    exclusive = db.Column(db.Boolean, default=False, nullable=False)

    books = db.relationship("Book", secondary="shelfbooks")
    user = db.relationship("User", backref="shelves")

    def __repr__(self):
        """ Provides helpful info when printing a Shelf object. """

        return "<Shelf shelf_id={}, name={}, user_id={}, exclusive={}>".format(self.shelf_id,
                                                                               self.name,
                                                                               self.user_id,
                                                                               self.exclusive)


class ShelfBook(db.Model):
    """ Shelf-Book association table. """

    __tablename__ = "shelfbooks"

    shelf_book_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    shelf_id = db.Column(db.Integer, db.ForeignKey("shelves.shelf_id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)

    def __repr__(self):
        """ Provides helpful info when printing a shelfbook object. """

        return "<Shelfbook s_b_id={}, shelf={}, book={}>".format(self.shelf_book_id,
                                                                 self.shelf.name,
                                                                 self.book.title)


class Challenge(db.Model):
    """ Challenge model. """

    __tablename__ = "challenges"

    chal_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.UnicodeText, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    goal_num = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", backref="challenges")
    books = db.relationship("Book",
                            primaryjoin='Challenge.chal_id == ChallengePoint.chal_id',
                            secondary='join(ChallengePoint, Review, ChallengePoint.review_id == Review.review_id)',
                            secondaryjoin='Review.book_id == Book.book_id',
                            viewonly=True,
                            backref=db.backref("challenges"))

    def __repr__(self):
        """ Provides helpful info when printing a Challenge object. """

        return "<Challenge chal_id={}, name={}, user={}, goal_num={}>".format(self.chal_id,
                                                                              self.name,
                                                                              self.user.name,
                                                                              self.goal_num)


class ChallengePoint(db.Model):
    """ ChallengePoints model. """

    __tablename__ = "challengepoints"

    c_p_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    chal_id = db.Column(db.Integer, db.ForeignKey("challenges.chal_id"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.review_id"), nullable=False)

    challenge = db.relationship("Challenge", backref="challenge_points")
    # review = db.relationhip("Review", backref="challenge_points")

    def __repr__(self):
        """ Provides helpful info when printing a ChallengePoint object. """

        return "<ChallengePoint c_p_id={}, challenge={}, user_id={}>".format(self.c_p_id,
                                                                             self.challenge.name,
                                                                             self.user_id)


class Format(db.Model):
    """ Format model. """

    __tablename__ = "formats"

    format_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_format = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        """ Provides helpful info when printing a Format object. """

        return "<Format format_id={}, book_format{}>".format(self.format_id,
                                                             self.book_format)


class Edition(db.Model):
    """ Edition model. """

    __tablename__ = "editions"

    ed_id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=False)  # set to ISBN
    format_id = db.Column(db.Integer, db.ForeignKey("formats.format_id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.book_id"), nullable=False)
    pic_url = db.Column(db.String(150), nullable=True)
    publisher = db.Column(db.String(150), nullable=False)
    num_pages = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=True)
    # gr_url = db.Column(db.String(150), nullable=False) # need to do more research
    # to see if this can be put together manually via the GR ID
    gr_id = db.Column(db.Integer, nullable=False)

    book_format = db.relationship("Format")
    book = db.relationship("Book", backref="editions")

    def __repr__(self):
        """ Provides helpful infor when printing an Edition object. """

        return "<Edition ed_id={}, title={}, publisher={}, date={}>".format(self.ed_id,
                                                                            self.book.title,
                                                                            self.publisher,
                                                                            self.date)


def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our postgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///readerboard'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    #create a fake flask app, so that we can talk to the database by running
    #this file directly
    from flask import Flask
    app = Flask(__name__)
    connect_to_db(app)
    print "Connected to DB."
