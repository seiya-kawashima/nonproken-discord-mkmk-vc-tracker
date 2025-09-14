#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日次集計プログラムのテストコード
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import date, datetime, timedelta
import os
import sys
import json
import base64
import io

# テスト対象モジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from daily_aggregator import DailyAggregator


class TestDailyAggregator(unittest.TestCase):
    """DailyAggregatorクラスのテスト"""

    def setUp(self):
        """テストの前処理"""
        # 環境変数の設定
        self.env_patcher = patch.dict(os.environ, {
            'GOOGLE_SHEET_NAME': 'Test_Sheet',
            'ALLOWED_VOICE_CHANNEL_IDS': '123456789,987654321',
            'GOOGLE_SERVICE_ACCOUNT_JSON': 'test_service_account.json'
        })
        self.env_patcher.start()

        # Google APIサービスのモック
        self.mock_drive_service = MagicMock()
        self.mock_sheets_service = MagicMock()

    def tearDown(self):
        """テストの後処理"""
        self.env_patcher.stop()

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_initialization(self, mock_build, mock_credentials):
        """初期化処理のテスト"""
        # モックの設定
        mock_credentials.from_service_account_info.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        # インスタンス作成
        aggregator = DailyAggregator(date(2025, 9, 15))

        # アサーション
        self.assertEqual(aggregator.target_date, date(2025, 9, 15))  # 対象日付の確認
        self.assertEqual(aggregator.sheet_name, 'Test_Sheet')  # シート名の確認
        self.assertEqual(aggregator.allowed_vc_ids, ['123456789', '987654321'])  # VCチャンネルIDの確認

        # API初期化の確認
        self.assertEqual(mock_build.call_count, 2)  # Drive APIとSheets APIの2回
        mock_build.assert_any_call('drive', 'v3', credentials=mock_credentials.from_service_account_info.return_value)
        mock_build.assert_any_call('sheets', 'v4', credentials=mock_credentials.from_service_account_info.return_value)

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_parse_vc_ids(self, mock_build, mock_credentials):
        """VCチャンネルID解析のテスト"""
        # 環境変数を変更
        with patch.dict(os.environ, {'ALLOWED_VOICE_CHANNEL_IDS': '111,222,333'}):
            aggregator = DailyAggregator()
            self.assertEqual(aggregator.allowed_vc_ids, ['111', '222', '333'])

        # 環境変数が空の場合
        with patch.dict(os.environ, {'ALLOWED_VOICE_CHANNEL_IDS': ''}):
            aggregator = DailyAggregator()
            self.assertEqual(aggregator.allowed_vc_ids, [])

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_get_csv_files_from_drive(self, mock_build, mock_credentials):
        """CSVファイル取得のテスト"""
        # モックの設定
        aggregator = DailyAggregator()
        aggregator.drive_service = self.mock_drive_service

        # フォルダ検索結果のモック
        self.mock_drive_service.files().list().execute.side_effect = [
            {'files': [{'id': 'folder123', 'name': 'VC_Tracker_Data'}]},  # フォルダ検索結果
            {'files': [  # CSVファイル検索結果
                {'id': 'csv1', 'name': 'general-voice.csv'},
                {'id': 'csv2', 'name': 'study-room.csv'}
            ]}
        ]

        # メソッド実行
        csv_files = aggregator.get_csv_files_from_drive()

        # アサーション
        self.assertEqual(len(csv_files), 2)  # 2つのCSVファイル
        self.assertEqual(csv_files[0]['name'], 'general-voice.csv')
        self.assertEqual(csv_files[1]['name'], 'study-room.csv')

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_read_csv_content(self, mock_build, mock_credentials):
        """CSV内容読み込みのテスト"""
        # モックの設定
        aggregator = DailyAggregator(date(2025, 9, 15))
        aggregator.drive_service = self.mock_drive_service

        # CSVコンテンツのモック
        csv_content = """datetime_jst,user_id,user_name,present
2025/09/15 10:30,111111111111111111,kawashima#1234,TRUE
2025/09/15 10:30,222222222222222222,tanaka#5678,TRUE
2025/09/14 10:30,333333333333333333,suzuki#9012,TRUE"""

        # ダウンロードのモック
        mock_request = MagicMock()
        self.mock_drive_service.files().get_media.return_value = mock_request

        with patch('daily_aggregator.MediaIoBaseDownload') as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader.next_chunk.return_value = (None, True)  # 1回で完了
            mock_downloader_class.return_value = mock_downloader

            # BytesIOに書き込むモック
            with patch('io.BytesIO') as mock_bytesio_class:
                mock_file = MagicMock()
                mock_file.read.return_value = csv_content.encode('utf-8')
                mock_bytesio_class.return_value = mock_file

                # メソッド実行
                records = aggregator.read_csv_content('csv1', 'general-voice.csv')

        # アサーション
        self.assertEqual(len(records), 2)  # 2025/09/15のレコードのみ
        self.assertEqual(records[0]['user_id'], '111111111111111111')
        self.assertEqual(records[0]['vc_name'], 'general-voice')  # VCチャンネル名が追加されている
        self.assertEqual(records[1]['user_id'], '222222222222222222')

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_aggregate_user_data(self, mock_build, mock_credentials):
        """ユーザーデータ集約のテスト"""
        # テストデータ
        all_records = [
            {'user_id': '111', 'user_name': 'user1', 'vc_name': 'general', 'present': 'TRUE'},
            {'user_id': '111', 'user_name': 'user1', 'vc_name': 'study', 'present': 'TRUE'},
            {'user_id': '222', 'user_name': 'user2', 'vc_name': 'general', 'present': 'TRUE'},
            {'user_id': '333', 'user_name': 'user3', 'vc_name': 'general', 'present': 'FALSE'},  # ログインしていない
        ]

        # メソッド実行
        aggregator = DailyAggregator()
        user_data = aggregator.aggregate_user_data(all_records)

        # アサーション
        self.assertEqual(len(user_data), 2)  # ユーザー111と222のみ
        self.assertEqual(user_data['111']['user_name'], 'user1')
        self.assertEqual(user_data['111']['vc_channels'], 'general, study')  # 2つのチャンネル
        self.assertEqual(user_data['111']['login_count'], 2)  # 2回ログイン
        self.assertEqual(user_data['222']['vc_channels'], 'general')
        self.assertEqual(user_data['222']['login_count'], 1)

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_update_user_statistics(self, mock_build, mock_credentials):
        """ユーザー統計更新のテスト"""
        # モックの設定
        aggregator = DailyAggregator(date(2025, 9, 15))
        aggregator.sheets_service = self.mock_sheets_service

        # 既存統計データのモック
        existing_stats = {
            'values': [
                ['user_id', 'user_name', 'last_login_date', 'consecutive_days', 'monthly_days', 'total_days', 'last_updated'],
                ['111', 'user1', '2025/09/14', '5', '10', '30', '2025/09/14 23:00:00'],  # 前日ログイン
                ['222', 'user2', '2025/09/13', '1', '8', '20', '2025/09/13 23:00:00'],  # 2日前ログイン
            ]
        }
        self.mock_sheets_service.spreadsheets().values().get().execute.return_value = existing_stats

        # 今日のユーザーデータ
        user_data = {
            '111': {'user_name': 'user1', 'vc_channels': 'general', 'login_count': 1},
            '333': {'user_name': 'user3', 'vc_channels': 'study', 'login_count': 1},  # 新規ユーザー
        }

        # メソッド実行
        aggregator.update_user_statistics('sheet123', user_data)

        # 更新データの確認
        update_call = self.mock_sheets_service.spreadsheets().values().update.call_args
        updated_values = update_call[1]['body']['values']

        # ヘッダー行の確認
        self.assertEqual(updated_values[0][0], 'user_id')

        # ユーザー111の更新確認（連続ログイン日数が6に増加）
        user111_row = next(row for row in updated_values if row[0] == '111')
        self.assertEqual(user111_row[3], 6)  # consecutive_days: 5 + 1 = 6
        self.assertEqual(user111_row[4], 11)  # monthly_days: 10 + 1 = 11
        self.assertEqual(user111_row[5], 31)  # total_days: 30 + 1 = 31

        # ユーザー222の確認（今日はログインしていないので変更なし）
        user222_row = next(row for row in updated_values if row[0] == '222')
        self.assertEqual(user222_row[3], 1)  # consecutive_days: そのまま
        self.assertEqual(user222_row[4], 8)  # monthly_days: そのまま
        self.assertEqual(user222_row[5], 20)  # total_days: そのまま

        # ユーザー333の確認（新規ユーザー）
        user333_row = next(row for row in updated_values if row[0] == '333')
        self.assertEqual(user333_row[3], 1)  # consecutive_days: 1
        self.assertEqual(user333_row[4], 1)  # monthly_days: 1
        self.assertEqual(user333_row[5], 1)  # total_days: 1

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_run_integration(self, mock_build, mock_credentials):
        """統合テスト（run メソッド）"""
        # モックの設定
        aggregator = DailyAggregator(date(2025, 9, 15))
        aggregator.drive_service = self.mock_drive_service
        aggregator.sheets_service = self.mock_sheets_service

        # CSVファイル取得のモック
        with patch.object(aggregator, 'get_csv_files_from_drive') as mock_get_csv:
            mock_get_csv.return_value = [
                {'id': 'csv1', 'name': 'general-voice.csv'},
                {'id': 'csv2', 'name': 'study-room.csv'}
            ]

            # CSV内容読み込みのモック
            with patch.object(aggregator, 'read_csv_content') as mock_read_csv:
                mock_read_csv.side_effect = [
                    [{'user_id': '111', 'user_name': 'user1', 'vc_name': 'general', 'present': 'TRUE'}],
                    [{'user_id': '222', 'user_name': 'user2', 'vc_name': 'study', 'present': 'TRUE'}]
                ]

                # Sheet ID取得のモック
                with patch.object(aggregator, 'get_sheet_id') as mock_get_sheet:
                    mock_get_sheet.return_value = 'sheet123'

                    # シート作成のモック
                    with patch.object(aggregator, 'ensure_sheets_exist'):
                        # 書き込みメソッドのモック
                        with patch.object(aggregator, 'write_daily_summary') as mock_write_daily:
                            with patch.object(aggregator, 'update_user_statistics') as mock_update_stats:
                                # メソッド実行
                                aggregator.run()

                                # アサーション
                                mock_get_csv.assert_called_once()  # CSVファイル取得
                                self.assertEqual(mock_read_csv.call_count, 2)  # 2つのCSVファイル読み込み
                                mock_get_sheet.assert_called_once()  # Sheet ID取得
                                mock_write_daily.assert_called_once()  # 日次サマリー書き込み
                                mock_update_stats.assert_called_once()  # 統計更新

                                # 集約データの確認
                                aggregated_data = mock_write_daily.call_args[0][1]
                                self.assertEqual(len(aggregated_data), 2)  # 2ユーザー分のデータ


class TestBase64Credentials(unittest.TestCase):
    """Base64エンコードされた認証情報のテスト"""

    @patch('daily_aggregator.service_account.Credentials')
    @patch('daily_aggregator.build')
    def test_base64_credentials(self, mock_build, mock_credentials):
        """Base64エンコードされた認証情報の処理テスト"""
        # サンプルのサービスアカウント情報
        service_account_info = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "key123",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }

        # Base64エンコード
        json_str = json.dumps(service_account_info)
        base64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

        # 環境変数の設定
        with patch.dict(os.environ, {
            'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64': base64_str,
            'GOOGLE_SHEET_NAME': 'Test_Sheet',
            'ALLOWED_VOICE_CHANNEL_IDS': '123456789'
        }):
            # インスタンス作成
            aggregator = DailyAggregator()

            # 認証情報が正しく処理されることを確認
            mock_credentials.from_service_account_info.assert_called_once()
            call_args = mock_credentials.from_service_account_info.call_args[0][0]
            self.assertEqual(call_args['project_id'], 'test-project')  # プロジェクトID確認
            self.assertEqual(call_args['client_email'], 'test@test.iam.gserviceaccount.com')  # メール確認


if __name__ == '__main__':
    unittest.main()