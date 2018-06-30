import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import ssl
import re
import requests
import json


class PokerSocketProvider:
    def get(self):
        return websocket.WebSocketApp('wss://planningpokercore.azurewebsites.net/ws')


class UserCacheItem:
    def __init__(self, session_id, user_id, token, user_name=None, is_host=None, is_observer=None):
        self.session_id = session_id
        self.user_id = user_id
        self.user_name = user_name
        self.is_host = is_host
        self.is_observer = is_observer
        self.token = token


class UserCacheProvider:
    def __init__(self):
        self.__user_cache = {}

    def get_user(self, session_id):
        return self.__user_cache[session_id]

    def set_user(self, session_id, user_cache_item):
        self.__user_cache[session_id] = user_cache_item


class PlanningPokerConnection:

    def __init__(self,
                 api_key,
                 on_connected=None,
                 on_session_creation_succeeded=None,
                 on_session_creation_failed=None,
                 on_session_stale=None,
                 on_session_ended=None,
                 on_session_join_suceeded=None,
                 on_session_join_failed=None,
                 on_invalid_message=None):
        self.api_key = api_key
        self.on_connected = on_connected
        self.on_session_creation_succeeded = on_session_creation_succeeded
        self.on_session_creation_failed = on_session_creation_failed
        self.on_session_stale = on_session_stale
        self.on_session_ended = on_session_ended
        self.on_session_join_suceeded = on_session_join_suceeded
        self.on_session_join_failed = on_session_join_failed
        self.on_invalid_message = on_invalid_message
        self.wsocket = None
        self.__user_cache_provider = UserCacheProvider()

    def __get_session_information(self, session_id):
        req = requests.get('https://sicarringtonplanningpokerapinew.azurewebsites.net/api/Sessions/' + session_id,
                           headers={'user-key': self.api_key})
        session_information = json.loads(req.text)

        user = self.__user_cache_provider.get_user(session_id)
        user_id = user.user_id
        token = user.token

        user_information = None
        for participant in session_information["participants"]:
            if participant["id"] == user_id:
                user_information = participant
                break

        self.__user_cache_provider.set_user(session_id, UserCacheItem(session_id, user_id, token,
                                                                      user_information["name"], user_information["isHost"], user_information["isObserver"]))

        return session_information

    def __handle_message_newsessionmessage(self, message):
        messageSuccessRegex = re.compile(
            r'Success:(.*)', re.MULTILINE | re.IGNORECASE)
        messageSuccessMatch = messageSuccessRegex.findall(message)

        if messageSuccessMatch[0] == 'false':
            if self.on_session_creation_failed is not None:
                self.on_session_creation_failed()
        else:
            if self.on_session_creation_succeeded is not None:
                messageSessionIdRegex = re.compile(
                    r'SessionId:(.*)', re.MULTILINE | re.IGNORECASE)
                messageSessionIdMatch = messageSessionIdRegex.findall(message)

                userIdRegex = re.compile(
                    r'userId:(.*)', re.MULTILINE | re.IGNORECASE)
                userIdMatch = userIdRegex.findall(message)

                tokenRegex = re.compile(
                    r'token:(.*)', re.MULTILINE | re.IGNORECASE)
                tokenMatch = tokenRegex.findall(message)

                self.__user_cache_provider.set_user(messageSessionIdMatch[0], UserCacheItem(
                    messageSessionIdMatch[0], userIdMatch[0], tokenMatch[0]))

                self.on_session_creation_succeeded(messageSessionIdMatch[0],
                                                   userIdMatch[0], tokenMatch[0])

    def __handle_message_session_stale(self, message):
        messageSessionIdRegex = re.compile(
            r'SessionId:(.*)', re.MULTILINE | re.IGNORECASE)
        messageSessionIdMatch = messageSessionIdRegex.findall(message)

        session_data = self.__get_session_information(messageSessionIdMatch[0])

        if self.on_session_stale is not None:
            self.on_session_stale(session_data)

    def __handle_message_session_ended(self, message):
        self.close_connection()
        if self.on_session_ended is not None:
            self.on_session_ended()

    def __handle_message_join_session(self, message):
        messageSuccessRegex = re.compile(
            r'Success:(.*)', re.MULTILINE | re.IGNORECASE)
        messageSuccessMatch = messageSuccessRegex.findall(message)

        if messageSuccessMatch[0] == 'false':
            if self.on_session_join_suceeded is not None:
                self.on_session_join_suceeded()
        else:
            messageSessionIdRegex = re.compile(
                r'SessionId:(.*)', re.MULTILINE | re.IGNORECASE)
            messageSessionIdMatch = messageSessionIdRegex.findall(message)

            userIdRegex = re.compile(
                r'userId:(.*)', re.MULTILINE | re.IGNORECASE)
            userIdMatch = userIdRegex.findall(message)

            tokenRegex = re.compile(
                r'token:(.*)', re.MULTILINE | re.IGNORECASE)
            tokenMatch = tokenRegex.findall(message)

            self.on_session_join_suceeded(messageSessionIdMatch[0],
                                          userIdMatch[0], tokenMatch[0])

    def __handle_message_invalid(self, message):
        if self.on_invalid_message is not None:
            self.on_invalid_message()

    def on_message(self, ws, message):
        print(message)

        messageTypeRegex = re.compile(
            r'MessageType:(.*)', re.MULTILINE | re.IGNORECASE)
        messageTypeMatch = messageTypeRegex.findall(message)

        if messageTypeMatch[0] == 'NewSessionResponse':
            self.__handle_message_newsessionmessage(message)
        elif messageTypeMatch[0] == 'RefreshSession':
            self.__handle_message_session_stale(message)
        elif messageTypeMatch[0] == 'SessionEndedMessage':
            self.__handle_message_session_ended(message)
        elif messageTypeMatch[0] == 'JoinSessionResponse':
            self.__handle_message_join_session(message)
        elif messageTypeMatch[0] == 'InvalidMessage':
            self.__handle_message_invalid(message)

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
        self.wsocket.send(
            "PP 1.0\nMessageType:NewSession\nUserName:" + hostName)

    def update_user(self, session_id, user_to_update_id, user_name, vote, is_host, is_observer):
        user_info = self.__user_cache_provider.get_user(session_id)
        self.wsocket.send("PP 1.0\nMessageType:UpdateSessionMemberMessage\nSessionId:" + session_id + "\nUserToUpdateId:" + user_to_update_id + "\nUserId:" +
                          user_info.user_id + "\nUserName:" + user_name + "\nVote:" + vote + "\nIsHost:" + str(is_host) + "\nIsObserver:" + str(is_observer) + "\nToken:" + user_info.token)

    def join_session(self, session_id, user_name):
        self.wsocket.send("PP 1.0\nMessageType:JoinSession\nUserName:" +
                          user_name + "\nSessionId:" + session_id + "\nIsObserver:false")

    def subscribe_session(self, user_id, session_id):
        user_info = self.__user_cache_provider.get_user(session_id)
        self.wsocket.send("PP 1.0\nMessageType:SubscribeMessage\nUserId:" +
                          user_id + "\nSessionId:" + session_id + "\nToken:" + user_info.token)

    def reset_session_votes(self, session_id):
        user_info = self.__user_cache_provider.get_user(session_id)
        self.wsocket.send("PP 1.0\nMessageType:ResetVotesMessage\nSessionId:" +
                          session_id + "\nUserId:" + user_info.user_id + "\nToken:" + user_info.token)

    def remove_user_from_session(self, session_id, user_to_remove_id):
        user_info = self.__user_cache_provider.get_user(session_id)
        self.wsocket.send("PP 1.0\nMessageType:RemoveUserFromSessionMessage\nSessionId:" + session_id + "\nUserId:" +
                          user_info.user_id + "\nUserToRemoveId:" + user_to_remove_id + "\nToken:" + user_info.token)

    def connect(self):
        websocket.enableTrace(True)
        self.wsocket = websocket.WebSocketApp('wss://planningpokercore.azurewebsites.net/ws',
                                              on_message=self.on_message,
                                              on_error=self.on_error,
                                              on_close=self.on_close)
        self.wsocket.on_open = self.on_open
        self.wsocket.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
