# Readerboard

A python/Flask web app for book lovers.  Learn more about the developer [here](https://www.linkedin.com/in/re-wilson/)
or [see Readerboard in action](#).

### Table of Contents

1. [Project Summary and Screenshots](#project-summary)
2. [Tech Stack](#tech-stack)
3. [MVP User Stories](#mvp-user-stories)
4. [2.0 and next steps](#2.0-goals)
5. [Testing Coverage/Instructions](#testing-coverage)
6. [Project Structure](#project-structure)
7. [Setup Instructions](#setup-instructions)

## Project Summary

![landing page](./static/img/landing.png)
Readerboard is a web app that gives readers a central location for tracking their reading habits and finding new books.  The search feature utilizes the Goodreads API, allowing the reader to view details about a book, add it to their shelves, and write a Goodreads book review.  Every book search also shows a list of friends on Goodreads who have read the book. The reader can see the book's availability at the library via the Overdrive API.   Each reader can view charts containing data about their reading habits and progress on custom reading challenges.  Readerboard retrieves user data from Goodreads via OAuth and relies on Chart.js to create meaningful, personalized content.
![book search view](./static/img/searchview.png)
![book detail view](./static/img/bookdetail.png)

## Tech Stack

A full list of project dependencies can be found in [requirements.txt](./requirements.txt).

#### Backend
- Python
- Flask
- PostgreSQL

#### Frontend
- Javascript
- HTML/CSS
- Bootstrap
- jQuery

#### APIs
- Goodreads
- Overdrive

#### Other libraries and tools

- SQLAlchemy
- untangle (xml parsing)
- Chart.js
- rauth
- Jinja2 templating
- werkzeug SimpleCache

## MVP User Stories

| MVP Goals | Status |
| --- |--- |
| User can login and access GR account information via OAuth. | :white_check_mark: |
|User can see the books on their shelves. | :white_check_mark:|
|User can add a book to their shelves, and changes will be reflected in their goodreads account. | :white_check_mark: |
| User can search for a book, and see if GR friends have marked it as read. |:white_check_mark:
| User can search for a book and see it's availability as an ebook at the local library. |:white_check_mark: |
| User can see their reading challenge progress. | :white_check_mark: |
| User can add an additional reading challenge to their account. | :white_check_mark: |
| User can submit a book review. |:white_check_mark: |
| User can see data about their reading habits and history. | :construction: |

## 2.0 Goals

- Finish Deployment
- Keep working on weird bugs within the current features
- Get testing coverage up to 80%
- Optimize the data retrieval and data update processes with celery/celerybeat
- Incorporate the Overdrive Circulation API so users can check out a book or place a copy on hold from within the app
- Add a "watch list" feature that alerts the user when a book added to their list drops below a specific price threshold (Will use Twilio and Amazon Product APIs for this)
- convert the reading history page to React
- Add more data vis with Chart.js

## Testing Coverage

Unit and integration tests written with the python `unittest` library.  Current coverage %: -- oops!

## Project Structure
#### server.py - Core of the flask app, lists all routes
#### model.py - database structure and db creation.
#### parser.py - handles most Goodreads requests and in cases where xml is returned, parses response.
#### helpers.py - small helper functions and most Overdrive API request functions found here.

## Setup Instructions

1. install python
2. ...
3. profit
- (real instructions coming soon!)







