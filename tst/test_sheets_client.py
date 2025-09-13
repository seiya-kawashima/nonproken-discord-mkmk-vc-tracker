"""Google Sheetsクライアントのユニットテスト"""  # テストモジュールの説明

import pytest  # テストフレームワーク
from unittest.mock import Mock, patch, MagicMock  # モック用
from datetime import datetime, timezone, timedelta  # 日時処理用
import gspread  # Google Sheets API用

from src.sheets_client import SheetsClient  # テスト対象クラス


class TestSheetsClient:
    """SheetsClientクラスのテスト"""  # テストクラスの説明

    def test_init(self):
        """初期化処理のテスト"""  # テストの説明
        service_account_json = "test.json"  # テスト用JSONファイル
        sheet_name = "Test Sheet"  # テスト用シート名
        
        client = SheetsClient(service_account_json, sheet_name)  # インスタンス作成
        
        assert client.service_account_json == service_account_json  # JSONファイルパスが正しいか
        assert client.sheet_name == sheet_name  # シート名が正しいか
        assert client.client is None  # クライアントが未初期化か
        assert client.sheet is None  # シートが未初期化か
        assert client.worksheet is None  # ワークシートが未初期化か

    @patch('src.sheets_client.gspread.authorize')
    @patch('src.sheets_client.Credentials')
    def test_connect_success(self, mock_creds, mock_authorize):
        """接続成功のテスト"""  # テストの説明
        # モックの設定
        mock_creds_instance = Mock()  # 認証情報モック
        mock_creds.from_service_account_file.return_value = mock_creds_instance  # 認証情報返す
        
        mock_client = Mock()  # クライアントモック
        mock_authorize.return_value = mock_client  # クライアント返す
        
        mock_sheet = Mock()  # シートモック
        mock_client.open.return_value = mock_sheet  # シート返す
        
        mock_worksheet = Mock()  # ワークシートモック
        mock_sheet.worksheet.return_value = mock_worksheet  # ワークシート返す
        
        # テスト実行
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.connect()  # 接続
        
        # アサーション
        mock_creds.from_service_account_file.assert_called_once()  # 認証ファイル読み込みが呼ばれたか
        mock_authorize.assert_called_once_with(mock_creds_instance)  # 認証が呼ばれたか
        mock_client.open.assert_called_once_with("Test Sheet")  # シートが開かれたか
        mock_sheet.worksheet.assert_called_once_with('daily_presence')  # ワークシートが取得されたか
        
        assert client.client == mock_client  # クライアントが設定されたか
        assert client.sheet == mock_sheet  # シートが設定されたか
        assert client.worksheet == mock_worksheet  # ワークシートが設定されたか

    @patch('src.sheets_client.gspread.authorize')
    @patch('src.sheets_client.Credentials')
    def test_connect_create_worksheet(self, mock_creds, mock_authorize):
        """ワークシート作成のテスト"""  # テストの説明
        # モックの設定
        mock_creds_instance = Mock()  # 認証情報モック
        mock_creds.from_service_account_file.return_value = mock_creds_instance  # 認証情報返す
        
        mock_client = Mock()  # クライアントモック
        mock_authorize.return_value = mock_client  # クライアント返す
        
        mock_sheet = Mock()  # シートモック
        mock_client.open.return_value = mock_sheet  # シート返す
        
        # ワークシートが見つからない場合の設定
        mock_sheet.worksheet.side_effect = gspread.WorksheetNotFound("Not found")  # エラーを発生
        
        mock_new_worksheet = Mock()  # 新しいワークシートモック
        mock_sheet.add_worksheet.return_value = mock_new_worksheet  # 新しいワークシート返す
        
        # テスト実行
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.connect()  # 接続
        
        # アサーション
        mock_sheet.add_worksheet.assert_called_once_with(  # ワークシート作成が呼ばれたか
            title='daily_presence',  # タイトル
            rows=1000,  # 行数
            cols=5  # 列数
        )
        mock_new_worksheet.update.assert_called_once()  # ヘッダー更新が呼ばれたか
        assert client.worksheet == mock_new_worksheet  # 新しいワークシートが設定されたか

    def test_upsert_presence_not_connected(self):
        """未接続時のupsertテスト"""  # テストの説明
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        
        with pytest.raises(RuntimeError, match="Not connected"):  # エラーが発生するか
            client.upsert_presence([])  # upsert実行

    @patch('src.sheets_client.datetime')
    def test_upsert_presence_new_records(self, mock_datetime):
        """新規レコード追加のテスト"""  # テストの説明
        # 日時のモック
        mock_now = Mock()  # 現在時刻モック
        mock_now.strftime.return_value = "2025-09-11"  # 日付文字列返す
        mock_datetime.now.return_value = mock_now  # 現在時刻返す
        
        # ワークシートのモック
        mock_worksheet = Mock()  # ワークシートモック
        mock_worksheet.get_all_records.return_value = []  # 既存データなし
        
        # クライアントの設定
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.worksheet = mock_worksheet  # ワークシート設定
        
        # テストデータ
        members = [  # メンバーリスト
            {
                "guild_id": "123",  # ギルドID
                "user_id": "456",  # ユーザーID
                "user_name": "test#1234"  # ユーザー名
            }
        ]
        
        # テスト実行
        result = client.upsert_presence(members)  # upsert実行
        
        # アサーション
        mock_worksheet.append_rows.assert_called_once()  # append_rowsが呼ばれたか
        assert result["new"] == 1  # 新規1件か
        assert result["updated"] == 0  # 更新0件か

    @patch('src.sheets_client.datetime')
    def test_upsert_presence_existing_records(self, mock_datetime):
        """既存レコードがある場合のテスト"""  # テストの説明
        # 日時のモック
        mock_now = Mock()  # 現在時刻モック
        mock_now.strftime.return_value = "2025-09-11"  # 日付文字列返す
        mock_datetime.now.return_value = mock_now  # 現在時刻返す
        
        # 既存データ
        existing_data = [  # 既存データリスト
            {
                "date_jst": "2025-09-11",  # 日付
                "guild_id": "123",  # ギルドID
                "user_id": "456",  # ユーザーID
                "user_name": "test#1234",  # ユーザー名
                "present": "TRUE"  # 出席済み
            }
        ]
        
        # ワークシートのモック
        mock_worksheet = Mock()  # ワークシートモック
        mock_worksheet.get_all_records.return_value = existing_data  # 既存データ返す
        
        # クライアントの設定
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.worksheet = mock_worksheet  # ワークシート設定
        
        # テストデータ（既存と同じ）
        members = [  # メンバーリスト
            {
                "guild_id": "123",  # ギルドID
                "user_id": "456",  # ユーザーID
                "user_name": "test#1234"  # ユーザー名
            }
        ]
        
        # テスト実行
        result = client.upsert_presence(members)  # upsert実行
        
        # アサーション
        mock_worksheet.append_rows.assert_not_called()  # append_rowsが呼ばれていないか
        assert result["new"] == 0  # 新規0件か
        assert result["updated"] == 0  # 更新0件か（既にTRUEなので）

    def test_get_total_days_not_connected(self):
        """未接続時の通算日数取得テスト"""  # テストの説明
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        
        with pytest.raises(RuntimeError, match="Not connected"):  # エラーが発生するか
            client.get_total_days("123")  # 通算日数取得

    def test_get_total_days_success(self):
        """通算日数取得成功のテスト"""  # テストの説明
        # テストデータ
        all_data = [  # 全データリスト
            {"user_id": "123", "present": "TRUE"},  # ユーザー123、出席
            {"user_id": "123", "present": "TRUE"},  # ユーザー123、出席
            {"user_id": "456", "present": "TRUE"},  # ユーザー456、出席
            {"user_id": "123", "present": "FALSE"},  # ユーザー123、欠席
        ]
        
        # ワークシートのモック
        mock_worksheet = Mock()  # ワークシートモック
        mock_worksheet.get_all_records.return_value = all_data  # データ返す
        
        # クライアントの設定
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.worksheet = mock_worksheet  # ワークシート設定
        
        # テスト実行
        result = client.get_total_days("123")  # ユーザー123の通算日数取得
        
        # アサーション
        assert result == 2  # 2日（TRUEが2つ）か確認

    def test_get_today_members_not_connected(self):
        """未接続時の今日のメンバー取得テスト"""  # テストの説明
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        
        with pytest.raises(RuntimeError, match="Not connected"):  # エラーが発生するか
            client.get_today_members()  # 今日のメンバー取得

    @patch('src.sheets_client.datetime')
    def test_get_today_members_success(self, mock_datetime):
        """今日のメンバー取得成功のテスト"""  # テストの説明
        # 日時のモック
        mock_now = Mock()  # 現在時刻モック
        mock_now.strftime.return_value = "2025-09-11"  # 日付文字列返す
        mock_datetime.now.return_value = mock_now  # 現在時刻返す
        
        # テストデータ
        all_data = [  # 全データリスト
            {"date_jst": "2025-09-11", "user_id": "123", "present": "TRUE"},  # 今日、出席
            {"date_jst": "2025-09-11", "user_id": "456", "present": "FALSE"},  # 今日、欠席
            {"date_jst": "2025-09-10", "user_id": "789", "present": "TRUE"},  # 昨日、出席
        ]
        
        # ワークシートのモック
        mock_worksheet = Mock()  # ワークシートモック
        mock_worksheet.get_all_records.return_value = all_data  # データ返す
        
        # クライアントの設定
        client = SheetsClient("test.json", "Test Sheet")  # インスタンス作成
        client.worksheet = mock_worksheet  # ワークシート設定
        
        # テスト実行
        result = client.get_today_members()  # 今日のメンバー取得
        
        # アサーション
        assert len(result) == 1  # 1件（今日かつTRUE）か確認
        assert result[0]["user_id"] == "123"  # ユーザーIDが正しいか