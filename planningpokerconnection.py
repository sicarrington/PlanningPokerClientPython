import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import ssl
import re
import requests

class PlanningPokerConnection:

    def __init__(self,
        api_key, 
        on_connected = None,
        on_session_creation_succeeded = None,
        on_session_creation_failed = None,
        on_session_stale = None,
        on_session_ended = None):
        self.api_key = api_key
        self.on_connected = on_connected
        self.on_session_creation_succeeded = on_session_creation_succeeded
        self.on_session_creation_failed = on_session_creation_failed
        self.on_session_stale = on_session_stale
        self.on_session_ended = on_session_ended
        self.wsocket = None

    def __handle_message_newsessionmessage(self, message): 
        messageSuccessRegex = re.compile(r'Success:(.*)', re.MULTILINE | re.IGNORECASE)
        messageSuccessMatch = messageSuccessRegex.findall(message)
        
        if messageSuccessMatch[0] == 'false':
            if self.on_session_creation_failed is not None:
                self.on_session_creation_failed()
        else:
            if self.on_session_creation_succeeded is not None:
                messageSessionIdRegex = re.compile(r'SessionId:(.*)', re.MULTILINE | re.IGNORECASE)
                messageSessionIdMatch = messageSessionIdRegex.findall(message)

                userIdRegex = re.compile(r'userId:(.*)', re.MULTILINE | re.IGNORECASE)
                userIdMatch = userIdRegex.findall(message)

                tokenRegex = re.compile(r'token:(.*)', re.MULTILINE | re.IGNORECASE)
                tokenMatch = tokenRegex.findall(message)

                self.on_session_creation_succeeded(messageSessionIdMatch[0], 
                    userIdMatch[0], tokenMatch[0])

    def __handle_message_session_stale(self, message):
        messageSessionIdRegex = re.compile(r'SessionId:(.*)', re.MULTILINE | re.IGNORECASE)
        messageSessionIdMatch = messageSessionIdRegex.findall(message)

        req = requests.get('https://sicarringtonplanningpokerapinew.azurewebsites.net/api/Sessions/'+ messageSessionIdMatch[0], 
            headers={'user-key': self.api_key})

        print(req.text)

        if self.on_session_stale is not None:
            self.on_session_stale()

    def __handle_message_session_ended(self, message):
        self.close_connection()
        if self.on_session_ended is not None:
            self.on_session_ended()

    def on_message(self, ws, message):
        print(message)

        messageTypeRegex = re.compile(r'MessageType:(.*)', re.MULTILINE | re.IGNORECASE)
        messageTypeMatch = messageTypeRegex.findall(message)

        if messageTypeMatch[0] == 'NewSessionResponse':
            self.__handle_message_newsessionmessage(message)
        elif messageTypeMatch[0] == 'RefreshSession':
            self.__handle_message_session_stale(message)
        elif messageTypeMatch[0] == 'SessionEndedMessage':
            self.__handle_message_session_ended(message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        print('on open')
        if self.on_connected is not None:
            self.on_connected()

    def close_connection(self):
        self.wsocket.close()


    def create_session(self, hostName):
        self.wsocket.send("PP 1.0\nMessageType:NewSession\nUserName:" + hostName)
    
    def update_user(self, sessionId, userId, userName, vote, isHost, isObserver, token):
        self.wsocket.send("PP 1.0\nMessageType:UpdateSessionMemberMessage\nSessionId:" + sessionId + "\nUserToUpdateId:" + userId + "\nUserId:" + userId + "\nUserName:" + userName + "\nVote:" + vote + "\nIsHost:" + isHost + "\nIsObserver:" + isObserver + "\nToken:" + token)

    def connect(self):
        websocket.enableTrace(True)
        self.wsocket = websocket.WebSocketApp('wss://planningpokercore.azurewebsites.net/ws',
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.wsocket.on_open = self.on_open
        self.wsocket.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
