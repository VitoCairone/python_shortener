"""
  conventions for setting up a database to use with Flask taken from these
  two projects: 
  
  http://github.com/mitsuhiko/flask/blob/master/examples/flaskr
  http://github.com/mitsuhiko/flask/blob/master/examples/minitwit
  
  Likewise, in style conventions regarding spacing, variable names,
  capitalization, etc. I've tried to mirror those projects as closely as
  possible.
"""

import string
import random
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, redirect, g, render_template, url_for, abort
from flask import jsonify
app = Flask(__name__)
SHORT_URL_SIZE = 5
SHORT_URL_HALF_SPACE = (36 ** SHORT_URL_SIZE) / 2

# Load default config
app.config.update(dict(
    DATABASE='/tmp/urls.db',
    DEBUG=True, # Do not set this True in production!
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
    
def make_new_short_url():
    """ generates and returns a random string which is not already a short_url
    in use. However, this method is NOT race-condition-proof (TODO: implement
    fix for this). Note that a size of 3 is unacceptable because it raises the
    possibility of dynamically generating the special shortURLs 'add' or 'all'
    """
    assert SHORT_URL_SIZE > 3
    chars = string.ascii_lowercase + string.digits
    not_unique = True
    db = get_db()
    
    """ It is always necessary to have the capability to increase the short
    URL length to prevent all names from being taken. This routine resizes when
    only half of a the name space is used; this means that the number of times
    a name is likely to be rejected never rises very high. However, with a proper
    queue of pre-cleared names, it would be possible to use the entire space
    before having to resize instead. """
    present_count = int(db.execute('select count * from urls').fetchone())
    
    while present_count > SHORT_URL_HALF_SPACE:
        SHORT_URL_SIZE += 1
        SHORT_URL_HALF_SPACE = (36 ** SHORT_URL_SIZE) / 2
    
    while not_unique:
        candidate = ''.join(random.choice(chars) for x in range(SHORT_URL_SIZE))
        cur = db.execute('select * from urls where short_url = ?', [candidate])
        if cur.fetchone() is None:
            not_unique = False
    return candidate
    
@app.teardown_appcontext
def close_db(error):
    # Closes the database at the end of a request
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

""" This handy debugging route displays the whole database as a simple page.
# It results in a 404 when the app is not in debug mode. """
@app.route('/all')
def list_all():
    if not app.config['DEBUG']:
        abort(404)
    db = get_db()
    cur = db.execute('select * from urls')
    url_list = cur.fetchall()
    return render_template('list_urls.html', url_list=url_list)
    
""" This is the app's main view and accepts a long URL to shorten.
It is important that '/' map to index because the helper url_for(index) is also
used in index.html as the root of the app's full URL. """    
@app.route('/')
def index():
    return render_template('index.html')
    
# This route accepts new long URLs via AJAX to create short URLs for.
@app.route('/add', methods=['POST'])
def add_url():
    db = get_db()
    new_short_url = make_new_short_url()
    long_url = request.form['url']
    db.execute('insert into urls (short_url, long_url) values (?,?)',
                [new_short_url, long_url])
    db.commit()
    return jsonify(result=new_short_url);

""" This route handles actual short URLs by redirecting to the intended long URL
an appropraite plaintext error if there is no such short URL. The app is not
responsable for users who input nonsense long URLs and will redirect to them
faithfully. """ 
@app.route('/<short_url>')
def goto_full_url(short_url):
    db = get_db()
    cur = db.execute('select * from urls where short_url = ?', [short_url])
    url_row = cur.fetchone()
    if url_row is None:
        return 'The short URL you input does not map to anything.'
    long_url = url_row['long_url']
    """ The redirect needs to be prefixed with // so that Flask doesn't try to
    stay within the app's own domain. However, this breaks urls which explicitly
    include prefixes, so these are handled explicitly. """
    if '://' in long_url:
        return redirect(long_url)
    return redirect('//%s' % url_row['long_url'])
    
if __name__ == '__main__':
    init_db()
    app.run()