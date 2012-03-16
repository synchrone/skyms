from pydev import pydevd
pydevd.settrace('192.168.20.161', port=9001, stdoutToServer=True, stderrToServer=True, suspend=False)

import sys
import settings
import time
import logging
sys.path.append(settings.distroRoot + "/ipc/python")
sys.path.append(settings.distroRoot + "/interfaces/skype/python")

try:
    import Skype
except ImportError:
    raise SystemExit("Program requires Skype and skypekit modules")
SkypeInstance = Skype.GetSkype(settings.keyFileName)
SkypeInstance.Start()

loggedIn = False
def AccountOnChange(self, property_name):
    global loggedIn
    if property_name == 'status':
        if self.status == 'LOGGED_IN':
            loggedIn = True
            print('Login complete.')
Skype.Account.OnPropertyChange = AccountOnChange

account = SkypeInstance.GetAccount(settings.skypeLogin)
print('Logging In')
account.LoginWithPassword(settings.skypePassword)

#awaiting login
while not loggedIn:
    time.sleep(1)

# proceding with web-handling stuff
from flask import Flask, url_for
app = Flask(__name__)

@app.route('/')
def index():
    return 'Usage: GET ' + url_for('channel_message',channel='CHANNEL',message='MESSAGE')

@app.route('/<channel>/<message>',methods=['GET'])
def channel_message(channel,message):
    try:
        conversation = SkypeInstance.GetConversationByBlob(channel, True)
    except Exception as e:
        return  traceback.format_exception(*sys.exc_info())
    conversation.PostText(message, False)
    return 'OK'



if __name__ == '__main__':
    import logging
    fh = logging.FileHandler('skyms.log')
    fh.setLevel(logging.DEBUG)
    app.logger.addHandler(fh)

    app.run(host='0.0.0.0')