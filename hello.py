"""
  conventions for setting up a database to use with Flask taken from these
  two projects: 
  http://github.com/mitsuhiko/flask/blob/master/examples/flaskr
  http://github.com/mitsuhiko/flask/blob/master/examples/minitwit
"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, redirect
app = Flask(__name__)

# Load default config
app.config.update(dict(
    DATABASE='/tmp/flaskr.db',
    DEBUG=True, #Do not set this true in production!!
))

@app.route('/')
def hello_world():
    return 'Hello World! 3'

@app.route('/<short_url>')
def full_url(short_url):
    return redirect("http://%s" % short_url)
    
if __name__ == '__main__':
    # not for production code!
    # this line detects changes in the file so we don't have to
    # keep restarting the server.
    app.run()