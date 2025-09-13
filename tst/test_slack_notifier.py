"""Slack通知クライアントのユニットテスト"""  # テストモジュールの説明

import pytest  # テストフレームワーク
from unittest.mock import Mock, patch  # モック用
from slack_sdk.errors import SlackApiError  # Slackエラー用

from src.slack_notifier import SlackNotifier  # テスト対象クラス


class TestSlackNotifier:
    """SlackNotifierクラスのテスト"""  # テストクラスの説明

    def test_init(self):
        """初期化処理のテスト"""  # テストの説明
        bot_token = "xoxb-test-token"  # テスト用トークン
        channel_id = "C1234567890"  # テスト用チャンネルID
        
        notifier = SlackNotifier(bot_token, channel_id)  # インスタンス作成
        
        assert notifier.bot_token == bot_token  # トークンが正しく設定されているか
        assert notifier.channel_id == channel_id  # チャンネルIDが正しく設定されているか
        assert notifier.client is not None  # クライアントが作成されているか

    @patch('src.slack_notifier.WebClient')
    def test_send_login_notification_normal(self, mock_webclient_class):
        """通常のログイン通知のテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.return_value = {"ok": True}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.send_login_notification("testuser#1234", 15)  # 通知送信
        
        # アサーション
        mock_client.chat_postMessage.assert_called_once_with(  # API呼び出し確認
            channel="C123",  # チャンネルID
            text="🎤 testuser#1234 さんがログインしました！（通算 15 日目）"  # メッセージ内容
        )
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_login_notification_milestone(self, mock_webclient_class):
        """節目のログイン通知のテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.return_value = {"ok": True}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.send_login_notification("testuser#1234", 100)  # 100日目の通知
        
        # アサーション
        mock_client.chat_postMessage.assert_called_once_with(  # API呼び出し確認
            channel="C123",  # チャンネルID
            text="🎉 testuser#1234 さんがログインしました！（通算 100 日目！おめでとう！）"  # お祝いメッセージ
        )
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_login_notification_api_error(self, mock_webclient_class):
        """API エラー時のテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        
        # SlackApiErrorを発生させる
        error_response = {"error": "channel_not_found"}  # エラーレスポンス
        mock_client.chat_postMessage.side_effect = SlackApiError(  # エラーを発生
            message="Error",  # エラーメッセージ
            response=error_response  # エラーレスポンス
        )
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.send_login_notification("testuser#1234", 15)  # 通知送信
        
        # アサーション
        assert result is False  # 失敗が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_login_notification_unexpected_error(self, mock_webclient_class):
        """予期しないエラーのテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.side_effect = Exception("Network error")  # 例外を発生
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.send_login_notification("testuser#1234", 15)  # 通知送信
        
        # アサーション
        assert result is False  # 失敗が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_daily_summary_no_members(self, mock_webclient_class):
        """メンバーなしのサマリーテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.return_value = {"ok": True}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.send_daily_summary(0, [])  # サマリー送信
        
        # アサーション
        mock_client.chat_postMessage.assert_called_once_with(  # API呼び出し確認
            channel="C123",  # チャンネルID
            text="📊 本日のVCログイン: なし"  # メッセージ内容
        )
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_daily_summary_with_members(self, mock_webclient_class):
        """メンバーありのサマリーテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.return_value = {"ok": True}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        members_list = ["user1", "user2", "user3"]  # メンバーリスト
        result = notifier.send_daily_summary(3, members_list)  # サマリー送信
        
        # アサーション
        mock_client.chat_postMessage.assert_called_once_with(  # API呼び出し確認
            channel="C123",  # チャンネルID
            text="📊 本日のVCログイン: 3名\nuser1, user2, user3"  # メッセージ内容
        )
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_send_daily_summary_many_members(self, mock_webclient_class):
        """多数メンバーのサマリーテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.chat_postMessage.return_value = {"ok": True}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        members_list = [f"user{i}" for i in range(15)]  # 15人のメンバー
        result = notifier.send_daily_summary(15, members_list)  # サマリー送信
        
        # アサーション
        expected_members = ", ".join([f"user{i}" for i in range(10)])  # 最初の10人
        expected_text = f"📊 本日のVCログイン: 15名\n{expected_members} 他5名"  # 期待されるテキスト
        mock_client.chat_postMessage.assert_called_once_with(  # API呼び出し確認
            channel="C123",  # チャンネルID
            text=expected_text  # メッセージ内容
        )
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_test_connection_success(self, mock_webclient_class):
        """接続テスト成功のテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.auth_test.return_value = {"ok": True, "team": "Test Team"}  # 成功レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.test_connection()  # 接続テスト
        
        # アサーション
        mock_client.auth_test.assert_called_once()  # auth_testが呼ばれたか
        assert result is True  # 成功が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_test_connection_failure(self, mock_webclient_class):
        """接続テスト失敗のテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        mock_client.auth_test.return_value = {"ok": False}  # 失敗レスポンス
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.test_connection()  # 接続テスト
        
        # アサーション
        mock_client.auth_test.assert_called_once()  # auth_testが呼ばれたか
        assert result is False  # 失敗が返されるか

    @patch('src.slack_notifier.WebClient')
    def test_test_connection_api_error(self, mock_webclient_class):
        """接続テストAPIエラーのテスト"""  # テストの説明
        # モックの設定
        mock_client = Mock()  # クライアントモック
        mock_webclient_class.return_value = mock_client  # クライアントを返す
        
        # SlackApiErrorを発生させる
        error_response = {"error": "invalid_auth"}  # エラーレスポンス
        mock_client.auth_test.side_effect = SlackApiError(  # エラーを発生
            message="Error",  # エラーメッセージ
            response=error_response  # エラーレスポンス
        )
        
        # テスト実行
        notifier = SlackNotifier("xoxb-test", "C123")  # インスタンス作成
        result = notifier.test_connection()  # 接続テスト
        
        # アサーション
        assert result is False  # 失敗が返されるか