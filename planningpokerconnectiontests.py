#!/usr/bin/env python
# -*- coding: utf-8 -*-

from planningpokerconnection import PlanningPokerConnection, UserCacheItem

import websocket
import mock
import unittest


class PlanningPokerConnectionTests(unittest.TestCase):

    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_create_is_called(self, mock_socketapp):
        mock_socketapp.return_value = mock_socketapp
        expected_name = 'simon'

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.create_session(expected_name)

        mock_socketapp.send.assert_called_with(
            "PP 1.0\nMessageType:NewSession\nUserName:" + expected_name)

    @mock.patch('planningpokerconnection.UserCacheProvider')
    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_update_user_is_called(self, mock_socketapp, mock_user_cache_provider):
        mock_socketapp.return_value = mock_socketapp
        expected_session_id = '123456789'
        expected_user_id = '987654'
        expected_user_to_update_id = '12345'
        expected_user_name = 'AUserName'
        expected_vote = '1'
        expected_is_host = True
        expected_is_observer = True
        expected_token = 'AToken123'

        mock_user_cache_provider.return_value.get_user.return_value.token = expected_token
        mock_user_cache_provider.return_value.get_user.return_value.user_id = expected_user_id
        mock_user_cache_provider.return_value.get_user.return_value.user_name = expected_user_name
        mock_user_cache_provider.return_value.get_user.return_value.is_host = expected_is_host
        mock_user_cache_provider.return_value.get_user.return_value.is_observer = expected_is_observer

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.update_user(expected_session_id, expected_user_to_update_id,
                                              expected_user_name, expected_vote, expected_is_host, expected_is_observer)

        mock_socketapp.send.assert_called_with("PP 1.0\nMessageType:UpdateSessionMemberMessage\nSessionId:" + expected_session_id + "\nUserToUpdateId:" + expected_user_to_update_id + "\nUserId:" +
                                               expected_user_id + "\nUserName:" + expected_user_name + "\nVote:" + expected_vote + "\nIsHost:" + str(expected_is_host) + "\nIsObserver:" + str(expected_is_observer) + "\nToken:" + expected_token)

    @mock.patch('planningpokerconnection.UserCacheProvider')
    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_join_session_is_called(self, mock_socketapp, mock_user_cache_provider):
        mock_socketapp.return_value = mock_socketapp
        expected_session_id = "12345"
        expected_user_name = "fred"

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.join_session(
            expected_session_id, expected_user_name)

        mock_socketapp.send.assert_called_with("PP 1.0\nMessageType:JoinSession\nUserName:" +
                                               expected_user_name + "\nSessionId:" + expected_session_id + "\nIsObserver:false")

    @mock.patch('planningpokerconnection.UserCacheItem')
    @mock.patch('planningpokerconnection.UserCacheProvider')
    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_subscribe_session_is_called(self, mock_socketapp, mock_user_cache_provider, mock_user_cache_item):
        mock_socketapp.return_value = mock_socketapp
        expected_token = 'AToken123'
        expected_session_id = '123456789'
        expected_user_id = '987654'
        expected_token = 'AToken123'

        mock_user_cache_provider.return_value.get_user.return_value.token = expected_token

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.subscribe_session(
            expected_user_id, expected_session_id)

        mock_socketapp.send.assert_called_with("PP 1.0\nMessageType:SubscribeMessage\nUserId:" +
                                               expected_user_id + "\nSessionId:" + expected_session_id + "\nToken:" + expected_token)

    @mock.patch('planningpokerconnection.UserCacheProvider')
    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_reset_session_votes_is_called(self, mock_socketapp, mock_user_cache_provider):
        mock_socketapp.return_value = mock_socketapp
        expected_token = '123456'
        expected_session_id = '123456789'
        expected_user_id = '987654'

        mock_user_cache_provider.return_value.get_user.return_value.token = expected_token
        mock_user_cache_provider.return_value.get_user.return_value.user_id = expected_user_id

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.reset_session_votes(expected_session_id)

        mock_socketapp.send.assert_called_with("PP 1.0\nMessageType:ResetVotesMessage\nSessionId:" +
                                               expected_session_id + "\nUserId:" + expected_user_id + "\nToken:" + expected_token)

    @mock.patch('planningpokerconnection.UserCacheProvider')
    @mock.patch('websocket.WebSocketApp')
    def test_message_is_sent_to_socket_when_remove_user_from_session_is_called(self, mock_socketapp, mock_user_cache_provider):
        mock_socketapp.return_value = mock_socketapp
        expected_token = '123456'
        expected_session_id = '123456789'
        expected_user_id = '987654'
        expected_user_to_remove_id = '4234234'

        mock_user_cache_provider.return_value.get_user.return_value.token = expected_token
        mock_user_cache_provider.return_value.get_user.return_value.user_id = expected_user_id

        planning_poker_connection = PlanningPokerConnection("1234")
        planning_poker_connection.connect()
        planning_poker_connection.remove_user_from_session(
            expected_session_id, expected_user_to_remove_id)

        mock_socketapp.send.assert_called_with("PP 1.0\nMessageType:RemoveUserFromSessionMessage\nSessionId:" + expected_session_id +
                                               "\nUserId:" + expected_user_id + "\nUserToRemoveId:" + expected_user_to_remove_id + "\nToken:" + expected_token)


if __name__ == '__main__':
    unittest.main()
