import sys
sys.path.append('/home/dotcloud/current')
sys.path.append('/home/dotcloud/current/skypekit')

from skyms import app as flask_app
application = flask_app.app
