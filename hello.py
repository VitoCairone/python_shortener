"""
  conventions for setting up a database to use with Flask taken from these
  two projects: 
  
  http://github.com/mitsuhiko/flask/blob/master/examples/flaskr
  http://github.com/mitsuhiko/flask/blob/master/examples/minitwit
  
  Likewise, style conventions regarding spacing, variable names,
  capitalization, etc. mirror those projects as closely as possible.
"""

import string
import random
from sqlite3 import dbapi2 as sqlite3
from redis import Redis
from flask import Flask, request, redirect, g, render_template, url_for, abort
app = Flask(__name__)
""" via http://flask.pocoo.org/snippets/71/,
'A redis instance is thread safe so you can just keep this on the global level
and use it directly.' """
redis = Redis()

# Load default config
app.config.update(dict(
    DATABASE='/tmp/urls.db',
    DEBUG=True, # Do not set this True in production!!
    REDIS_QUEUE_KEY='next_url_queue'
))

def connect_db():
    # Connects to the database
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv
    
def init_db():
    # Creates the database
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        
def get_db():
    # Opens a new database connection if there is none for the current
    # app context
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
    
# in the current implementation, size is always 5 and not actually variable
def make_new_short_url(size):
    # a size of 3 is unacceptable because it raises the possibility
    # of dynamically generating the special shortURLs 'add' or 'all'
    assert size > 3
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for x in range(size))
    
@app.teardown_appcontext
def close_db(error):
    # Closes the database at the end of a request
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# This handy debugging route displays the whole database as a simple page.
# It results in a 404 when the app is not in debug mode.
@app.route('/all')
def list_all():
    if not app.config['DEBUG']:
        abort(404)
    db = get_db()
    cur = db.execute('select * from urls')
    url_list = cur.fetchall()
    return render_template('list_urls.html', url_list=url_list)
    
@app.route('/')
# This is the app's main view and accepts a long URL to shorten.
def index():
    db = get_db()
    cur = db.execute('select * from urls')
    url_list = cur.fetchall()
    return render_template('list_urls.html', url_list=url_list)
    
@app.route('/add', methods=['POST'])
def add_url():
    db = get_db()
    new_short_url = make_new_short_url(5)
    long_url = request.form['url']
    db.execute('insert into urls (short_url, long_url) values (?,?)',
                [new_short_url, long_url])
    db.commit()
    """ This is somewhat sub-ideal because it does not update the browser URL to
    one which is meaningful. It would be better to redirect to the view,
    rather than returning it in-place, if the short_url could be passed to it.
    """
    return render_template('created_entry.html', short_url=new_short_url,
                                                 long_url=long_url)

@app.route('/<short_url>')
def goto_full_url(short_url):
    db = get_db()
    cur = db.execute('select * from urls where short_url = ?', [short_url])
    url_row = cur.fetchone()
    return redirect(url_row['long_url'])
    
if __name__ == '__main__':
    init_db()
    app.run()