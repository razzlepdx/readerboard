import oauth2 as oauth
import urlparse
import os

GR_KEY = os.environ['GR_KEY']
GR_SECRET = os.environ['GR_SECRET']

url = 'http://www.goodreads.com'
request_token_url = '{}/oauth/request_token/'.format(url)
authorize_url = '{}/oauth/authorize/'.format(url)
access_token_url = '{}/oauth/access_token/'.format(url)

consumer = oauth.Consumer(key=GR_KEY,
                          secret=GR_SECRET)

client = oauth.Client(consumer)

response, content = client.request(request_token_url, 'GET')
if response['status'] != '200':
    raise Exception('Invalid response: {}'.format(response['status']))

request_token = dict(urlparse.parse_qsl(content))

authorize_link = '{}?oauth_token={}'.format(authorize_url,
                                            request_token['oauth_token'])
print authorize_link
accepted = 'n'
while accepted.lower() == 'n':
    # you need to access the authorize_link via a browser,
    # and proceed to manually authorize the consumer
    accepted = raw_input('Have you authorized me? (y/n) ')

token = oauth.Token(request_token['oauth_token'],
                    request_token['oauth_token_secret'])

client = oauth.Client(consumer, token)
response, content = client.request(access_token_url, 'POST')
if response['status'] != '200':
    raise Exception('Invalid response: {}'.format(response['status']))

access_token = dict(urlparse.parse_qsl(content))

# this is the token you should save for future uses
token = oauth.Token(access_token['oauth_token'],
                    access_token['oauth_token_secret'])

#
# As an example, let's add a book to one of the user's shelves
#

# import urllib

# client = oauth.Client(consumer, token)
# # the book is: "Generation A" by Douglas Coupland
# body = urllib.urlencode({'name': 'to-read', 'book_id': 6801825})
# headers = {'content-type': 'application/x-www-form-urlencoded'}
# response, content = client.request('%s/shelf/add_to_shelf.xml' % url,
#                                    'POST', body, headers)
# # check that the new resource has been created
# if response['status'] != '201':
#     raise Exception('Cannot create resource: %s' % response['status'])
# else:
#     print 'Book added!'
