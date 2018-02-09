import untangle
import requests


def book_search_results(key, title):
    """Parses xml data from book.search call, and returns a list of book objects to display."""

    payload = {"key": key, "q": title}
    query = requests.get("https://www.goodreads.com/search.xml", params=payload)

    doc = untangle.parse(query.content)
    print doc
    gr = doc.GoodreadsResponse

    search = gr.search

    results = search.results

    books = []

    for i in range(20):
        book = {}

        book['title'] = results.work[i].best_book.title.cdata.encode('utf8')
        book['book_id'] = int(results.work[i].best_book.id.cdata.encode('utf8'))
        book['author_id'] = int(results.work[i].best_book.author.id.cdata.encode('utf8'))
        book['author_fname'] = results.work[i].best_book.author.name.cdata
        book['image_url'] = results.work[i].best_book.image_url.cdata.encode('utf8')
        books.append(book)

    return books
