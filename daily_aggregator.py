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
import jpholiday  # 日本の祝日判定用
from loguru import logger
from slack_sdk import WebClient  # Slack APIクライアント
from slack_sdk.errors import SlackApiError  # Slack APIエラー

# Google Drive/Sheets API関連のインポート
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# 環境変数から設定を読み込み
from dotenv import load_dotenv
load_dotenv()

# config.pyから設定を読み込み
from config import get_config, get_environment_from_arg, Environment

# loguruの設定
logger.remove()  # デフォルトハンドラーを削除
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # コンソール出力（ファイル名と関数名を先に表示）

# logsフォルダが存在しない場合は作成
os.makedirs("logs", exist_ok=True)  # logsフォルダを作成（既に存在する場合はスキップ）

# 現在の日付を取得（YYYYMMDD形式）
current_date = datetime.now().strftime("%Y%m%d")  # 日付取得

# 処理別のログファイル設定
# 1. メイン処理のログ
logger.add(f"logs/daily_aggregator_{current_date}.log",
          rotation="10 MB",
          retention="7 days",
          level="INFO",
          encoding="utf-8",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {name}.py | def: {function}",
          filter=lambda record: "get_csv" not in record["function"] and "aggregate" not in record["function"])  # メイン処理ログ

# 2. CSVファイル取得処理のログ
logger.add(f"logs/csv_fetch_{current_date}.log",
          rotation="10 MB",
          retention="7 days",
          level="DEBUG",
          encoding="utf-8",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {name}.py | def: {function}",
          filter=lambda record: "get_csv" in record["function"] or "read_csv" in record["function"])  # CSV取得ログ

# 3. 集計処理のログ
logger.add(f"logs/aggregation_{current_date}.log",
          rotation="10 MB",
          retention="7 days",
          level="INFO",
          encoding="utf-8",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {name}.py | def: {function}",
          filter=lambda record: "aggregate" in record["function"] or "write" in record["function"] or "update" in record["function"])  # 集計処理ログ

