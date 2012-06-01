print "Trying to start skyms..."
import sys
import settings
import time
import traceback
import signal
from flask import request

try:
    import Skype
except ImportError:
    raise SystemExit("Program requires skypekit and Skype modules from "+
                     "<skypekitsdk>/ipc/python and <skypekitsdk>/interfaces/skype/python respectively")

print "Startup..."
SkypeInstance = Skype.GetSkype(settings.keyFileName)
SkypeInstance.Start()

#SIGINT handler
def signal_handler(signal, frame):
    global SkypeInstance
    SkypeInstance.stop()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#login handler
loggedIn = False
def AccountOnChange(self, property_name):
    global loggedIn
    if property_name == 'status':
        if self.status == 'LOGGED_IN':
            loggedIn = True
            print('Login complete.')
        elif self.status == 'LOGGED_OUT':
            loggedIn = False
        else:
            print('Status changed to '+self.status)
Skype.Account.OnPropertyChange = AccountOnChange
conferenceCount = 0
def OnConversationListChange(_self,conversation,type,added):
    if conversation.type == 'CONFERENCE' and type == 'REALLY_ALL_CONVERSATIONS':
        global conferenceCount
        conferenceCount += 1 if added else -1
        print conversation.displayname + " (BLOB:" + conversation.GetJoinBlob() + ") TYPE: " + conversation.type + " added" if added else "removed"
Skype.Skype.OnConversationListChange = OnConversationListChange

account = SkypeInstance.GetAccount(settings.skypeLogin)
account.LoginWithPassword(settings.skypePassword)

print "Log in ..."
while not loggedIn: time.sleep(1)
print "Awaiting conference list to populate..."
while conferenceCount == 0: time.sleep(1)


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

        print "Getting converstaion "+channel
        conversation = SkypeInstance.GetConversationByBlob(channel)
        print "Posing text..."
        conversation.PostText(message, False)
        return 'OK'

    except Exception as e:
        print "ERROR: " + e.msg + "\n" + "\n".join(traceback.format_exception(*sys.exc_info()))
        return 'ERROR'

if __name__ == '__main__':
    app.run(host='0.0.0.0')