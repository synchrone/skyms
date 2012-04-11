import sys
import settings
import time
import traceback
from flask import request

try:
    import Skype
except ImportError:
    raise SystemExit("Program requires skypekit and Skype modules from "+
                     "<skypekitsdk>/ipc/python and <skypekitsdk>/interfaces/skype/python respectively")

SkypeInstance = Skype.GetSkype(settings.keyFileName)
SkypeInstance.Start()

loggedIn = False
def AccountOnChange(self, property_name):
    global loggedIn
    if property_name == 'status':
        if self.status == 'LOGGED_IN':
            loggedIn = True
            print('Login complete.')
        else:
            print('Status changed to '+self.status)
    else:
        print('Account property changed: '+property_name+'. New value: '+str(getattr(self,property_name)))
Skype.Account.OnPropertyChange = AccountOnChange

account = SkypeInstance.GetAccount(settings.skypeLogin)
print('Logging In')
account.LoginWithPassword(settings.skypePassword)

#awaiting login
while not loggedIn:
    time.sleep(1)

convList = SkypeInstance.GetConversationList('REALLY_ALL_CONVERSATIONS')
print('Found ' + str(len(convList)) + ' conversations.')
N = 1

for c in convList:
    if c.type =='CONFERENCE':
        print(str(N) + '. ' + c.displayname + '  (type = ' + c.type + ') blob: '+c.GetJoinBlob())
        N += 1

# proceding with web-handling stuff
from flask import Flask, url_for
app = Flask(__name__)

@app.route('/',methods=['GET'])
def index():
    return 'Usage: GET ' + url_for('channel_message',channel='CHANNEL',message='MESSAGE') + '''
        <br />
        OR <form method='POST'>
            <input type='test' name='channel' /><br />
            <textarea name='message'></textarea>
            <input type='submit' />
        </form>'''


@app.route('/',methods=['POST'])
@app.route('/<channel>/<message>',methods=['GET'])
def channel_message(channel=None,message=None):

    if request.method == 'POST':
        channel = request.form['channel']
        message = request.form['message']

    try:
        #Skype conference BLOB is like:
        # skype:?chat&blob=HrO22b73C8eeDucL4CR8OfDNI_chxBOJ6CbNZtQTMFRVG2KFcG_kGGFF3g2uLT3s
        conversation = SkypeInstance.GetConversationByBlob(channel, True)
        conversation.PostText(message, False)
        return 'OK'

    except Exception as e:
        app.logger.error(
            "<br />\n".join(traceback.format_exception(*sys.exc_info()))
        )
        return 'ERROR'

if __name__ == '__main__':
    import logging
    fh = logging.FileHandler('skyms.log')
    fh.setLevel(logging.DEBUG)
    app.logger.addHandler(fh)

    app.run(host='0.0.0.0')