#!/usr/bin/env python

from planningpokerconnection import PlanningPokerConnection

def connected():
    print('test connected callback')
    pp.create_session("Simon")

def on_session_creation_suceeded(sessionId, userId, token):
    print('session created callback, result:')
    print(sessionId)
    print(userId)
    print(token)
    pp.close_connection()

def on_session_creation_failed():
    pp.close_connection()

def on_session_stale():
    print("session stale")

if __name__ == '__main__':
    pp = PlanningPokerConnection('1234', connected, on_session_creation_suceeded)
    pp.connect()


