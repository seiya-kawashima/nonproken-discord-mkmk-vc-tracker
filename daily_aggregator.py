#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日次集計プログラム
Google Drive上のCSVファイルから当日のVCログイン情報を集計し、
ユーザーごとの統計情報をGoogle Sheetsに書き込む
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from collections import defaultdict
import io
from loguru import logger

# Google Drive/Sheets API関連のインポート
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# 環境変数から設定を読み込み
from dotenv import load_dotenv
load_dotenv()

# loguruの設定
logger.remove()  # デフォルトハンドラーを削除
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # コンソール出力（ファイル名と関数名付き）
# logsフォルダが存在しない場合は作成
os.makedirs("logs", exist_ok=True)  # logsフォルダを作成（既に存在する場合はスキップ）
logger.add("logs/daily_aggregator.log", rotation="10 MB", retention="7 days", level="INFO", encoding="utf-8", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # ファイル出力（ファイル名と関数名付き）


class DailyAggregator:
    """日次集計処理クラス"""

    def __init__(self, target_date: Optional[date] = None):
        """
        初期化

        Args:
            target_date: 集計対象日（Noneの場合は今日）
        """
        self.target_date = target_date or date.today()  # 集計対象日
        self.drive_service = None  # Google Drive APIサービス
        self.sheets_service = None  # Google Sheets APIサービス
        self.credentials = None  # 認証情報
        self.sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'VC_Tracker_Database')  # Sheets名
        self.allowed_vc_ids = self._parse_vc_ids()  # 対象VCチャンネルID

        # 初期化処理
        self._initialize_services()

    def _parse_vc_ids(self) -> List[str]:
        """環境変数からVCチャンネルIDリストを取得"""
        vc_ids_str = os.getenv('ALLOWED_VOICE_CHANNEL_IDS', '')  # 環境変数から取得
        if not vc_ids_str:
            logger.warning("ALLOWED_VOICE_CHANNEL_IDS not set")  # 警告ログ
            return []
        return [vc_id.strip() for vc_id in vc_ids_str.split(',')]  # カンマ区切りで分割

    def _initialize_services(self):
        """Google API サービスを初期化"""
        try:
            # 認証情報の取得
            self.credentials = self._get_credentials()

            # Drive APIサービスの構築
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            logger.info("Google Drive service initialized")  # 初期化成功ログ

            # Sheets APIサービスの構築
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheets service initialized")  # 初期化成功ログ

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")  # エラーログ
            raise

    def _get_credentials(self):
        """認証情報を取得"""
        # Base64エンコードされた認証情報を優先
        service_account_json_base64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64')

        if service_account_json_base64:
            # Base64デコード
            service_account_json = base64.b64decode(service_account_json_base64).decode('utf-8')
            service_account_info = json.loads(service_account_json)
            logger.info("Using Base64 encoded credentials")  # Base64認証使用ログ
        else:
            # ファイルパスから読み込み
            service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(f"Service account file not found: {service_account_file}")
            with open(service_account_file, 'r') as f:
                service_account_info = json.load(f)
            logger.info(f"Using credentials from file: {service_account_file}")  # ファイル認証使用ログ

        # スコープ設定
        scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        # 認証情報オブジェクトを作成
        return service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )

    def get_csv_files_from_drive(self) -> List[Dict[str, str]]:
        """
        Google DriveからCSVファイル一覧を取得

        Returns:
            CSVファイル情報のリスト [{id, name}, ...]
        """
        try:
            # discord_mokumoku_trackerフォルダを検索
            folder_query = "name='discord_mokumoku_tracker' and mimeType='application/vnd.google-apps.folder'"
            folder_results = self.drive_service.files().list(
                q=folder_query,
                fields="files(id, name)"
            ).execute()

            folders = folder_results.get('files', [])
            if not folders:
                logger.warning("discord_mokumoku_tracker folder not found")  # フォルダ未発見警告
                return []

            folder_id = folders[0]['id']  # フォルダID取得
            logger.info(f"Found folder: {folders[0]['name']} (ID: {folder_id})")  # フォルダ発見ログ

            # csvサブフォルダを検索
            csv_folder_query = f"'{folder_id}' in parents and name='csv' and mimeType='application/vnd.google-apps.folder'"
            csv_folder_results = self.drive_service.files().list(
                q=csv_folder_query,
                fields="files(id, name)"
            ).execute()

            csv_folders = csv_folder_results.get('files', [])
            if not csv_folders:
                logger.warning("csv subfolder not found")  # csvサブフォルダ未発見警告
                return []

            csv_folder_id = csv_folders[0]['id']  # csvフォルダID取得
            logger.info(f"Found csv folder (ID: {csv_folder_id})")  # csvフォルダ発見ログ

            # csvフォルダ内のCSVファイルを検索
            csv_query = f"'{csv_folder_id}' in parents and name contains '.csv'"
            csv_results = self.drive_service.files().list(
                q=csv_query,
                fields="files(id, name)"
            ).execute()

            csv_files = csv_results.get('files', [])
            logger.info(f"Found {len(csv_files)} CSV files")  # CSVファイル数ログ

            return csv_files

        except HttpError as e:
            logger.error(f"Failed to get CSV files: {e}")  # エラーログ
            return []

    def read_csv_content(self, file_id: str, file_name: str) -> List[Dict[str, str]]:
        """
        CSVファイルの内容を読み込み

        Args:
            file_id: ファイルID
            file_name: ファイル名

        Returns:
            CSVレコードのリスト
        """
        try:
            # ファイルをダウンロード
            request = self.drive_service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            # CSVをパース
            file_content.seek(0)
            csv_text = file_content.read().decode('utf-8')

            if not csv_text:
                logger.warning(f"Empty CSV file: {file_name}")  # 空ファイル警告
                return []

            lines = csv_text.strip().split('\n')
            if len(lines) < 2:  # ヘッダーのみの場合
                return []

            # ヘッダー行を取得
            headers = lines[0].split(',')

            # データ行をパース
            records = []
            target_date_str = self.target_date.strftime('%Y/%m/%d')  # 対象日付文字列

            for line in lines[1:]:
                values = line.split(',')
                if len(values) != len(headers):
                    continue

                record = dict(zip(headers, values))

                # 対象日のレコードのみ抽出
                if 'datetime_jst' in record and record['datetime_jst'].startswith(target_date_str):
                    # VCチャンネル名を追加（ファイル名から拡張子を除いたもの）
                    record['vc_name'] = file_name.replace('.csv', '')
                    records.append(record)

            logger.info(f"Read {len(records)} records for {target_date_str} from {file_name}")  # 読み込み結果ログ
            return records

        except Exception as e:
            logger.error(f"Failed to read CSV {file_name}: {e}")  # エラーログ
            return []

    def aggregate_user_data(self, all_records: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        ユーザーごとにデータを集約

        Args:
            all_records: 全CSVレコード

        Returns:
            ユーザーごとの集計データ
        """
        user_data = defaultdict(lambda: {
            'user_name': '',
            'vc_channels': set(),
            'login_count': 0
        })

        for record in all_records:
            if record.get('present', '').upper() == 'TRUE':  # ログイン中の場合
                user_id = record.get('user_id', '')
                if user_id:
                    user_data[user_id]['user_name'] = record.get('user_name', '')  # ユーザー名
                    user_data[user_id]['vc_channels'].add(record.get('vc_name', ''))  # VCチャンネル追加
                    user_data[user_id]['login_count'] += 1  # ログイン回数カウント

        # セットを文字列に変換
        for user_id, data in user_data.items():
            data['vc_channels'] = ', '.join(sorted(data['vc_channels']))

        logger.info(f"Aggregated data for {len(user_data)} users")  # 集計結果ログ
        return dict(user_data)

    def get_sheet_id(self) -> Optional[str]:
        """Google SheetsのIDを取得"""
        try:
            # Sheets名で検索
            query = f"name='{self.sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()

            sheets = results.get('files', [])
            if not sheets:
                logger.error(f"Sheet not found: {self.sheet_name}")  # シート未発見エラー
                return None

            sheet_id = sheets[0]['id']
            logger.info(f"Found sheet: {self.sheet_name} (ID: {sheet_id})")  # シート発見ログ
            return sheet_id

        except Exception as e:
            logger.error(f"Failed to get sheet ID: {e}")  # エラーログ
            return None

    def ensure_sheets_exist(self, sheet_id: str):
        """必要なシートが存在することを確認、なければ作成"""
        try:
            # 既存のシート一覧を取得
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()

            existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]

            # 必要なシート名
            required_sheets = ['daily_summary', 'user_statistics']

            # 不足しているシートを作成
            requests = []
            for sheet_name in required_sheets:
                if sheet_name not in existing_sheets:
                    requests.append({
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    })
                    logger.info(f"Creating sheet: {sheet_name}")  # シート作成ログ

            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()

                # ヘッダーを設定
                self._set_sheet_headers(sheet_id)

        except Exception as e:
            logger.error(f"Failed to ensure sheets exist: {e}")  # エラーログ
            raise

    def _set_sheet_headers(self, sheet_id: str):
        """シートのヘッダーを設定"""
        try:
            # daily_summaryのヘッダー
            daily_headers = [['date', 'user_id', 'user_name', 'vc_channels', 'login_count']]
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='daily_summary!A1:E1',
                valueInputOption='RAW',
                body={'values': daily_headers}
            ).execute()

            # user_statisticsのヘッダー
            stats_headers = [['user_id', 'user_name', 'last_login_date', 'consecutive_days',
                             'monthly_days', 'total_days', 'last_updated']]
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='user_statistics!A1:G1',
                valueInputOption='RAW',
                body={'values': stats_headers}
            ).execute()

            logger.info("Sheet headers set successfully")  # ヘッダー設定成功ログ

        except Exception as e:
            logger.error(f"Failed to set headers: {e}")  # エラーログ

    def write_daily_summary(self, sheet_id: str, user_data: Dict[str, Dict[str, Any]]):
        """日次サマリーをシートに書き込み"""
        try:
            # 書き込むデータを準備
            rows = []
            date_str = self.target_date.strftime('%Y/%m/%d')

            for user_id, data in user_data.items():
                rows.append([
                    date_str,
                    user_id,
                    data['user_name'],
                    data['vc_channels'],
                    data['login_count']
                ])

            if not rows:
                logger.info("No data to write to daily_summary")  # データなしログ
                return

            # 既存データの最終行を取得
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='daily_summary!A:A'
            ).execute()

            existing_rows = result.get('values', [])
            next_row = len(existing_rows) + 1

            # データを追記
            range_name = f'daily_summary!A{next_row}:E{next_row + len(rows) - 1}'
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            logger.info(f"Wrote {len(rows)} rows to daily_summary")  # 書き込み成功ログ

        except Exception as e:
            logger.error(f"Failed to write daily summary: {e}")  # エラーログ

    def update_user_statistics(self, sheet_id: str, user_data: Dict[str, Dict[str, Any]]):
        """ユーザー統計情報を更新"""
        try:
            # 既存の統計情報を読み込み
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='user_statistics!A:G'
            ).execute()

            existing_data = result.get('values', [])

            # ヘッダー行をスキップして、ユーザーIDをキーにした辞書を作成
            stats_dict = {}
            for row in existing_data[1:] if existing_data else []:
                if len(row) >= 7:
                    stats_dict[row[0]] = {
                        'user_name': row[1],
                        'last_login_date': row[2],
                        'consecutive_days': int(row[3]) if row[3] else 0,
                        'monthly_days': int(row[4]) if row[4] else 0,
                        'total_days': int(row[5]) if row[5] else 0,
                        'last_updated': row[6]
                    }

            # 統計情報を更新
            today_str = self.target_date.strftime('%Y/%m/%d')
            yesterday = self.target_date - timedelta(days=1)
            yesterday_str = yesterday.strftime('%Y/%m/%d')
            current_month = self.target_date.month

            for user_id in user_data:
                if user_id in stats_dict:
                    # 既存ユーザーの更新
                    stats = stats_dict[user_id]

                    # 連続ログイン日数の計算
                    if stats['last_login_date'] == yesterday_str:
                        stats['consecutive_days'] += 1  # 前日もログインしていた
                    else:
                        stats['consecutive_days'] = 1  # 連続が途切れた

                    # 月間ログイン日数の計算
                    last_login_date = datetime.strptime(stats['last_login_date'], '%Y/%m/%d').date()
                    if last_login_date.month == current_month:
                        stats['monthly_days'] += 1  # 同じ月
                    else:
                        stats['monthly_days'] = 1  # 月が変わった

                    # 累計ログイン日数
                    stats['total_days'] += 1

                    # 最終ログイン日と更新日時を更新
                    stats['last_login_date'] = today_str
                    stats['last_updated'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    stats['user_name'] = user_data[user_id]['user_name']  # ユーザー名も更新

                else:
                    # 新規ユーザー
                    stats_dict[user_id] = {
                        'user_name': user_data[user_id]['user_name'],
                        'last_login_date': today_str,
                        'consecutive_days': 1,
                        'monthly_days': 1,
                        'total_days': 1,
                        'last_updated': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    }

            # シートに書き込むデータを準備
            rows = [['user_id', 'user_name', 'last_login_date', 'consecutive_days',
                    'monthly_days', 'total_days', 'last_updated']]  # ヘッダー

            for user_id, stats in sorted(stats_dict.items()):
                rows.append([
                    user_id,
                    stats['user_name'],
                    stats['last_login_date'],
                    stats['consecutive_days'],
                    stats['monthly_days'],
                    stats['total_days'],
                    stats['last_updated']
                ])

            # シート全体を更新
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='user_statistics!A:G',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            logger.info(f"Updated statistics for {len(stats_dict)} users")  # 更新成功ログ

        except Exception as e:
            logger.error(f"Failed to update user statistics: {e}")  # エラーログ

    def run(self):
        """集計処理のメイン実行"""
        try:
            logger.info(f"Starting aggregation for {self.target_date}")  # 開始ログ

            # 1. CSVファイル一覧を取得
            csv_files = self.get_csv_files_from_drive()
            if not csv_files:
                logger.warning("No CSV files found")  # CSVファイルなし警告
                return

            # 2. 各CSVファイルからデータを読み込み
            all_records = []
            for csv_file in csv_files:
                records = self.read_csv_content(csv_file['id'], csv_file['name'])
                all_records.extend(records)

            logger.info(f"Total records read: {len(all_records)}")  # 総レコード数ログ

            # 3. ユーザーごとにデータを集約
            user_data = self.aggregate_user_data(all_records)

            if not user_data:
                logger.info("No user data to aggregate")  # 集約データなしログ
                return

            # 4. Google SheetsのIDを取得
            sheet_id = self.get_sheet_id()
            if not sheet_id:
                logger.error("Cannot proceed without sheet ID")  # シートID取得失敗エラー
                return

            # 5. 必要なシートを確認・作成
            self.ensure_sheets_exist(sheet_id)

            # 6. daily_summaryシートに書き込み
            self.write_daily_summary(sheet_id, user_data)

            # 7. user_statisticsシートを更新
            self.update_user_statistics(sheet_id, user_data)

            logger.info("Aggregation completed successfully")  # 完了ログ

        except Exception as e:
            logger.error(f"Aggregation failed: {e}")  # エラーログ
            raise


def main():
    """メイン関数"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='Daily VC login aggregator')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # デバッグモードの設定
    if args.debug:
        logger.remove()  # 既存のハンドラーを削除
        logger.add(sys.stderr, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")  # DEBUGレベルでコンソール出力
        logger.add("daily_aggregator.log", rotation="10 MB", retention="7 days", level="DEBUG", encoding="utf-8")  # DEBUGレベルでファイル出力

    # 対象日付の設定
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}")  # 日付フォーマットエラー
            sys.exit(1)

    # 集計処理を実行
    aggregator = DailyAggregator(target_date)
    aggregator.run()


if __name__ == '__main__':
    main()