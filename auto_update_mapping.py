#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord-Slackマッピング自動更新スクリプト
CSVファイルから新しいユーザーを検出して、マッピングシートに自動追加
"""

import os
import sys
import csv
import io
import argparse
from datetime import datetime
from typing import List, Dict, Set, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from config import get_config, Environment
from loguru import logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import discord  # Discord API用（Python 3.12環境で使用）
import asyncio

# loguruの設定
logger.remove()  # デフォルトハンドラーを削除

# ログレベルを環境変数から取得（デフォルトはINFO）
log_level = os.getenv("LOGLEVEL", "INFO")  # 環境変数LOGLEVELから取得

logger.add(sys.stderr, level=log_level, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # コンソール出力
# logsフォルダが存在しない場合は作成
os.makedirs("logs", exist_ok=True)  # logsフォルダを作成
# タイムスタンプベースのログファイル名を生成
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 現在時刻をフォーマット
log_filename = f"logs/auto_update_mapping_{timestamp}.log"  # タイムスタンプ付きファイル名
logger.add(log_filename, level=log_level, encoding="utf-8", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # ファイル出力


class MappingUpdater:
    """Discord-Slackマッピング更新クラス"""

    def __init__(self, env: Environment, enable_slack_notify: bool = True):
        """初期化"""
        self.env = env  # 環境
        self.enable_slack_notify = enable_slack_notify  # Slack通知の有効/無効
        self.config = get_config(env)  # 設定取得
        self.drive_service = None  # Drive APIサービス
        self.sheets_service = None  # Sheets APIサービス
        self.slack_client = None  # Slack APIクライアント
        self.discord_members = {}  # Discordメンバー情報キャッシュ {user_id: display_name}
        self.excluded_users = self.config.get('discord_excluded_users', [])  # 除外ユーザーリスト
        self.initialize_services()  # サービス初期化

    def initialize_services(self):
        """Google APIとSlack APIサービスを初期化"""
        service_account_json = self.config['google_drive_service_account_json']  # 認証ファイルパス
        credentials = service_account.Credentials.from_service_account_file(
            service_account_json,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
        )  # 認証情報作成

        self.drive_service = build('drive', 'v3', credentials=credentials)  # Drive API初期化
        self.sheets_service = build('sheets', 'v4', credentials=credentials)  # Sheets API初期化

        # Slack APIクライアントの初期化
        slack_token = self.config.get('slack_token')  # Slackトークン取得
        if slack_token:  # トークンがある場合
            self.slack_client = WebClient(token=slack_token)  # Slackクライアント作成

    def get_users_from_csv(self) -> Dict[str, Tuple[str, str, str]]:
        """CSVファイルからユーザー情報を取得

        Returns:
            Dict[discord_id, (discord_name, display_name, vc_name)]
        """
        users = {}  # ユーザー辞書

        # CSVパステンプレートからフォルダパスを取得
        csv_path_template = self.config.get('google_drive_csv_path')  # CSVパステンプレート取得
        if not csv_path_template:  # テンプレートがない場合
            logger.error("CSVパステンプレートが設定されていません")  # エラー出力
            return users  # 空の辞書を返す

        # 環境サフィックスを取得
        target_suffix = self.config.get('suffix')  # 環境サフィックス（0_PRD, 1_TST, 2_DEV）
        logger.info(f"処理対象: *_{target_suffix}.csv ファイルのみを処理します")  # 対象ファイルログ

        # フォルダパスを抽出（{vc_name}より前の部分）
        folder_path = csv_path_template.split('{vc_name}')[0].rstrip('/')  # フォルダパス取得

        # 共有ドライブIDを取得
        shared_drive_id = self.config.get('google_drive_shared_drive_id')  # 共有ドライブID

        # フォルダIDを検索
        folder_id = self._find_folder_id(folder_path, shared_drive_id)  # フォルダID検索
        if not folder_id:  # フォルダが見つからない場合
            logger.error(f"フォルダが見つかりません: {folder_path}")  # エラー出力
            return users  # 空の辞書を返す

        # CSVファイルを検索
        query = f"'{folder_id}' in parents and mimeType='text/csv'"  # 検索クエリ
        if shared_drive_id:  # 共有ドライブの場合
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='drive',
                driveId=shared_drive_id
            ).execute()  # ファイル検索（共有ドライブ）
        else:  # マイドライブの場合
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()  # ファイル検索（マイドライブ）

        files = results.get('files', [])  # ファイルリスト取得
        logger.info(f"CSVファイル {len(files)}個を発見")  # ファイル数ログ

        # 対象環境のCSVファイルのみをフィルタリング
        target_files = []  # 処理対象ファイルリスト
        for file in files:  # 各ファイルをチェック
            if file['name'].endswith(f"_{target_suffix}.csv"):  # 対象環境のファイルか確認
                target_files.append(file)  # 対象リストに追加
            else:  # 対象外のファイル
                logger.debug(f"スキップ: {file['name']} (対象外の環境)")  # デバッグログ

        logger.info(f"処理対象CSVファイル: {len(target_files)}個 (環境: {target_suffix})")  # 対象ファイル数ログ

        # 各CSVファイルからユーザー情報を収集
        for file in target_files:  # 各対象ファイルに対して
            file_id = file['id']  # ファイルID
            file_name = file['name']  # ファイル名

            # VC名を抽出（ファイル名から環境サフィックスを除去）
            vc_name = file_name.replace(f"_{self.config['suffix']}.csv", "")  # VC名取得

            logger.info(f"処理中: {file_name} (VC: {vc_name})")  # 処理開始ログ

            # CSVファイルをダウンロード
            request = self.drive_service.files().get_media(fileId=file_id)  # ダウンロードリクエスト
            file_content = io.BytesIO()  # ファイル内容格納用
            downloader = MediaIoBaseDownload(file_content, request)  # ダウンローダー作成
            done = False  # 完了フラグ
            while not done:  # ダウンロード完了まで
                status, done = downloader.next_chunk()  # チャンクダウンロード

            # CSVを解析
            file_content.seek(0)  # ファイルポインタを先頭に
            csv_text = file_content.read().decode('utf-8')  # UTF-8デコード
            csv_reader = csv.DictReader(io.StringIO(csv_text))  # CSVリーダー作成

            for row in csv_reader:  # 各行に対して
                discord_id = row.get('user_id', '').strip()  # Discord ID取得
                discord_name = row.get('user_name', '').strip()  # Discord名取得

                # 除外ユーザーをスキップ
                if discord_name in self.excluded_users:  # 除外リストに含まれている場合
                    logger.info(f"  除外ユーザーをスキップ: {discord_name}")  # ログ出力
                    continue  # 次の行へ

                # display_name列があれば使用、なければuser_nameから#以降を除去
                display_name = row.get('display_name', '')  # 表示名取得
                if not display_name and discord_name:  # display_nameがない場合
                    display_name = discord_name.split('#')[0]  # #以降を除去して表示名とする

                if discord_id and discord_name:  # IDと名前がある場合
                    users[discord_id] = (discord_name, display_name, vc_name)  # ユーザー情報保存

        logger.info(f"CSVから {len(users)}人のユニークユーザーを取得")  # 取得数ログ
        return users  # ユーザー辞書を返す

    def get_existing_mapping(self) -> Set[str]:
        """マッピングシートから既存のDiscord IDを取得

        Returns:
            Set[discord_id]
        """
        existing_ids = set()  # 既存IDセット

        # マッピングシートのパスを取得
        mapping_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # パス取得
        if not mapping_path:  # パスがない場合
            logger.error("マッピングシートパスが設定されていません")  # エラー出力
            return existing_ids  # 空のセットを返す

        # ファイル名を抽出
        sheet_name = mapping_path.split('/')[-1]  # ファイル名取得

        # シートを検索
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()  # ファイル検索

        sheets = results.get('files', [])  # シートリスト取得
        if not sheets:  # シートが見つからない場合
            logger.warning(f"マッピングシートが見つかりません: {sheet_name}")  # 警告出力
            return existing_ids  # 空のセットを返す

        sheet_id = sheets[0]['id']  # シートID取得
        logger.info(f"マッピングシート発見: {sheet_name}")  # 発見ログ

        # 既存データを読み込み
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')  # タブ名
        range_name = f'{tab_name}!A:D'  # 範囲指定（D列まで）

        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()  # データ取得

            values = result.get('values', [])  # 値リスト取得

            # ヘッダー行をスキップして、Discord IDを収集
            for row in values[1:]:  # ヘッダー以外の行
                if row and len(row) > 0:  # 行が存在する場合
                    discord_id = row[0].strip()  # Discord ID取得
                    if discord_id:  # IDがある場合
                        existing_ids.add(discord_id)  # セットに追加

        except Exception as e:  # エラー時
            logger.warning(f"既存データ読み込みエラー: {e}")  # 警告出力

        logger.info(f"マッピングシートに {len(existing_ids)}人の既存ユーザー")  # 既存数ログ
        return existing_ids  # 既存IDセットを返す

    def update_existing_users(self, csv_users: Dict[str, Tuple[str, str, str]], discord_display_names: Dict[str, str]):
        """既存ユーザーの名前と表示名を更新

        Args:
            csv_users: {discord_id: (discord_name, display_name, vc_name)}
            discord_display_names: {discord_id: display_name} from Discord API
        """
        # マッピングシートを取得
        mapping_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # パス取得
        sheet_name = mapping_path.split('/')[-1]  # ファイル名取得

        # シートを検索
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()  # ファイル検索

        sheets = results.get('files', [])  # シートリスト取得
        if not sheets:  # シートが見つからない場合
            logger.error(f"マッピングシートが見つかりません: {sheet_name}")  # エラー出力
            return  # 処理終了

        sheet_id = sheets[0]['id']  # シートID取得
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')  # タブ名

        # 既存データを読み込み
        range_name = f'{tab_name}!A:D'  # 範囲指定
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()  # データ取得

        existing_rows = result.get('values', [])  # 既存データ

        if len(existing_rows) <= 1:  # ヘッダーのみまたはデータなし
            return  # 処理終了

        # 更新データを準備
        updates = []  # 更新リスト
        for i, row in enumerate(existing_rows):
            if i == 0:  # ヘッダー行をスキップ
                continue

            if len(row) > 0:  # 行にデータがある場合
                discord_id = row[0]  # Discord ID

                # CSVのユーザー情報がある場合
                if discord_id in csv_users:
                    discord_name, _, _ = csv_users[discord_id]  # CSV情報
                    display_name = discord_display_names.get(discord_id, discord_name.split('#')[0])  # Discord API表示名

                    # 既存の値と比較
                    old_name = row[1] if len(row) > 1 else ""  # 既存の名前
                    old_display = row[2] if len(row) > 2 else ""  # 既存の表示名

                    # 更新が必要な場合
                    if discord_name != old_name or display_name != old_display:
                        # B列とC列を更新
                        updates.append({
                            'range': f'{tab_name}!B{i+1}:C{i+1}',
                            'values': [[discord_name, display_name]]
                        })
                        logger.debug(f"更新: 行{i+1} {old_name}/{old_display} → {discord_name}/{display_name}")  # デバッグログ

        # バッチ更新を実行
        if updates:  # 更新がある場合
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }  # リクエストボディ

            self.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body=body
            ).execute()  # バッチ更新

            logger.info(f"✅ {len(updates)}件の既存ユーザー情報を更新")  # 成功ログ
        else:
            logger.info("既存ユーザーの更新は不要です")  # ログ出力

    def append_new_users(self, new_users: List[Tuple[str, str, str, str]]):
        """新規ユーザーをマッピングシートに追加

        Args:
            new_users: [(discord_id, discord_name, display_name, vc_name), ...]
        """
        if not new_users:  # 新規ユーザーがない場合
            logger.info("追加する新規ユーザーはありません")  # ログ出力
            return  # 処理終了

        # マッピングシートを取得
        mapping_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # パス取得
        sheet_name = mapping_path.split('/')[-1]  # ファイル名取得

        # シートを検索
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()  # ファイル検索

        sheets = results.get('files', [])  # シートリスト取得
        if not sheets:  # シートが見つからない場合
            logger.error(f"マッピングシートが見つかりません: {sheet_name}")  # エラー出力
            return  # 処理終了

        sheet_id = sheets[0]['id']  # シートID取得
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')  # タブ名

        # 追加するデータを準備（Slack IDは空欄）
        new_rows = []  # 新規行リスト
        for discord_id, discord_name, display_name, vc_name in new_users:  # 各新規ユーザー
            new_rows.append([discord_id, discord_name, display_name, ''])  # Discord ID、名前、表示名、Slack ID（空）

        # データを追加
        body = {'values': new_rows}  # リクエストボディ

        try:
            # 既存データの行数を取得
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f'{tab_name}!A:A'
            ).execute()  # A列データ取得

            existing_rows = len(result.get('values', []))  # 既存行数
            if existing_rows == 0:  # データがない場合
                # ヘッダーを追加してからデータを追加
                header = [['Discord User ID', 'Discord User Name', 'Discord Display Name', 'Slack Mention ID']]  # ヘッダー（Display Name追加）
                header_body = {'values': header}  # ヘッダーボディ
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f'{tab_name}!A1:D1',
                    valueInputOption='USER_ENTERED',
                    body=header_body
                ).execute()  # ヘッダー追加
                start_row = 2  # データ開始行
            else:  # データがある場合
                start_row = existing_rows + 1  # 次の行から

            # 新規データを追加
            append_range = f'{tab_name}!A{start_row}:D{start_row + len(new_rows) - 1}'  # 追加範囲（D列まで）
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=append_range,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()  # データ追加

            logger.info(f"✅ {len(new_users)}人の新規ユーザーをマッピングシートに追加")  # 成功ログ
            for discord_id, discord_name, display_name, vc_name in new_users:  # 各追加ユーザー
                logger.info(f"  - {discord_name} / {display_name} (ID: {discord_id}, VC: {vc_name})")  # 詳細ログ

        except Exception as e:  # エラー時
            logger.error(f"データ追加エラー: {e}")  # エラー出力

    def _find_folder_id(self, folder_path: str, shared_drive_id: str = None) -> str:
        """フォルダパスからフォルダIDを検索

        Args:
            folder_path: フォルダパス（例: discord_mokumoku_tracker/csv）
            shared_drive_id: 共有ドライブID

        Returns:
            フォルダID
        """
        path_parts = folder_path.split('/')  # パスを分割
        parent_id = shared_drive_id if shared_drive_id else 'root'  # 親ID設定

        for part in path_parts:  # 各パーツに対して
            if not part:  # 空の場合
                continue  # スキップ

            query = f"name='{part}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'"  # 検索クエリ

            if shared_drive_id:  # 共有ドライブの場合
                results = self.drive_service.files().list(
                    q=query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    corpora='drive',
                    driveId=shared_drive_id
                ).execute()  # フォルダ検索（共有ドライブ）
            else:  # マイドライブの場合
                results = self.drive_service.files().list(
                    q=query,
                    fields="files(id, name)"
                ).execute()  # フォルダ検索（マイドライブ）

            folders = results.get('files', [])  # フォルダリスト取得
            if not folders:  # フォルダが見つからない場合
                return None  # Noneを返す

            parent_id = folders[0]['id']  # 次の親IDに設定

        return parent_id  # 最終フォルダIDを返す

    def get_slack_users(self) -> List[Dict[str, str]]:
        """Slackワークスペースのユーザー一覧を取得

        Returns:
            List[Dict]: ユーザー情報のリスト [{id, name, display_name, real_name}, ...]
        """
        if not self.slack_client:  # Slackクライアントがない場合
            logger.warning("Slack APIが設定されていません")  # 警告出力
            return []  # 空のリストを返す

        try:
            # ユーザー一覧を取得
            response = self.slack_client.users_list()  # APIコール

            if not response['ok']:  # エラーの場合
                logger.error(f"Slackユーザー取得エラー: {response.get('error')}")  # エラー出力
                return []  # 空のリストを返す

            users = []  # ユーザーリスト
            for member in response['members']:  # 各メンバーに対して
                # botやdeactivatedユーザーを除外
                if member.get('is_bot') or member.get('deleted'):  # botまたは削除済みの場合
                    continue  # スキップ

                user_info = {
                    'id': member['id'],  # ユーザーID
                    'name': member.get('name', ''),  # ユーザー名
                    'display_name': member.get('profile', {}).get('display_name', ''),  # 表示名
                    'real_name': member.get('profile', {}).get('real_name', ''),  # 実名
                }  # ユーザー情報辞書
                users.append(user_info)  # リストに追加

            logger.info(f"Slackから {len(users)}人のユーザー情報を取得")  # 取得数ログ
            return users  # ユーザーリストを返す

        except SlackApiError as e:  # Slack APIエラー
            logger.error(f"Slack API呼び出しエラー: {e.response['error']}")  # エラー出力
            return []  # 空のリストを返す
        except Exception as e:  # その他のエラー
            logger.error(f"予期しないエラー: {e}")  # エラー出力
            return []  # 空のリストを返す

    async def get_discord_display_names(self, user_ids: Set[str]) -> Dict[str, str]:
        """Discord APIを使用してサーバーニックネームを取得

        Args:
            user_ids: Discord User IDのセット

        Returns:
            user_id -> display_nameのマッピング辞書
        """
        display_names = {}  # 結果を格納する辞書

        discord_token = self.config.get('discord_token')  # Discordトークン取得
        if not discord_token:  # トークンがない場合
            logger.warning("Discord Botトークンが設定されていません")  # 警告出力
            return display_names  # 空の辞書を返す

        try:
            # Discord Botクライアントの設定
            intents = discord.Intents.default()  # デフォルトIntents
            intents.guilds = True  # ギルド情報権限を有効化
            intents.members = True  # メンバー情報権限を有効化

            client = discord.Client(intents=intents)  # クライアント作成
            data_collected = asyncio.Event()  # データ収集完了イベント

            @client.event
            async def on_ready():  # Bot接続完了時の処理
                try:
                    logger.info(f"Discord Botとして接続: {client.user}")  # 接続ログ

                    # すべてのギルドを検索
                    for guild in client.guilds:  # 各ギルドに対して
                        logger.debug(f"ギルド確認中: {guild.name} (ID: {guild.id})")  # デバッグログ

                        # 各ユーザーIDについてメンバー情報を取得
                        for user_id in user_ids:  # 各ユーザーIDに対して
                            if user_id in display_names:  # すでに取得済みの場合
                                continue  # スキップ

                            try:
                                member = guild.get_member(int(user_id))  # メンバー取得
                                if member:  # メンバーが存在する場合
                                    # display_nameプロパティを使用（ニックネーム > グローバル名 > ユーザー名の優先順位）
                                    display_name = member.display_name  # 表示名を取得
                                    display_names[user_id] = display_name  # 表示名を保存
                                    logger.debug(f"表示名取得: {user_id} -> {display_name} (nick: {member.nick}, name: {member.name})")  # デバッグログ
                            except Exception as e:  # エラー時
                                logger.debug(f"メンバー {user_id} の取得エラー: {e}")  # デバッグログ

                except Exception as e:  # エラー時
                    logger.error(f"Discord表示名取得エラー: {e}")  # エラー出力
                finally:
                    data_collected.set()  # データ収集完了を通知
                    await client.close()  # クライアント終了

            # Botを起動（タイムアウト付き）
            bot_task = asyncio.create_task(client.start(discord_token))  # タスク作成

            # データ取得完了まで待機（最大30秒）
            await asyncio.wait_for(data_collected.wait(), timeout=30.0)  # タイムアウト付き待機

        except asyncio.TimeoutError:  # タイムアウト時
            logger.warning("Discord接続タイムアウト")  # 警告出力
        except Exception as e:  # エラー時
            logger.error(f"Discord API呼び出しエラー: {e}")  # エラー出力
        finally:
            if 'client' in locals() and not client.is_closed():  # クライアントが存在し閉じていない場合
                await client.close()  # クライアントを閉じる

        logger.info(f"Discord表示名を {len(display_names)} 件取得")  # 取得数ログ
        return display_names  # 表示名辞書を返す

    def write_slack_users_to_sheet(self, users: List[Dict[str, str]]):
        """Slackユーザー一覧をマッピングシートのslack_usersタブに書き込み

        Args:
            users: Slackユーザー情報のリスト
        """
        if not users:  # ユーザーがない場合
            logger.info("書き込むSlackユーザーがありません")  # ログ出力
            return  # 処理終了

        # マッピングシートのパスを取得
        mapping_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # パス取得
        if not mapping_path:  # パスがない場合
            logger.error("マッピングシートパスが設定されていません")  # エラー出力
            return  # 処理終了

        # ファイル名を抽出
        sheet_name = mapping_path.split('/')[-1]  # ファイル名取得

        # シートを検索
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()  # ファイル検索

        sheets = results.get('files', [])  # シートリスト取得
        if not sheets:  # シートが見つからない場合
            logger.error(f"マッピングシートが見つかりません: {sheet_name}")  # エラー出力
            return  # 処理終了

        sheet_id = sheets[0]['id']  # シートID取得
        logger.info(f"マッピングシート発見: {sheet_name}")  # 発見ログ

        # slack_usersタブが存在するか確認
        tab_name = 'slack_users'  # タブ名
        try:
            # 既存のタブ一覧を取得
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()  # スプレッドシート情報取得

            # タブが存在するか確認
            tab_exists = False  # タブ存在フラグ
            for sheet in spreadsheet.get('sheets', []):  # 各シートをチェック
                if sheet['properties']['title'] == tab_name:  # タブ名が一致
                    tab_exists = True  # 存在フラグを立てる
                    break  # ループ終了

            if not tab_exists:  # タブが存在しない場合
                # 新しいタブを追加
                request = {
                    'addSheet': {
                        'properties': {
                            'title': tab_name  # タブ名設定
                        }
                    }
                }  # リクエストボディ
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=sheet_id,
                    body={'requests': [request]}
                ).execute()  # タブ追加
                logger.info(f"新しいタブを作成: {tab_name}")  # ログ出力
            else:  # タブが存在する場合
                logger.info(f"既存のタブを更新: {tab_name}")  # ログ出力

        except Exception as e:  # エラー時
            logger.error(f"タブ確認エラー: {e}")  # エラー出力
            return  # 処理終了

        # データを準備
        header = [['Slack ID', 'User Name', 'Display Name', 'Real Name']]  # ヘッダー行
        rows = []  # データ行リスト
        for user in users:  # 各ユーザーに対して
            rows.append([
                user['id'],  # Slack ID
                user['name'],  # ユーザー名
                user['display_name'],  # 表示名
                user['real_name']  # 実名
            ])  # 行データ追加

        # 全データを結合
        all_data = header + rows  # ヘッダー＋データ

        # シートをクリアして新しいデータを書き込み
        try:
            # 既存データをクリア
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=f'{tab_name}!A:D'
            ).execute()  # データクリア

            # 新しいデータを書き込み
            body = {'values': all_data}  # リクエストボディ
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=f'{tab_name}!A1',
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()  # データ書き込み

            logger.info(f"✅ {len(users)}人のSlackユーザー情報を{tab_name}タブに書き込み完了")  # 成功ログ

        except Exception as e:  # エラー時
            logger.error(f"シート書き込みエラー: {e}")  # エラー出力

    def check_unmapped_users(self) -> List[Tuple[str, str]]:
        """マッピングシートでSlack IDが未設定のユーザーを確認

        Returns:
            List[Tuple[discord_id, discord_name]]: 未マッピングユーザーのリスト
        """
        unmapped_users = []  # 未マッピングユーザーリスト

        # マッピングシートのパスを取得
        mapping_path = self.config.get('google_drive_discord_slack_mapping_sheet_path')  # パス取得
        if not mapping_path:  # パスがない場合
            logger.error("マッピングシートパスが設定されていません")  # エラー出力
            return unmapped_users  # 空のリストを返す

        # ファイル名を抽出
        sheet_name = mapping_path.split('/')[-1]  # ファイル名取得

        # シートを検索
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"  # 検索クエリ
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()  # ファイル検索

        sheets = results.get('files', [])  # シートリスト取得
        if not sheets:  # シートが見つからない場合
            logger.warning(f"マッピングシートが見つかりません: {sheet_name}")  # 警告出力
            return unmapped_users  # 空のリストを返す

        sheet_id = sheets[0]['id']  # シートID取得
        sheet_url = sheets[0].get('webViewLink', '')  # シートURL取得

        # マッピングデータを読み込み
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')  # タブ名
        range_name = f'{tab_name}!A:D'  # 範囲指定（D列まで）

        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()  # データ取得

            values = result.get('values', [])  # 値リスト取得

            # ヘッダー行をスキップして、未マッピングユーザーを収集
            for row in values[1:]:  # ヘッダー以外の行
                if row and len(row) >= 2:  # 行が存在し、少なくとも2列ある場合
                    discord_id = row[0].strip()  # Discord ID
                    discord_name = row[1].strip()  # Discord名
                    display_name = row[2].strip() if len(row) > 2 else discord_name.split('#')[0]  # 表示名（あれば）
                    slack_id = row[3].strip() if len(row) > 3 else ''  # Slack ID（あれば）

                    if discord_id and discord_name and not slack_id:  # Slack IDが空の場合
                        unmapped_users.append((discord_id, display_name))  # 未マッピングリストに追加（表示名を使用）

        except Exception as e:  # エラー時
            logger.error(f"マッピングデータ読み込みエラー: {e}")  # エラー出力

        logger.info(f"未マッピングユーザー数: {len(unmapped_users)}")  # 未マッピング数ログ
        return unmapped_users, sheet_url  # 未マッピングユーザーとシートURLを返す

    def notify_unmapped_users(self, unmapped_users: List[Tuple[str, str]], sheet_url: str):
        """未マッピングユーザーについてSlackに通知

        Args:
            unmapped_users: 未マッピングユーザーのリスト
            sheet_url: マッピングシートのURL
        """
        if not unmapped_users:  # 未マッピングユーザーがいない場合
            logger.info("すべてのユーザーがマッピング済みです")  # ログ出力
            return  # 処理終了

        if not self.enable_slack_notify:  # Slack通知が無効の場合
            logger.info("⚠️ ドライランモード：Slack通知をスキップ")  # 情報ログ
            logger.info(f"  未マッピングユーザー数: {len(unmapped_users)}名")  # 未マッピング数表示
            for discord_id, name in unmapped_users[:5]:  # 最初の5件を表示
                logger.info(f"    - {name} (Discord表示名) / ID: {discord_id}")  # ユーザー情報
            if len(unmapped_users) > 5:  # 5件以上の場合
                logger.info(f"    ... 他 {len(unmapped_users) - 5}名")  # 残りの人数
            return  # 処理終了

        if not self.slack_client:  # Slackクライアントがない場合
            logger.warning("Slack APIが設定されていないため、通知をスキップ")  # 警告出力
            return  # 処理終了

        # 通知メッセージを作成
        user_list = '\n'.join([f"• {name} (Discord表示名) / ID: {discord_id}" for discord_id, name in unmapped_users])  # ユーザーリスト作成

        message = f""":warning: **Discord-Slackマッピング未設定のユーザーがいます**

