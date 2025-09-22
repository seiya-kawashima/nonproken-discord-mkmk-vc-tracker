"""discord_attendance_collector.pyのユニットテスト"""  # テストモジュールの説明

import pytest  # テストフレームワーク
import asyncio  # 非同期処理用
import sys  # システム関連操作用
import os  # 環境変数操作用
from unittest.mock import Mock, AsyncMock, patch, MagicMock  # モック用

# discord_attendance_collector.pyをインポート
import discord_attendance_collector as poll_once  # テスト対象モジュール


class TestPollOnce:
    """discord_attendance_collector.pyのテスト"""  # テストクラスの説明

    @pytest.mark.asyncio
    @patch('poll_once.load_dotenv')
    @patch('poll_once.os.getenv')
    @patch('poll_once.os.path.exists')
    @patch('poll_once.DiscordVCPoller')
    @patch('poll_once.SheetsClient')
    @patch('poll_once.SlackNotifier')
    async def test_main_success(self, mock_slack_class, mock_sheets_class, mock_discord_class, 
                                 mock_exists, mock_getenv, mock_load_dotenv):
        """正常動作のテスト"""  # テストの説明
        
        # 環境変数のモック設定
        def getenv_side_effect(key, default=None):
            env_map = {  # 環境変数マップ
                'DISCORD_BOT_TOKEN': 'test_discord_token',  # Discordトークン
                'GOOGLE_SHEET_NAME': 'test_sheet',  # シート名
                'GOOGLE_SERVICE_ACCOUNT_JSON': 'service_account.json',  # JSONファイル
                'ALLOWED_VOICE_CHANNEL_IDS': '123,456',  # チャンネルID
                'SLACK_BOT_TOKEN': 'test_slack_token',  # Slackトークン
                'SLACK_CHANNEL_ID': 'C123',  # SlackチャンネルID
            }
            return env_map.get(key, default)  # 環境変数を返す
        
        mock_getenv.side_effect = getenv_side_effect  # side_effectを設定
        mock_exists.return_value = True  # ファイルが存在する
        
        # Discordクライアントのモック
        mock_discord = AsyncMock()  # Discordインスタンスモック
        mock_discord.get_vc_members.return_value = [  # メンバーリストを返す
            {'guild_id': '111', 'user_id': '222', 'user_name': 'test#1234'}  # メンバー情報
        ]
        mock_discord_class.return_value = mock_discord  # インスタンスを返す
        
        # Sheetsクライアントのモック
        mock_sheets = Mock()  # Sheetsインスタンスモック
        mock_sheets.connect = Mock()  # connectメソッドをモック
        mock_sheets.upsert_presence.return_value = {'new': 1, 'updated': 0}  # 結果を返す
        mock_sheets.get_total_days.return_value = 10  # 通算日数を返す
        mock_sheets_class.return_value = mock_sheets  # インスタンスを返す
        
        # Slackクライアントのモック
        mock_slack = Mock()  # Slackインスタンスモック
        mock_slack.send_login_notification.return_value = True  # 成功を返す
        mock_slack_class.return_value = mock_slack  # インスタンスを返す
        
        # テスト実行
        await poll_once.main()  # メイン処理実行
        
        # アサーション
        mock_load_dotenv.assert_called_once()  # dotenvが読み込まれたか
        mock_discord.get_vc_members.assert_called_once()  # VCメンバー取得が呼ばれたか
        mock_sheets.connect.assert_called_once()  # Sheets接続が呼ばれたか
        mock_sheets.upsert_presence.assert_called_once()  # upsertが呼ばれたか
        mock_slack.send_login_notification.assert_called_once()  # Slack通知が呼ばれたか

    @pytest.mark.asyncio
    @patch('poll_once.load_dotenv')
    @patch('poll_once.os.getenv')
    @patch('poll_once.sys.exit')
    async def test_main_no_discord_token(self, mock_exit, mock_getenv, mock_load_dotenv):
        """Discordトークンがない場合のテスト"""  # テストの説明
        
        # 環境変数のモック設定（Discordトークンなし）
        def getenv_side_effect(key, default=None):
            env_map = {  # 環境変数マップ
                'GOOGLE_SHEET_NAME': 'test_sheet',  # シート名
                'ALLOWED_VOICE_CHANNEL_IDS': '123,456',  # チャンネルID
            }
            return env_map.get(key, default)  # 環境変数を返す
        
        mock_getenv.side_effect = getenv_side_effect  # side_effectを設定
        
        # テスト実行
        await poll_once.main()  # メイン処理実行
        
        # アサーション
        mock_exit.assert_called_with(1)  # 異常終了が呼ばれたか

    @pytest.mark.asyncio
    @patch('poll_once.load_dotenv')
    @patch('poll_once.os.getenv')
    @patch('poll_once.sys.exit')
    async def test_main_no_sheet_name(self, mock_exit, mock_getenv, mock_load_dotenv):
        """シート名がない場合のテスト"""  # テストの説明
        
        # 環境変数のモック設定（シート名なし）
        def getenv_side_effect(key, default=None):
            env_map = {  # 環境変数マップ
                'DISCORD_BOT_TOKEN': 'test_discord_token',  # Discordトークン
                'ALLOWED_VOICE_CHANNEL_IDS': '123,456',  # チャンネルID
            }
            return env_map.get(key, default)  # 環境変数を返す
        
        mock_getenv.side_effect = getenv_side_effect  # side_effectを設定
        
        # テスト実行
        await poll_once.main()  # メイン処理実行
        
        # アサーション
        mock_exit.assert_called_with(1)  # 異常終了が呼ばれたか

    @pytest.mark.asyncio
    @patch('poll_once.load_dotenv')
    @patch('poll_once.os.getenv')
    @patch('poll_once.os.path.exists')
    @patch('poll_once.DiscordVCPoller')
    @patch('poll_once.sys.exit')
    async def test_main_no_members(self, mock_exit, mock_discord_class, 
                                    mock_exists, mock_getenv, mock_load_dotenv):
        """VCにメンバーがいない場合のテスト"""  # テストの説明
        
        # 環境変数のモック設定
        def getenv_side_effect(key, default=None):
            env_map = {  # 環境変数マップ
                'DISCORD_BOT_TOKEN': 'test_discord_token',  # Discordトークン
                'GOOGLE_SHEET_NAME': 'test_sheet',  # シート名
                'GOOGLE_SERVICE_ACCOUNT_JSON': 'service_account.json',  # JSONファイル
                'ALLOWED_VOICE_CHANNEL_IDS': '123,456',  # チャンネルID
            }
            return env_map.get(key, default)  # 環境変数を返す
        
        mock_getenv.side_effect = getenv_side_effect  # side_effectを設定
        mock_exists.return_value = True  # ファイルが存在する
        
        # Discordクライアントのモック（メンバーなし）
        mock_discord = AsyncMock()  # Discordインスタンスモック
        mock_discord.get_vc_members.return_value = []  # 空のリストを返す
        mock_discord_class.return_value = mock_discord  # インスタンスを返す
        
        # テスト実行
        await poll_once.main()  # メイン処理実行
        
        # アサーション
        mock_discord.get_vc_members.assert_called_once()  # VCメンバー取得が呼ばれたか
        mock_exit.assert_not_called()  # 正常終了（exitが呼ばれない）

    @pytest.mark.asyncio
    @patch('poll_once.load_dotenv')
    @patch('poll_once.os.getenv')
    @patch('poll_once.os.path.exists')
    @patch('poll_once.DiscordVCPoller')
    @patch('poll_once.SheetsClient')
    @patch('poll_once.sys.exit')
    async def test_main_exception(self, mock_exit, mock_sheets_class, mock_discord_class,
                                   mock_exists, mock_getenv, mock_load_dotenv):
        """例外発生時のテスト"""  # テストの説明
        
        # 環境変数のモック設定
        def getenv_side_effect(key, default=None):
            env_map = {  # 環境変数マップ
                'DISCORD_BOT_TOKEN': 'test_discord_token',  # Discordトークン
                'GOOGLE_SHEET_NAME': 'test_sheet',  # シート名
                'GOOGLE_SERVICE_ACCOUNT_JSON': 'service_account.json',  # JSONファイル
                'ALLOWED_VOICE_CHANNEL_IDS': '123,456',  # チャンネルID
            }
            return env_map.get(key, default)  # 環境変数を返す
        
        mock_getenv.side_effect = getenv_side_effect  # side_effectを設定
        mock_exists.return_value = True  # ファイルが存在する
        
        # Discordクライアントのモック（例外を発生）
        mock_discord = AsyncMock()  # Discordインスタンスモック
        mock_discord.get_vc_members.side_effect = Exception("Connection error")  # 例外を発生
        mock_discord_class.return_value = mock_discord  # インスタンスを返す
        
        # テスト実行
        await poll_once.main()  # メイン処理実行
        
        # アサーション
        mock_exit.assert_called_with(1)  # 異常終了が呼ばれたか