# 4. エラーログ（全てのエラーを記録）
logger.add(f"logs/error_{current_date}.log",
          rotation="10 MB",
          retention="30 days",
          level="ERROR",
          encoding="utf-8",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # エラーログ


class DailyAggregator:
    """日次集計処理クラス"""

    def __init__(self, target_date: Optional[date] = None, env: Environment = Environment.PRD, output_pattern: str = 'slack'):
        """
        初期化

        Args:
            target_date: 集計対象日（Noneの場合は今日）
            env: 実行環境
            output_pattern: 出力パターン ('discord' or 'slack')
        """
        self.target_date = target_date or date.today()  # 集計対象日
        self.env = env  # 実行環境
        self.output_pattern = output_pattern  # 出力パターン
        self.drive_service = None  # Google Drive APIサービス
        self.sheets_service = None  # Google Sheets APIサービス
        self.credentials = None  # 認証情報
        self.user_mapping = {}  # Discord ID→SlackメンションIDのマッピング
        self.slack_client = None  # Slack APIクライアント
        self.config = None  # 設定情報

        # config.pyから設定を取得
        self.config = get_config(env)  # すべての設定を取得

        # Google Drive関連の設定を取得（デフォルト値を設定）
        self.google_drive_folder_path = self.config.get('google_drive_base_folder', 'discord_mokumoku_tracker')  # Google Driveベースフォルダパス
        folder_structure = self.config.get('google_drive_folder_structure', {})  # Google Driveフォルダ構造
        self.sheet_name = folder_structure.get('spreadsheet', f"もくもくトラッカー_{self.config['suffix']}")  # Sheets名
        self.google_drive_folder_structure = folder_structure  # Google Driveフォルダ構造定義
        self.allowed_vc_ids = self.config.get('discord_channel_ids', self.config.get('channel_ids'))  # Discord対象VCチャンネルID
        self.suffix = self.config['suffix']  # 環境サフィックス (0_PRD/1_TST/2_DEV)
        self.google_drive_discord_slack_mapping_sheet_id = self.config.get('google_drive_discord_slack_mapping_sheet_id')  # Discord-Slackユーザーマッピングシート ID
        self.slack_token = self.config.get('slack_token')  # Slack Botトークン
        self.slack_channel = self.config.get('slack_channel')  # SlackチャンネルID

        # 初期化処理
        self._initialize_services()


    def _initialize_services(self):
        """Google API サービスを初期化"""
        try:
            # 認証情報の取得
            self.credentials = self._get_credentials()

            # Drive APIサービスの構築
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            logger.info("📁 Google Driveへの接続が完了しました")  # 初期化成功ログ

            # Sheets APIサービスの構築
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("📊 Google Sheetsへの接続が完了しました")  # 初期化成功ログ

            # Slackクライアントの初期化
            if self.slack_token:
                self.slack_client = WebClient(token=self.slack_token)
                logger.info("💬 Slackクライアントを初期化しました")  # Slack初期化
            else:
                logger.warning("⚠️ Slackトークンが設定されていません")  # Slack未設定

            # ユーザーマッピングを読み込み
            self._load_user_mapping()

        except Exception as e:
            logger.error(f"⚠️ サービスの初期化に失敗しました: {e}")  # エラーログ
            raise

    def _get_credentials(self):
        """認証情報を取得"""
        # config.pyから認証情報を取得
        config = get_config(self.env)  # すべての設定を取得
        google_drive_service_account_json_base64 = config.get('google_drive_service_account_json_base64', config.get('service_account_json_base64'))  # Google Drive Base64認証情報
        service_account_file = config.get('google_drive_service_account_json', config.get('service_account_json'))  # Google Driveサービスアカウントファイルパス

        if google_drive_service_account_json_base64:
            # Base64デコード
            service_account_json = base64.b64decode(google_drive_service_account_json_base64).decode('utf-8')
            service_account_info = json.loads(service_account_json)
            logger.info("🔐 環境変数から認証情報を取得しました（Base64形式）")  # Base64認証使用ログ
        else:
            # ファイルパスから読み込み
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(f"Service account file not found: {service_account_file}")
            with open(service_account_file, 'r') as f:
                service_account_info = json.load(f)
            logger.info(f"🔐 認証ファイルを読み込みました: {service_account_file}")  # ファイル認証使用ログ

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

    def _load_user_mapping(self):
        """ユーザーマッピングシートからデータを読み込み"""
        try:
            # シートIDが設定されていない場合はエラー
            if not self.google_drive_discord_slack_mapping_sheet_id:
                logger.error(f"❌ GOOGLE_DRIVE_DISCORD_SLACK_MAPPING_SHEET_ID_{self.suffix}が設定されていません")  # 設定エラー
                logger.error(f"   環境変数にシートIDを設定してください: GOOGLE_DRIVE_DISCORD_SLACK_MAPPING_SHEET_ID_{self.suffix}=<シートID>")  # 設定方法
                raise ValueError(f"Discord-SlackマッピングシートIDが設定されていません（GOOGLE_DRIVE_DISCORD_SLACK_MAPPING_SHEET_ID_{self.suffix}）")  # エラー

            logger.info(f"📖 Discord-SlackマッピングシートIDを使用: {self.google_drive_discord_slack_mapping_sheet_id}")  # シートID使用

            # シートからデータを読み込み
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.google_drive_discord_slack_mapping_sheet_id,
                range='user_mapping!A2:C1000'  # ヘッダーを除くデータ範囲
            ).execute()  # データ取得

            rows = result.get('values', [])  # データ行
            for row in rows:
                if len(row) >= 3:
                    discord_user_id = row[0]  # DiscordユーザーID
                    slack_mention_id = row[2]  # SlackメンションID
                    if discord_user_id and slack_mention_id:
                        self.user_mapping[discord_user_id] = slack_mention_id  # マッピング登録

            logger.info(f"✅ {len(self.user_mapping)}件のユーザーマッピングを読み込みました")  # 読み込み完了

        except Exception as e:
            logger.warning(f"⚠️ ユーザーマッピングの読み込みに失敗: {e}")  # エラー
            # マッピングがなくても処理継続

    def is_business_day(self, target_date: date) -> bool:
        """
        営業日か否かを判定

        Args:
            target_date: 判定対象日

        Returns:
            営業日の場合True、土日祝日の場合False
        """
        # 土日の判定 (weekday(): 0=月, 5=土, 6=日)
        if target_date.weekday() >= 5:  # 土日
            return False

        # 祝日の判定
        if jpholiday.is_holiday(target_date):  # 祝日
            return False

        return True  # 営業日

    def get_previous_business_day(self, target_date: date) -> date:
        """
        直前の営業日を取得

        Args:
            target_date: 基準日

        Returns:
            直前の営業日
        """
        previous_date = target_date - timedelta(days=1)  # 1日前
        while not self.is_business_day(previous_date):  # 営業日でない間
            previous_date -= timedelta(days=1)  # さらに1日前
        return previous_date  # 営業日を返す

    def get_csv_files_from_drive(self) -> List[Dict[str, str]]:
        """
        Google DriveからCSVファイル一覧を取得

        Returns:
            CSVファイル情報のリスト [{id, name}, ...]
        """
        try:
            logger.info(f"🔍 CSVファイルの検索を開始します")  # 検索開始ログ
            logger.info(f"📍 検索パス: {self.google_drive_folder_path}")  # 検索パス表示

            # フォルダパスからフォルダ階層を取得
            folder_parts = self.google_drive_folder_path.split('/')  # パスを分割
            if not folder_parts:
                logger.warning("⚠️ フォルダパスが無効です")  # 無効なパス警告
                return []

            # ルートフォルダを検索（共有ドライブ対応）
            root_folder_name = folder_parts[0]  # ルートフォルダ名
            folder_query = f"name='{root_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            folder_results = self.drive_service.files().list(
                q=folder_query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='allDrives'
            ).execute()

            folders = folder_results.get('files', [])
            if not folders:
                logger.warning(f"⚠️ Google Drive上に '{root_folder_name}' フォルダが見つかりません")  # フォルダ未発見警告
                return []

            folder_id = folders[0]['id']  # フォルダID取得
            logger.info(f"📂 フォルダを発見: {folders[0]['name']}")  # フォルダ発見ログ

            # 残りのフォルダ階層を順に探索
            current_folder_id = folder_id
            for folder_name in folder_parts[1:]:
                subfolder_query = f"'{current_folder_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
                subfolder_results = self.drive_service.files().list(
                    q=subfolder_query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                subfolders = subfolder_results.get('files', [])
                if not subfolders:
                    logger.warning(f"⚠️ サブフォルダ '{folder_name}' が見つかりません")  # サブフォルダ未発見警告
                    return []

                current_folder_id = subfolders[0]['id']  # 次のフォルダID
                logger.info(f"📂 サブフォルダを発見: {folder_name}")  # フォルダ発見ログ

            # 最終的なフォルダIDを保存（discord_mokumoku_trackerフォルダ）
            base_folder_id = current_folder_id

            # discord_mokumoku_tracker内のVCチャンネルフォルダを検索
            full_path = '/'.join(folder_parts)  # 完全なパスを構築
            logger.info(f"📂 現在のフォルダ: {full_path}")  # 現在位置ログ
            logger.info(f"🔎 VCチャンネルフォルダを検索中...")  # チャンネルフォルダ検索ログ
            channel_folder_query = f"'{base_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            channel_folder_results = self.drive_service.files().list(
                q=channel_folder_query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            channel_folders = channel_folder_results.get('files', [])
            logger.info(f"📁 {len(channel_folders)}個のVCチャンネルフォルダを発見しました")  # チャンネルフォルダ数ログ
            if channel_folders:
                logger.info(f"📝 発見したチャンネルフォルダ: {', '.join([f['name'] for f in channel_folders])}")  # チャンネル名一覧

            csv_files = []
            # 各VCチャンネルフォルダ内のcsvサブフォルダを検索
            for channel_folder in channel_folders:
                channel_folder_id = channel_folder['id']
                channel_name = channel_folder['name']

                # csvサブフォルダを検索
                csv_folder_query = f"'{channel_folder_id}' in parents and name='csv' and mimeType='application/vnd.google-apps.folder'"
                csv_folder_results = self.drive_service.files().list(
                    q=csv_folder_query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                csv_folders = csv_folder_results.get('files', [])
                if not csv_folders:
                    logger.info(f"  ℹ️ {channel_name}フォルダ内にcsvフォルダがありません")  # csvフォルダなしログ
                    continue

                csv_folder_id = csv_folders[0]['id']

                # csvフォルダ内の環境に応じたCSVファイルを検索
                target_csv_name = f"{self.suffix}.csv"  # 対象CSVファイル名
                search_path = f"{full_path}/{channel_name}/csv/{target_csv_name}"  # 検索パスを構築
                logger.debug(f"🔍 CSVファイルを検索中: {search_path}")  # デバッグログ
                csv_query = f"'{csv_folder_id}' in parents and name='{target_csv_name}'"
                csv_results = self.drive_service.files().list(
                    q=csv_query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                channel_csv_files = csv_results.get('files', [])
                csv_files.extend(channel_csv_files)
                if channel_csv_files:
                    for csv_file in channel_csv_files:
                        logger.debug(f"  ✅ 発見: {search_path}")  # CSVファイル名表示
                        logger.info(f"  ✅ CSVファイルを発見: {search_path}")  # CSVファイル発見通知
                else:
                    logger.debug(f"  ⚠️ {target_csv_name}が見つかりません")  # CSVファイルなしログ
                    logger.info(f"  ℹ️ {channel_name}/csvフォルダ内に{target_csv_name}がありません")  # 詳細情報
            logger.info(f"📝 合計{len(csv_files)}個のCSVファイルを発見しました")  # CSVファイル数ログ

            return csv_files

        except HttpError as e:
            logger.error(f"⚠️ CSVファイルの取得に失敗しました: {e}")  # エラーログ
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

            # CSVをパース（BOMを除去）
            file_content.seek(0)
            csv_text = file_content.read().decode('utf-8-sig')  # BOMを自動除去

            if not csv_text:
                logger.warning(f"⚠️ CSVファイルが空です: {file_name}")  # 空ファイル警告
                return []

            lines = csv_text.strip().split('\n')
            if len(lines) < 2:  # ヘッダーのみの場合
                return []

            # ヘッダー行を取得（改行コードも除去）
            headers = [h.strip() for h in lines[0].split(',')]
            logger.debug(f"📋 CSVヘッダー: {headers}")  # ヘッダー情報ログ

            # 日付列の確認
            if 'datetime_jst' in headers:
                logger.info(f"✅ datetime_jst列を発見（インデックス: {headers.index('datetime_jst')}）")  # 日付列確認
            else:
                logger.warning(f"⚠️ datetime_jst列が見つかりません。利用可能な列: {headers}")  # 日付列なし警告

            # データ行をパース
            records = []
            # 両方の日付形式をサポート（ゼロパディングあり/なし）
            target_date_str = self.target_date.strftime('%Y/%m/%d')  # 対象日付文字列（ゼロパディングあり）
            target_date_str_no_pad = self.target_date.strftime('%Y/%-m/%-d') if os.name != 'nt' else self.target_date.strftime('%Y/%#m/%#d')  # ゼロパディングなし
            logger.info(f"🔍 検索対象日付: {target_date_str} または {target_date_str_no_pad}")  # 検索日付ログ

            # 最初の数行をサンプル表示
            sample_count = min(3, len(lines) - 1)  # 最大3行表示
            if sample_count > 0:
                logger.debug(f"📊 CSVデータサンプル（最初の{sample_count}行）:")  # サンプルデータヘッダー

            for idx, line in enumerate(lines[1:]):
                values = line.split(',')
                if len(values) != len(headers):
                    continue

                record = dict(zip(headers, values))

                # サンプルデータ表示
                if idx < sample_count:
                    if 'datetime_jst' in record:
                        logger.debug(f"  行{idx+1}: datetime_jst='{record['datetime_jst']}'")  # サンプルデータ表示
                    else:
                        logger.debug(f"  行{idx+1}: {record}")  # サンプルデータ全体

                # 対象日のレコードのみ抽出
                if 'datetime_jst' in record:
                    datetime_value = record['datetime_jst'].strip()  # 改行コード等を除去
                    # 両方の日付形式でチェック
                    if datetime_value.startswith(target_date_str) or datetime_value.startswith(target_date_str_no_pad):
                        # VCチャンネル名を追加（ファイル名から拡張子を除いたもの）
                        record['vc_name'] = file_name.replace('.csv', '')
                        records.append(record)
                        logger.debug(f"  ✅ マッチ: {datetime_value}")  # マッチしたレコード

            logger.info(f"📖 {file_name}から{target_date_str}の{len(records)}件のデータを読み込みました")  # 読み込み結果ログ
            return records

        except Exception as e:
            logger.error(f"⚠️ CSVファイル {file_name} の読み込みに失敗しました: {e}")  # エラーログ
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
            # present列が削除されたため、全レコードを集計対象とする
            user_id = record.get('user_id', '')
            if user_id:
                user_data[user_id]['user_name'] = record.get('user_name', '')  # ユーザー名
                # vc_name列がない場合はファイルパスから取得（互換性のため）
                vc_name = record.get('vc_name', 'unknown')  # VCチャンネル名
                user_data[user_id]['vc_channels'].add(vc_name)  # VCチャンネル追加
                user_data[user_id]['login_count'] += 1  # ログイン回数カウント

        # セットを文字列に変換
        for user_id, data in user_data.items():
            data['vc_channels'] = ', '.join(sorted(data['vc_channels']))

        logger.info(f"📈 {len(user_data)}名のユーザーデータを集計しました")  # 集計結果ログ
        return dict(user_data)

    def get_sheet_id(self) -> Optional[str]:
        """Google SheetsのIDを取得"""
        try:
            # Sheets名で検索（共有ドライブ対応）
            query = f"name='{self.sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='allDrives'
            ).execute()

            sheets = results.get('files', [])
            if not sheets:
                logger.error(f"⚠️ スプレッドシートが見つかりません: {self.sheet_name}")  # シート未発見エラー
                return None

            sheet_id = sheets[0]['id']
            logger.info(f"📊 スプレッドシートを発見: {self.sheet_name}")  # シート発見ログ
            return sheet_id

        except Exception as e:
            logger.error(f"⚠️ シートIDの取得に失敗しました: {e}")  # エラーログ
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
                    logger.info(f"📄 新しいシートを作成中: {sheet_name}")  # シート作成ログ

            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()

                # ヘッダーを設定
                self._set_sheet_headers(sheet_id)

        except Exception as e:
            logger.error(f"⚠️ シートの確認・作成に失敗しました: {e}")  # エラーログ
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
                             'total_days', 'last_updated']]
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='user_statistics!A1:F1',
                valueInputOption='RAW',
                body={'values': stats_headers}
            ).execute()

            logger.info("✅ シートのヘッダーを設定しました")  # ヘッダー設定成功ログ

        except Exception as e:
            logger.error(f"⚠️ ヘッダーの設定に失敗しました: {e}")  # エラーログ

    def post_to_slack(self, user_data: Dict[str, Dict[str, Any]], stats_dict: Dict[str, Dict[str, Any]]) -> str:
        """集計結果をSlackに投稿"""
        try:
            # メッセージを構築
            date_str = self.target_date.strftime('%Y年%m月%d日')
            message_lines = [f"📅 [{date_str}] のVCログインレポート", ""]

            if user_data:
                message_lines.append("本日の参加者：")

                # ユーザー情報を整形
                for user_id, data in sorted(user_data.items(), key=lambda x: x[1]['user_name']):
                    # 統計情報を取得
                    stats = stats_dict.get(user_id, {})
                    consecutive = stats.get('consecutive_days', 1)
                    total = stats.get('total_days', 1)

                    # ユーザー名を取得（マッピングまたはDiscord名）
                    if self.output_pattern == 'slack' and user_id in self.user_mapping:
                        user_display = f"<@{self.user_mapping[user_id]}>"
                    else:
                        user_display = data['user_name']

                    # メッセージを構築
                    if consecutive == 1:
                        message_lines.append(f"{user_display} さん　１日目のログイン（累計{total}日）")
                    else:
                        message_lines.append(f"{user_display} さん　{consecutive}日連続ログイン（累計{total}日）")

                message_lines.append("")
                message_lines.append(f"本日の参加者数： {len(user_data)}名")
            else:
                message_lines.append("本日のVCログイン者はいませんでした。")

            message = "\n".join(message_lines)

            # Slackに投稿
            if self.output_pattern == 'slack' and self.slack_client and self.slack_channel:
                try:
                    response = self.slack_client.chat_postMessage(
                        channel=self.slack_channel,
                        text=message
                    )
                    logger.info(f"✅ Slackにレポートを投稿しました")  # 投稿成功
                except SlackApiError as e:
                    logger.warning(f"⚠️ Slack投稿エラー: {e.response['error']}")  # Slackエラー
                    logger.info("📝 コンソールに出力します")  # コンソール出力
                    print(message)
            else:
                # Discord出力モードまたはSlackが設定されていない場合はコンソール出力
                logger.info("📝 コンソールに出力します")  # コンソール出力
                print(message)

            return message

        except SlackApiError as e:
            logger.error(f"❌ Slack投稿エラー: {e.response['error']}")  # Slackエラー
            raise
        except Exception as e:
            logger.error(f"❌ レポート作成エラー: {e}")  # エラー
            raise

    def get_user_statistics_sheet_id(self) -> str:
        """ユーザー統計シートのIDを取得または作成"""
        try:
            # シート名を生成
            sheet_name = f"UserStatistics_{self.suffix}"  # 統計シート名

            # シートを検索
            query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()  # 検索実行

            files = results.get('files', [])  # ファイルリスト
            if files:
                logger.info(f"📊 既存の統計シートを発見: {sheet_name}")  # 発見
                return files[0]['id']  # シートID返却

            # シートが存在しない場合は作成
            logger.info(f"📄 新規統計シートを作成: {sheet_name}")  # 作成ログ
            spreadsheet = {
                'properties': {'title': sheet_name},
                'sheets': [{
                    'properties': {
                        'title': 'statistics',
                        'gridProperties': {'frozenRowCount': 1}
                    }
                }]
            }

            result = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()  # 作成
            sheet_id = result['spreadsheetId']  # ID取得

            # ヘッダーを設定
            headers = [['user_id', 'user_name', 'last_login_date', 'consecutive_days', 'total_days', 'last_updated']]  # ヘッダー
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='statistics!A1:F1',
                valueInputOption='RAW',
                body={'values': headers}
            ).execute()  # ヘッダー書き込み

            return sheet_id  # ID返却

        except Exception as e:
            logger.error(f"❌ 統計シートの取得/作成エラー: {e}")  # エラー
            raise

    def update_user_statistics(self, user_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """ユーザー統計情報を更新して返却"""
        try:
            # 統計シートのIDを取得
            sheet_id = self.get_user_statistics_sheet_id()  # シートID

            # 既存の統計情報を読み込み
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='statistics!A:F'
            ).execute()  # データ取得

            existing_data = result.get('values', [])  # 既存データ

            # ヘッダー行をスキップして、ユーザーIDをキーにした辞書を作成
            stats_dict = {}
            for row in existing_data[1:] if existing_data else []:
                if len(row) >= 5:
                    stats_dict[row[0]] = {
                        'user_name': row[1],
                        'last_login_date': row[2],
                        'consecutive_days': int(row[3]) if row[3] else 0,
                        'total_days': int(row[4]) if row[4] else 0,
                        'last_updated': row[5] if len(row) > 5 else ''
                    }

            # 統計情報を更新
            today_str = self.target_date.strftime('%Y/%m/%d')  # 今日
            previous_business_day = self.get_previous_business_day(self.target_date)  # 前営業日
            previous_business_day_str = previous_business_day.strftime('%Y/%m/%d')  # 前営業日文字列

            for user_id in user_data:
                if user_id in stats_dict:
                    # 既存ユーザーの更新
                    stats = stats_dict[user_id]

                    # 連続ログイン日数の計算（営業日ベース）
                    if stats['last_login_date'] == previous_business_day_str:
                        stats['consecutive_days'] += 1  # 前営業日もログインしていた
                    else:
                        stats['consecutive_days'] = 1  # 連続が途切れた

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
                        'total_days': 1,
                        'last_updated': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    }

            # シートに書き込むデータを準備
            rows = [['user_id', 'user_name', 'last_login_date', 'consecutive_days',
                    'total_days', 'last_updated']]  # ヘッダー

            for user_id, stats in sorted(stats_dict.items()):
                rows.append([
                    user_id,
                    stats['user_name'],
                    stats['last_login_date'],
                    stats['consecutive_days'],
                    stats['total_days'],
                    stats['last_updated']
                ])

            # シート全体を更新
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='statistics!A:F',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()  # 書き込み

            logger.info(f"✅ {len(stats_dict)}名のユーザー統計情報を更新しました")  # 更新成功ログ

            return stats_dict  # 統計情報を返却

        except Exception as e:
            logger.error(f"⚠️ ユーザー統計情報の更新に失敗しました: {e}")  # エラーログ
            return {}  # 空の辞書を返却

    def run(self) -> str:
        """集計処理のメイン実行"""
        try:
            logger.info(f"🚀 {self.target_date}のデータ集計を開始します")  # 開始ログ

            # 1. CSVファイル一覧を取得
            csv_files = self.get_csv_files_from_drive()
            if not csv_files:
                logger.warning("⚠️ CSVファイルが見つかりませんでした")  # CSVファイルなし警告
                return

            # 2. 各CSVファイルからデータを読み込み
            all_records = []
            for csv_file in csv_files:
                records = self.read_csv_content(csv_file['id'], csv_file['name'])
                all_records.extend(records)

            logger.info(f"📖 合計{len(all_records)}件のレコードを読み込みました")  # 総レコード数ログ

            # 3. ユーザーごとにデータを集約
            user_data = self.aggregate_user_data(all_records)

            if not user_data:
                logger.info("📈 集計するユーザーデータがありません")  # 集約データなしログ
                return "本日の参加者はいませんでした。"

            # 4. ユーザー統計情報を更新
            stats_dict = self.update_user_statistics(user_data)  # 統計更新

            # 5. Slackに投稿
            report = self.post_to_slack(user_data, stats_dict)  # Slack投稿

            logger.info("🎉 データ集計が正常に完了しました！")  # 完了ログ

            return report  # レポート文字列を返す

        except Exception as e:
            logger.error(f"⚠️ データ集計に失敗しました: {e}")  # エラーログ
            raise

    def load_user_mapping(self):
        """ユーザーマッピングシートを再読み込み（プライベートメソッドのエイリアス）"""
        self._load_user_mapping()  # プライベートメソッドを呼び出し

    def generate_attendance_report(self, user_data: Dict[str, Dict[str, Any]]) -> str:
        """
        出席レポートを文字列として生成（互換性のため残す）

        Args:
            user_data: ユーザーごとの集計データ

        Returns:
            レポート文字列（Slackなどで使用可能）
        """
        try:
            # レポート文字列を構築
            lines = []  # レポートの各行
            lines.append("="*60)  # 区切り線
            lines.append(f"📅 {self.target_date.strftime('%Y年%m月%d日')} の参加者レポート")  # タイトル
            lines.append("="*60)  # 区切り線
            lines.append("")  # 空行

            if not user_data:
                lines.append("本日の参加者はいませんでした。")  # 参加者なし
                return "\n".join(lines)  # 文字列として返す

            lines.append(f"本日参加した人（{len(user_data)}名）：")  # 参加者数
            lines.append("")  # 空行

            # ユーザー名でソート
            sorted_users = sorted(user_data.items(), key=lambda x: x[1]['user_name'])  # 名前順ソート

            # 連続ログイン日数を簡易計算（互換性のため残す）
            for user_id, data in sorted_users:
                user_name = data['user_name'] or 'Unknown'  # Discordユーザー名

                # ランダムな日数を生成（デモ用）
                import random  # ランダム
                random.seed(user_id)  # ユーザーIDでシード固定
                total_days = random.randint(1, 30)  # 総ログイン日数（デモ）
                streak_days = min(random.randint(1, 7), total_days)  # 連続日数（デモ）

                # 出力パターンに応じてメッセージを生成
                if self.output_pattern == 'discord':  # Discord名で出力（モック用）
                    message = f"{user_name} さん　{total_days}日目のログインになります。"  # Discord名使用
                else:  # Slackメンションで出力（本番用）
                    # Slackメンションを取得
                    slack_mention = self.get_slack_mention(user_id, user_name)  # Slackメンション取得
                    message = f"{slack_mention} さん　{total_days}日目のログインになります。"  # Slackメンション使用

                # 連続ログインメッセージを追加
                if streak_days > 1:  # 2日以上連続の場合
                    message += f"（{streak_days}日連続ログイン達成！）"  # 連続日数表示

                lines.append(f"  ✅ {message}")  # メッセージ追加

            lines.append("")  # 空行
            lines.append("="*60)  # 区切り線

            return "\n".join(lines)  # 改行で結合して返す

        except Exception as e:
            logger.error(f"⚠️ レポート生成でエラー: {e}")  # エラーログ
            return f"レポートの生成に失敗しました: {e}"  # エラーメッセージ

    def load_user_mapping(self):
        """
        ユーザー名対照表をGoogle Sheetsから読み込み
        """
        try:
            # 対照表シート名
            mapping_sheet_name = f"ユーザー名対照表_{self.env.name}"  # 環境別のシート名

            # シートを検索
            query = f"name='{mapping_sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='allDrives'
            ).execute()

            sheets = results.get('files', [])  # 結果取得
            if not sheets:
                logger.warning(f"⚠️ ユーザー名対照表が見つかりません: {mapping_sheet_name}")  # 対照表なし警告
                logger.info("👉 create_user_mapping_sheet.pyを実行して対照表を作成してください")  # 作成指示
                return

            sheet_id = sheets[0]['id']  # シートID取得
            logger.info(f"📝 ユーザー名対照表を読み込み中: {mapping_sheet_name}")  # 読み込みログ

            # データを読み込み
            range_name = 'A2:E100'  # ヘッダーを除く100行まで
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])  # データ取得
            if not values:
                logger.warning("⚠️ 対照表にデータがありません")  # データなし警告
                return

            # マッピングを作成
            for row in values:
                if len(row) >= 5:  # 必要な列数確認
                    discord_id = row[0]  # Discord ID
                    discord_name = row[1]  # Discord名
                    slack_id = row[2] if len(row) > 2 else ''  # Slack ID
                    slack_name = row[3] if len(row) > 3 else ''  # Slack名
                    slack_mention = row[4] if len(row) > 4 else ''  # Slackメンション

                    if discord_id and slack_mention:  # IDとメンションがある場合
                        self.user_mapping[discord_id] = {
                            'discord_name': discord_name,
                            'slack_id': slack_id,
                            'slack_name': slack_name,
                            'slack_mention': slack_mention
                        }

            logger.info(f"✅ {len(self.user_mapping)}件のユーザーマッピングを読み込みました")  # 読み込み完了

        except Exception as e:
            logger.warning(f"⚠️ ユーザーマッピングの読み込みでエラー: {e}")  # エラーログ
            # エラーがあっても処理を続行

    def get_slack_mention(self, discord_id: str, discord_name: str) -> str:
        """
        Discord IDまたは名前からSlackメンションを取得

        Args:
            discord_id: DiscordユーザーID
            discord_name: Discordユーザー名

        Returns:
            Slackメンション形式またはDiscord名
        """
        # IDでマッチングを検索
        if discord_id in self.user_mapping:
            return self.user_mapping[discord_id]['slack_mention']  # Slackメンション返す

        # Discord名でマッチングを検索（フォールバック）
        for user_id, mapping in self.user_mapping.items():
            if mapping['discord_name'] == discord_name:
                return mapping['slack_mention']  # Slackメンション返す

        # マッピングがない場合はDiscord名を返す
        return discord_name  # Discord名をそのまま返す