以下のユーザーのSlack IDが設定されていません：

{user_list}

:link: マッピングシートで紐付けを行ってください：
{sheet_url}
"""

        # Slackチャンネルに通知
        slack_channel = self.config.get('slack_channel')  # チャンネルID取得
        if not slack_channel:  # チャンネルIDがない場合
            logger.warning("Slack通知先チャンネルが設定されていません")  # 警告出力
            return  # 処理終了

        try:
            response = self.slack_client.chat_postMessage(
                channel=slack_channel,
                text=message,
                mrkdwn=True
            )  # メッセージ送信

            if response['ok']:  # 送信成功の場合
                logger.info(f"✅ Slackに未マッピングユーザーの通知を送信しました")  # 成功ログ
            else:  # 送信失敗の場合
                logger.error(f"Slack通知送信エラー: {response.get('error')}")  # エラー出力

        except SlackApiError as e:  # Slack APIエラー
            logger.error(f"Slack通知エラー: {e.response['error']}")  # エラー出力
        except Exception as e:  # その他のエラー
            logger.error(f"予期しないエラー: {e}")  # エラー出力

    def run(self):
        """メイン処理を実行"""
        logger.info("=" * 60)  # 区切り線
        logger.info("Discord-Slackマッピング自動更新を開始")  # 開始ログ
        logger.info(f"環境: {['本番', 'テスト', '開発'][self.env]}")  # 環境ログ
        logger.info("=" * 60)  # 区切り線

        # CSVからユーザー情報を取得
        logger.info("\n📁 CSVファイルからユーザー情報を取得中...")  # 処理開始ログ
        csv_users = self.get_users_from_csv()  # CSVユーザー取得

        if csv_users:  # CSVユーザーがある場合
            # Discord APIから表示名を取得
            logger.info("\n🎮 Discordからサーバー表示名を取得中...")  # 処理開始ログ
            user_ids = set(csv_users.keys())  # ユーザーIDのセット

            # 非同期処理を実行
            loop = asyncio.new_event_loop()  # 新しいイベントループ作成
            asyncio.set_event_loop(loop)  # イベントループを設定
            try:
                self.discord_members = loop.run_until_complete(self.get_discord_display_names(user_ids))  # 表示名取得
            finally:
                loop.close()  # イベントループを閉じる

            # 取得した表示名でCSVユーザー情報を更新
            for user_id in csv_users:  # 各ユーザーID
                discord_name, _, vc_name = csv_users[user_id]  # 現在の情報
                display_name = self.discord_members.get(user_id, discord_name.split('#')[0])  # 表示名取得（なければユーザー名）
                csv_users[user_id] = (discord_name, display_name, vc_name)  # 更新

        if not csv_users:  # ユーザーがない場合
            logger.warning("CSVファイルにユーザーが見つかりませんでした")  # 警告出力
            return  # 処理終了

        # マッピングシートから既存ユーザーを取得
        logger.info("\n📋 マッピングシートの既存データを確認中...")  # 処理開始ログ
        existing_ids = self.get_existing_mapping()  # 既存ID取得

        # 新規ユーザーを特定
        new_users = []  # 新規ユーザーリスト
        for discord_id, (discord_name, display_name, vc_name) in csv_users.items():  # 各CSVユーザー
            if discord_id not in existing_ids:  # 新規の場合
                new_users.append((discord_id, discord_name, display_name, vc_name))  # リストに追加
                logger.debug(f"  新規ユーザー検出: {discord_name} / {display_name} (ID: {discord_id})")  # デバッグログ

        # デバッグ: 既存ユーザーと CSV ユーザーの比較
        logger.debug(f"CSV ユーザーID一覧: {set(csv_users.keys())}")  # CSVのID一覧
        logger.debug(f"既存マッピングID一覧: {existing_ids}")  # 既存のID一覧

        logger.info(f"\n🔍 分析結果:")  # 分析結果ログ
        logger.info(f"  - CSV内のユーザー数: {len(csv_users)}")  # CSV数
        logger.info(f"  - 既存マッピング数: {len(existing_ids)}")  # 既存数
        logger.info(f"  - 新規ユーザー数: {len(new_users)}")  # 新規数

        # 新規ユーザーをマッピングシートに追加
        if new_users:  # 新規ユーザーがある場合
            logger.info("\n➕ 新規ユーザーをマッピングシートに追加中...")  # 処理開始ログ
            self.append_new_users(new_users)  # 追加処理
        else:  # 新規ユーザーがない場合
            logger.info("\n✅ すべてのユーザーは既にマッピング済みです")  # 完了ログ

        # Slackユーザー一覧を取得してシートに書き込み
        logger.info("\n👥 Slackユーザー一覧を取得中...")  # 処理開始ログ
        slack_users = self.get_slack_users()  # Slackユーザー取得
        if slack_users:  # ユーザーが取得できた場合
            logger.info("\n📝 Slackユーザー一覧をスプレッドシートに書き込み中...")  # 処理開始ログ
            self.write_slack_users_to_sheet(slack_users)  # シートに書き込み

        # 未マッピングユーザーをチェックして通知
        logger.info("\n🔍 未マッピングユーザーをチェック中...")  # 処理開始ログ
        unmapped_users, sheet_url = self.check_unmapped_users()  # 未マッピングチェック
        if unmapped_users:  # 未マッピングユーザーがいる場合
            if self.enable_slack_notify:  # Slack通知が有効の場合
                logger.info("\n📢 Slackに未マッピングユーザーの通知を送信中...")  # 処理開始ログ
            self.notify_unmapped_users(unmapped_users, sheet_url)  # Slack通知（フラグに応じて処理）

        logger.info("\n" + "=" * 60)  # 区切り線
        logger.info("処理完了")  # 完了ログ
        logger.info("=" * 60)  # 区切り線


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='Discord-Slackマッピングを自動更新'
    )  # 引数パーサー作成
    parser.add_argument(
        '--env',
        type=int,
        default=2,
        choices=[0, 1, 2],
        help='環境 (0=本番, 1=テスト, 2=開発)'
    )  # 環境引数追加
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Slack通知を無効化 (デフォルト: 有効)'
    )  # ドライランモード
    args = parser.parse_args()  # 引数パース

    env = Environment(args.env)  # 環境設定
    enable_slack = not args.dry_run  # Slack通知の有効/無効を設定（dry-run時は無効）
    updater = MappingUpdater(env, enable_slack_notify=enable_slack)  # 更新クラス作成
    updater.run()  # 実行


if __name__ == "__main__":
    main()  # メイン関数実行