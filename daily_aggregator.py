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
from typing import Dict, List, Optional, Any, Union
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

# 現在の日時を取得（YYYYMMDD_HHMMSS形式）
current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")  # 日時取得（時分秒まで）

# メイン処理のログ（すべてのログを1つのファイルに集約）
logger.add(f"logs/daily_aggregator_{current_datetime}.log",
          rotation="10 MB",
          retention="7 days",
          level="DEBUG",  # DEBUGレベルに変更してより詳細なログを出力
          encoding="utf-8",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # すべての処理を1つのログファイルに記録


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
        self.mapping_sheet_id = None  # マッピングシートのID（キャッシュ用）

        # config.pyから設定を取得
        self.config = get_config(env)  # すべての設定を取得

        # Google Drive関連の設定を取得（デフォルト値を設定）
        self.google_drive_folder_path = self.config.get('google_drive_base_folder', 'discord_mokumoku_tracker')  # Google Driveベースフォルダパス
        self.google_drive_csv_path = self.config.get('google_drive_csv_path')  # CSVファイルパステンプレート
        self.sheet_name = f"もくもくトラッカー_{self.config['suffix']}"  # Sheets名
        self.allowed_vc_ids = self.config.get('discord_channel_ids', self.config.get('channel_ids'))  # Discord対象VCチャンネルID
        self.suffix = self.config['suffix']  # 環境サフィックス (0_PRD/1_TST/2_DEV)
        self.google_drive_discord_slack_mapping_sheet_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # Discord-Slackユーザーマッピングシートパス
        self.google_drive_discord_slack_mapping_sheet_tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')  # マッピングシート内のタブ名（デフォルト: Sheet1）
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
            logger.info("Google Driveへの接続が完了しました")  # 初期化成功ログ

            # Sheets APIサービスの構築
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheetsへの接続が完了しました")  # 初期化成功ログ

            # Slackクライアントの初期化
            if self.slack_token:
                self.slack_client = WebClient(token=self.slack_token)
                logger.info("Slackクライアントを初期化しました")  # Slack初期化
            else:
                logger.warning("Slackトークンが設定されていません")  # Slack未設定

            # ユーザーマッピングを読み込み
            self._load_user_mapping()

        except Exception as e:
            logger.error(f"サービスの初期化に失敗しました: {e}")  # エラーログ
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
            logger.info("環境変数から認証情報を取得しました（Base64形式）")  # Base64認証使用ログ
        else:
            # ファイルパスから読み込み
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(f"Service account file not found: {service_account_file}")
            with open(service_account_file, 'r') as f:
                service_account_info = json.load(f)
            logger.info(f"認証ファイルを読み込みました: {service_account_file}")  # ファイル認証使用ログ

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
            # パスが設定されていない場合はスキップ
            if not self.google_drive_discord_slack_mapping_sheet_path:
                logger.info("Discord-Slackマッピングシートが設定されていません。Discord名を使用します")  # 設定なし
                return

            # パスからフォルダとファイル名を取得
            path_parts = self.google_drive_discord_slack_mapping_sheet_path.split('/')  # パスを分割
            file_name = path_parts[-1]  # ファイル名（最後の要素）

            logger.info(f"Discord-Slackマッピングシートを検索: {self.google_drive_discord_slack_mapping_sheet_path}")  # シート検索

            # Google Driveでスプレッドシートを検索
            query = f"name='{file_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"  # 検索クエリ
            results = self.drive_service.files().list(
                q=query,
                fields='files(id, name)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()  # 検索実行

            items = results.get('files', [])  # 検索結果
            if not items:
                logger.warning(f"Discord-Slackマッピングシートが見つかりません: {file_name}")  # シートなし
                logger.info("Discord名を使用します")  # フォールバック
                return

            sheet_id = items[0]['id']  # シートID取得
            self.mapping_sheet_id = sheet_id  # キャッシュに保存
            logger.info(f"マッピングシートを発見: {file_name} (ID: {sheet_id})")  # シート発見

            # configで指定されたタブ名を使用
            tab_name = self.google_drive_discord_slack_mapping_sheet_tab_name
            logger.info(f"config設定タブ名を使用: {tab_name}")  # タブ名表示

            # タブの存在確認（エラー防止のため）
            try:
                spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
                sheet_names = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]

                if tab_name not in sheet_names:
                    logger.error(f"指定されたタブ '{tab_name}' が見つかりません。利用可能なタブ: {sheet_names}")
                    logger.error(f"config.pyで正しいタブ名を設定してください: google_drive_discord_slack_mapping_sheet_tab_name")
                    raise ValueError(f"タブ '{tab_name}' がスプレッドシートに存在しません")
            except Exception as e:
                logger.warning(f"タブ一覧の取得に失敗しました: {e}")
                # タブ確認に失敗してもconfigの設定を信じて続行

            range_name = f'{tab_name}!A2:C1000'  # config設定または代替タブを使用

            # シートからデータを読み込み
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name  # 動的に決定した範囲
            ).execute()  # データ取得

            rows = result.get('values', [])  # データ行
            for row in rows:
                if len(row) >= 3:
                    discord_user_id = row[0]  # DiscordユーザーID
                    slack_mention_id = row[2]  # SlackメンションID
                    if discord_user_id and slack_mention_id:
                        self.user_mapping[discord_user_id] = slack_mention_id  # マッピング登録

            logger.info(f"{len(self.user_mapping)}件のユーザーマッピングを読み込みました")  # 読み込み完了

        except Exception as e:
            logger.warning(f"ユーザーマッピングの読み込みに失敗: {e}")  # エラー
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
        configのgoogle_drive_csv_pathテンプレートに基づいてファイルを探す

        Returns:
            CSVファイル情報のリスト [{id, name, vc_name}, ...]
        """
        try:
            logger.info(f"CSVファイルの検索を開始します")  # 検索開始ログ

            # configから設定されたCSVパステンプレートを使用
            if self.google_drive_csv_path:
                logger.info(f"CSVパステンプレート: {self.google_drive_csv_path}")  # テンプレート表示

                # パステンプレートを解析 (例: discord_mokumoku_tracker/csv/{vc_name}_0_PRD.csv)
                # {vc_name}より前の部分を抽出してフォルダパスとする
                path_parts = self.google_drive_csv_path.split('{vc_name}')
                if len(path_parts) >= 2:
                    # フォルダパスとファイルパターンを取得
                    folder_path = path_parts[0].rstrip('/')  # 末尾の/を削除
                    file_pattern = path_parts[1].lstrip('_')  # 先頭の_を削除（例: 0_PRD.csv）

                    logger.info(f"フォルダパス: {folder_path}")  # フォルダパス表示
                    logger.info(f"ファイルパターン: *_{file_pattern}")  # パターン表示
                else:
                    logger.error(f"CSVパステンプレートの形式が不正です: {self.google_drive_csv_path}")
                    return []
            else:
                logger.error("CSVパステンプレートが設定されていません")
                return []

            # フォルダ階層を探索
            folder_parts = folder_path.split('/')  # パスを分割
            if not folder_parts:
                logger.warning("フォルダパスが無効です")  # 無効なパス警告
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
                logger.warning(f"Google Drive上に '{root_folder_name}' フォルダが見つかりません")  # フォルダ未発見警告
                return []

            current_folder_id = folders[0]['id']  # フォルダID取得
            logger.info(f"ルートフォルダを発見: {folders[0]['name']} (ID: {current_folder_id})")  # フォルダ発見ログ

            # 残りのフォルダ階層を順に探索
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
                    logger.warning(f"サブフォルダ '{folder_name}' が見つかりません")  # サブフォルダ未発見警告
                    return []

                current_folder_id = subfolders[0]['id']  # 次のフォルダID
                logger.info(f"サブフォルダを発見: {folder_name} (ID: {current_folder_id})")  # フォルダ発見ログ

            # 最終フォルダ（csvフォルダ）内のCSVファイルを検索
            target_folder_id = current_folder_id
            logger.info(f"CSVファイルを検索中...")  # 検索ログ

            # ファイルパターンに基づいて検索（例: *_0_PRD.csv）
            csv_query = f"'{target_folder_id}' in parents and name contains '_{file_pattern}'"
            csv_results = self.drive_service.files().list(
                q=csv_query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            csv_files = csv_results.get('files', [])

            # vc_nameを抽出してファイル情報に追加
            result_files = []
            for csv_file in csv_files:
                file_name = csv_file['name']
                # ファイル名からVCチャンネル名を抽出（例: ☁もくもく広場_0_PRD.csv → ☁もくもく広場）
                if file_name.endswith(f'_{file_pattern}'):
                    vc_name = file_name.replace(f'_{file_pattern}', '')
                    result_files.append({
                        'id': csv_file['id'],
                        'name': file_name,
                        'vc_name': vc_name
                    })
                    logger.info(f"  CSVファイルを発見: {file_name} (VCチャンネル: {vc_name})")  # ファイル発見ログ

            logger.info(f"合計{len(result_files)}個のCSVファイルを発見しました")  # CSVファイル数ログ
            return result_files

        except Exception as e:
            logger.error(f"CSVファイルの取得に失敗しました: {e}")  # エラーログ
            import traceback
            logger.error(traceback.format_exc())  # スタックトレース
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
                logger.warning(f"CSVファイルが空です: {file_name}")  # 空ファイル警告
                return []

            lines = csv_text.strip().split('\n')
            if len(lines) < 2:  # ヘッダーのみの場合
                return []

            # ヘッダー行を取得（改行コードも除去）
            headers = [h.strip() for h in lines[0].split(',')]
            logger.debug(f"CSVヘッダー: {headers}")  # ヘッダー情報ログ

            # 日付列の確認
            if 'datetime_jst' in headers:
                logger.info(f"datetime_jst列を発見（インデックス: {headers.index('datetime_jst')}）")  # 日付列確認
            else:
                logger.warning(f"datetime_jst列が見つかりません。利用可能な列: {headers}")  # 日付列なし警告

            # データ行をパース
            records = []
            # 両方の日付形式をサポート（ゼロパディングあり/なし）
            target_date_str = self.target_date.strftime('%Y/%m/%d')  # 対象日付文字列（ゼロパディングあり）
            target_date_str_no_pad = self.target_date.strftime('%Y/%-m/%-d') if os.name != 'nt' else self.target_date.strftime('%Y/%#m/%#d')  # ゼロパディングなし
            logger.info(f"検索対象日付: {target_date_str} または {target_date_str_no_pad}")  # 検索日付ログ

            # サンプル表示は削除（不要なログ）  # サンプルデータヘッダー

            for idx, line in enumerate(lines[1:]):
                values = line.split(',')
                if len(values) != len(headers):
                    continue

                record = dict(zip(headers, values))

                # サンプル表示は削除（不要なログ）

                # 対象日のレコードのみ抽出
                if 'datetime_jst' in record:
                    datetime_value = record['datetime_jst'].strip()  # 改行コード等を除去
                    # 両方の日付形式でチェック
                    if datetime_value.startswith(target_date_str) or datetime_value.startswith(target_date_str_no_pad):
                        # VCチャンネル名を追加（ファイル名から拡張子を除いたもの）
                        record['vc_name'] = file_name.replace('.csv', '')
                        records.append(record)
                        # マッチログは削除（不要）  # マッチしたレコード

            logger.info(f"{file_name}から{target_date_str}の{len(records)}件のデータを読み込みました")  # 読み込み結果ログ
            return records

        except Exception as e:
            logger.error(f"CSVファイル {file_name} の読み込みに失敗しました: {e}")  # エラーログ
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
            'login_count': 0,
            'records': []  # デバッグ用：該当レコードを保存
        })

        logger.debug(f"集計対象レコード数: {len(all_records)}")  # 全レコード数

        for idx, record in enumerate(all_records):
            # present列が削除されたため、全レコードを集計対象とする
            user_id = record.get('user_id', '')
            if user_id:
                user_data[user_id]['user_name'] = record.get('user_name', '')  # ユーザー名
                # vc_name列がない場合はファイルパスから取得（互換性のため）
                vc_name = record.get('vc_name', 'unknown')  # VCチャンネル名
                user_data[user_id]['vc_channels'].add(vc_name)  # VCチャンネル追加
                user_data[user_id]['login_count'] += 1  # ログイン回数カウント

                # デバッグ用：レコードの詳細を保存
                user_data[user_id]['records'].append({
                    'index': idx,
                    'datetime': record.get('datetime_jst', ''),
                    'vc_name': vc_name,
                    'user_name': record.get('user_name', '')
                })

        # セットを文字列に変換＋デバッグ出力
        for user_id, data in user_data.items():
            data['vc_channels'] = ', '.join(sorted(data['vc_channels']))

            # デバッグ：特定ユーザーの詳細を出力
            if 'blue' in data['user_name'].lower():
                logger.debug(f"=== {data['user_name']} (ID: {user_id}) のレコード一覧 ===")
                logger.debug(f"  総レコード数: {len(data['records'])}")
                for rec in data['records']:
                    logger.debug(f"  - 行{rec['index']+1}: {rec['datetime']} @ {rec['vc_name']}")

        logger.info(f"{len(user_data)}名のユーザーデータを集計しました")  # 集計結果ログ
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
                logger.error(f"スプレッドシートが見つかりません: {self.sheet_name}")  # シート未発見エラー
                return None

            sheet_id = sheets[0]['id']
            logger.info(f"スプレッドシートを発見: {self.sheet_name}")  # シート発見ログ
            return sheet_id

        except Exception as e:
            logger.error(f"シートIDの取得に失敗しました: {e}")  # エラーログ
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
                    logger.info(f"新しいシートを作成中: {sheet_name}")  # シート作成ログ

            if requests:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': requests}
                ).execute()

                # ヘッダーを設定
                self._set_sheet_headers(sheet_id)

        except Exception as e:
            logger.error(f"シートの確認・作成に失敗しました: {e}")  # エラーログ
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

            logger.info("シートのヘッダーを設定しました")  # ヘッダー設定成功ログ

        except Exception as e:
            logger.error(f"ヘッダーの設定に失敗しました: {e}")  # エラーログ

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
                    logger.info(f"Slackにレポートを投稿しました")  # 投稿成功
                except SlackApiError as e:
                    logger.warning(f"Slack投稿エラー: {e.response['error']}")  # Slackエラー
                    logger.info("Slackに投稿できなかったため、ログに出力します")  # ログ出力
                    # レポート全体を1つのログメッセージとして出力
                    logger.info(f"\n{'='*60}\n[レポート]\n{message}\n{'='*60}")
            else:
                # Discord出力モードまたはSlackが設定されていない場合はログ出力
                logger.info("レポートをログに出力します")  # ログ出力
                # レポート全体を1つのログメッセージとして出力
                logger.info(f"\n{'='*60}\n[レポート]\n{message}\n{'='*60}")

            return message

        except SlackApiError as e:
            logger.error(f"Slack投稿エラー: {e.response['error']}")  # Slackエラー
            raise
        except Exception as e:
            logger.error(f"レポート作成エラー: {e}")  # エラー
            raise

    def get_user_statistics_sheet_id(self) -> Optional[str]:
        """Discord-Slackマッピングシートのスプレッドシート IDを取得"""
        try:
            # すでにIDを取得済みの場合はそれを使用
            if self.mapping_sheet_id:
                logger.info(f"config設定パス({self.google_drive_discord_slack_mapping_sheet_path})のシートIDを使用: {self.mapping_sheet_id}")  # ID再利用
                sheet_id = self.mapping_sheet_id
            else:
                # マッピングシートが設定されていない場合
                if not self.google_drive_discord_slack_mapping_sheet_path:
                    logger.warning("マッピングシートが設定されていません")  # 設定なし
                    logger.info("統計情報の保存をスキップします")  # スキップ
                    return None

                # パスからファイル名を取得
                file_name = self.google_drive_discord_slack_mapping_sheet_path.split('/')[-1]  # パスから名前を取得

                # Google Driveでシートを検索
                query = f"name='{file_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
                results = self.drive_service.files().list(
                    q=query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()  # 検索実行

                files = results.get('files', [])  # ファイルリスト
                if not files:
                    logger.warning(f"マッピングシートが見つかりません: {file_name}")  # シートなし
                    logger.info("統計情報の保存をスキップします")  # スキップ
                    return None

                sheet_id = files[0]['id']  # シートID
                self.mapping_sheet_id = sheet_id  # キャッシュに保存
                logger.info(f"マッピングシートを発見: {file_name} (ID: {sheet_id})")  # 発見

                # statisticsタブが存在するか確認、なければ作成
                spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()  # シート情報取得
                sheet_titles = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]  # タブ名リスト

                if 'statistics' not in sheet_titles:
                    # statisticsタブを追加
                    request = {
                        'addSheet': {
                            'properties': {
                                'title': 'statistics',
                                'gridProperties': {'frozenRowCount': 1}
                            }
                        }
                    }
                    self.sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=sheet_id,
                        body={'requests': [request]}
                    ).execute()  # タブ追加

                    # ヘッダーを設定
                    headers = [['user_id', 'user_name', 'last_login_date', 'consecutive_days', 'total_days', 'last_updated']]  # ヘッダー
                    self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=sheet_id,
                        range='statistics!A1:F1',
                        valueInputOption='RAW',
                        body={'values': headers}
                    ).execute()  # ヘッダー書き込み

                    logger.info("statisticsタブを作成しました")  # タブ作成ログ

            return sheet_id  # ID返却

        except Exception as e:
            logger.error(f"マッピングシートの取得エラー: {e}")  # エラー
            return None

    def update_user_statistics(self, user_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """ユーザー統計情報を更新して返却"""
        try:
            # 統計シートのIDを取得
            sheet_id = self.get_user_statistics_sheet_id()  # シートID

            if not sheet_id:
                logger.warning("統計シートが見つからないため、統計情報の更新をスキップします")  # スキップログ
                # 統計情報なしで返却（連続日数は1日として返す）
                for user_id in user_data:
                    user_data[user_id]['consecutive_days'] = 1
                    user_data[user_id]['total_days'] = 1
                return user_data

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
                user_name = user_data[user_id]['user_name']

                if user_id in stats_dict:
                    # 既存ユーザーの更新
                    stats = stats_dict[user_id]
                    old_consecutive = stats['consecutive_days']
                    old_total = stats['total_days']
                    old_last_login = stats['last_login_date']

                    # デバッグ：更新前の状態を出力（blueさんの場合）
                    if 'blue' in user_name.lower():
                        logger.debug(f"=== {user_name} の統計更新 ===")
                        logger.debug(f"  ユーザーID: {user_id}")
                        logger.debug(f"  【統計シート既存値】")
                        logger.debug(f"    最終ログイン日: {old_last_login}")
                        logger.debug(f"    連続日数: {old_consecutive}日")
                        logger.debug(f"    累計日数: {old_total}日")
                        logger.debug(f"  【処理日情報】")
                        logger.debug(f"    今日: {today_str}")
                        logger.debug(f"    前営業日: {previous_business_day_str}")

                    # 最終ログイン日が今日でない場合のみ更新（同じ日の重複カウントを防ぐ）
                    if stats['last_login_date'] != today_str:
                        # 連続ログイン日数の計算（営業日ベース）
                        if stats['last_login_date'] == previous_business_day_str:
                            stats['consecutive_days'] += 1  # 前営業日もログインしていた
                            if 'blue' in user_name.lower():
                                logger.debug(f"  【連続ログイン判定】")
                                logger.debug(f"    判定: 継続（最終ログイン日 {old_last_login} = 前営業日 {previous_business_day_str}）")
                                logger.debug(f"    更新: {old_consecutive}日 → {stats['consecutive_days']}日")
                        else:
                            stats['consecutive_days'] = 1  # 連続が途切れた
                            if 'blue' in user_name.lower():
                                logger.debug(f"  【連続ログイン判定】")
                                logger.debug(f"    判定: リセット（最終ログイン日 {old_last_login} ≠ 前営業日 {previous_business_day_str}）")
                                logger.debug(f"    更新: {old_consecutive}日 → 1日")

                        # 累計ログイン日数（今日が新しい日の場合のみインクリメント）
                        stats['total_days'] += 1
                        if 'blue' in user_name.lower():
                            logger.debug(f"  【累計ログイン更新】")
                            logger.debug(f"    既存累計: {old_total}日")
                            logger.debug(f"    +1（今日の分）")
                            logger.debug(f"    新累計: {stats['total_days']}日")

                        # 最終ログイン日と更新日時を更新
                        stats['last_login_date'] = today_str
                        stats['last_updated'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    else:
                        if 'blue' in user_name.lower():
                            logger.debug(f"  【処理スキップ】")
                            logger.debug(f"    理由: 既に今日（{today_str}）のデータ処理済み")
                            logger.debug(f"    現在の連続日数: {stats['consecutive_days']}日（変更なし）")
                            logger.debug(f"    現在の累計日数: {stats['total_days']}日（変更なし）")

                    # ユーザー名は常に最新のものに更新
                    stats['user_name'] = user_data[user_id]['user_name']

                else:
                    # 新規ユーザー
                    stats_dict[user_id] = {
                        'user_name': user_data[user_id]['user_name'],
                        'last_login_date': today_str,
                        'consecutive_days': 1,
                        'total_days': 1,
                        'last_updated': datetime.now().strftime('%Y/%m/%d %H:%M:%S')
                    }
                    if 'blue' in user_name.lower():
                        logger.debug(f"=== {user_name} 新規登録 ===")
                        logger.debug(f"  初回ログイン: {today_str}, 連続=1日, 累計=1日")

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

            logger.info(f"{len(stats_dict)}名のユーザー統計情報を更新しました")  # 更新成功ログ

            return stats_dict  # 統計情報を返却

        except Exception as e:
            logger.error(f"ユーザー統計情報の更新に失敗しました: {e}")  # エラーログ
            return {}  # 空の辞書を返却

    def run(self) -> str:
        """集計処理のメイン実行"""
        try:
            logger.info(f"{self.target_date}のデータ集計を開始します")  # 開始ログ

            # 1. CSVファイル一覧を取得
            csv_files = self.get_csv_files_from_drive()
            if not csv_files:
                logger.warning("CSVファイルが見つかりませんでした")  # CSVファイルなし警告
                return

            # 2. 各CSVファイルからデータを読み込み
            all_records = []
            for csv_file in csv_files:
                # vc_nameを含む新しい形式に対応
                records = self.read_csv_content(csv_file['id'], csv_file.get('name', ''))
                # vc_nameが既に設定されている場合はそれを使用
                if 'vc_name' in csv_file:
                    for record in records:
                        if 'vc_name' not in record:
                            record['vc_name'] = csv_file['vc_name']
                all_records.extend(records)

            logger.info(f"合計{len(all_records)}件のレコードを読み込みました")  # 総レコード数ログ

            # 3. ユーザーごとにデータを集約
            user_data = self.aggregate_user_data(all_records)

            if not user_data:
                logger.info("集計するユーザーデータがありません")  # 集約データなしログ
                return "本日の参加者はいませんでした。"

            # 4. ユーザー統計情報を更新
            stats_dict = self.update_user_statistics(user_data)  # 統計更新

            # 5. Slackに投稿
            report = self.post_to_slack(user_data, stats_dict)  # Slack投稿

            logger.info("データ集計が正常に完了しました！")  # 完了ログ

            return report  # レポート文字列を返す

        except Exception as e:
            logger.error(f"データ集計に失敗しました: {e}")  # エラーログ
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

                lines.append(f"  {message}")  # メッセージ追加

            lines.append("")  # 空行
            lines.append("="*60)  # 区切り線

            return "\n".join(lines)  # 改行で結合して返す

        except Exception as e:
            logger.error(f"レポート生成でエラー: {e}")  # エラーログ
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
                logger.warning(f"ユーザー名対照表が見つかりません: {mapping_sheet_name}")  # 対照表なし警告
                logger.info("Google Drive上に対照表スプレッドシートを作成してください")  # 作成指示
                return

            sheet_id = sheets[0]['id']  # シートID取得
            logger.info(f"ユーザー名対照表を読み込み中: {mapping_sheet_name}")  # 読み込みログ

            # データを読み込み
            range_name = 'A2:E100'  # ヘッダーを除く100行まで
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])  # データ取得
            if not values:
                logger.warning("対照表にデータがありません")  # データなし警告
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

            logger.info(f"{len(self.user_mapping)}件のユーザーマッピングを読み込みました")  # 読み込み完了

        except Exception as e:
            logger.warning(f"ユーザーマッピングの読み込みでエラー: {e}")  # エラーログ
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
            logger.error(f"日付フォーマットが無効です: {args.date}。YYYY-MM-DD形式で指定してください")  # 日付フォーマットエラー
            sys.exit(1)

    # 環境の設定
    env = Environment(args.env)  # 環境を設定
    env_name = {Environment.PRD: "本番環境", Environment.TST: "テスト環境", Environment.DEV: "開発環境"}[env]  # 環境名取得
    logger.info(f"{env_name}で実行中です")  # 環境ログ出力

    # 集計処理を実行
    aggregator = DailyAggregator(target_date, env, args.output)  # 出力パターンを渡す
    report = aggregator.run()  # レポートを取得

    # レポートを文字列として返す（Slack連携などで使用可能）
    return report


if __name__ == '__main__':
    main()