def main():
    """メイン関数"""
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='日次VCログイン集計プログラム')
    parser.add_argument('--date', type=str, help='集計対象日 (YYYY-MM-DD形式)')
    parser.add_argument('--debug', action='store_true', help='デバッグログを有効化')
    parser.add_argument('--env', type=int, default=2, choices=[0, 1, 2],
                       help='実行環境 (0=本番, 1=テスト, 2=開発, デフォルト=2)')  # 環境引数追加
    parser.add_argument('--output', type=str, default='slack', choices=['discord', 'slack'],
                       help='出力形式 (discord=Discord名, slack=Slackメンション, デフォルト=slack)')  # 出力形式引数追加

    args = parser.parse_args()

    # デバッグモードの設定
    if args.debug:
        logger.remove()  # 既存のハンドラーを削除
        logger.add(sys.stderr, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # DEBUGレベルでコンソール出力（ファイル名と関数名を先に表示）

        # デバッグ時も日付付きファイル名でログ出力
        from datetime import datetime
        debug_date = datetime.now().strftime("%Y%m%d")  # 日付取得

        # 全ての処理を含むデバッグログ
        logger.add(f"logs/debug_{debug_date}.log",
                  rotation="10 MB",
                  retention="7 days",
                  level="DEBUG",
                  encoding="utf-8",
                  format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # DEBUGレベルでファイル出力

    # 対象日付の設定
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"⚠️ 日付フォーマットが無効です: {args.date}。YYYY-MM-DD形式で指定してください")  # 日付フォーマットエラー
            sys.exit(1)

    # 環境の設定
    env = Environment(args.env)  # 環境を設定
    env_name = {Environment.PRD: "本番環境", Environment.TST: "テスト環境", Environment.DEV: "開発環境"}[env]  # 環境名取得
    logger.info(f"🌐 {env_name}で実行中です")  # 環境ログ出力

    # 集計処理を実行
    aggregator = DailyAggregator(target_date, env, args.output)  # 出力パターンを渡す
    report = aggregator.run()  # レポートを取得

    # レポートを文字列として返す（Slack連携などで使用可能）
    return report


if __name__ == '__main__':
    main()