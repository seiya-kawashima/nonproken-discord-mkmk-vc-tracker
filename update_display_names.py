#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""既存マッピングシートのDiscord表示名を更新するスクリプト"""

import os
import sys
import asyncio
import discord
from typing import Dict, Set
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import get_config, Environment
from loguru import logger

# ログ設定
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level} | {message}")

class DisplayNameUpdater:
    """Discord表示名更新クラス"""

    def __init__(self, env: Environment = Environment.DEV):
        self.config = get_config(env)
        self.drive_service = None
        self.sheets_service = None
        self.initialize_services()

    def initialize_services(self):
        """Google APIサービスを初期化"""
        service_account_json = self.config['google_drive_service_account_json']
        credentials = service_account.Credentials.from_service_account_file(
            service_account_json,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets'
            ]
        )

        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)

    async def get_discord_display_names(self, user_ids: Set[str]) -> Dict[str, str]:
        """Discord APIから表示名を取得"""
        display_names = {}

        discord_token = self.config.get('discord_token')
        if not discord_token:
            logger.error("Discordトークンが設定されていません")
            return display_names

        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True

        client = discord.Client(intents=intents)
        data_collected = asyncio.Event()

        @client.event
        async def on_ready():
            try:
                logger.info(f"Discord接続: {client.user}")

                for guild in client.guilds:
                    logger.info(f"ギルド: {guild.name}")

                    for user_id in user_ids:
                        if user_id in display_names:
                            continue

                        try:
                            member = guild.get_member(int(user_id))
                            if member:
                                # display_nameを使用（正しい表示名）
                                display_name = member.display_name
                                display_names[user_id] = display_name
                                logger.info(f"  {member.name} → {display_name}")
                        except Exception as e:
                            logger.debug(f"エラー: {e}")

            finally:
                data_collected.set()
                await client.close()

        try:
            bot_task = asyncio.create_task(client.start(discord_token))
            await asyncio.wait_for(data_collected.wait(), timeout=30.0)
        except Exception as e:
            logger.error(f"Discord接続エラー: {e}")
        finally:
            if not client.is_closed():
                await client.close()

        return display_names

    def update_sheet_display_names(self, display_names: Dict[str, str]):
        """スプレッドシートの表示名を更新"""

        # シートを検索
        sheet_name = 'discord_slack_mapping'
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()

        sheets = results.get('files', [])
        if not sheets:
            logger.error(f"シートが見つかりません: {sheet_name}")
            return

        sheet_id = sheets[0]['id']
        logger.info(f"シート発見: {sheet_name}")

        # 既存データを読み込み
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')
        range_name = f'{tab_name}!A:D'

        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])

        # 更新データを準備
        updates = []
        for i, row in enumerate(values):
            if i == 0:  # ヘッダー行をスキップ
                continue

            if len(row) > 0:
                discord_id = row[0]
                if discord_id in display_names:
                    new_display_name = display_names[discord_id]
                    old_display_name = row[2] if len(row) > 2 else ""

                    if new_display_name != old_display_name:
                        # C列（3列目）を更新
                        updates.append({
                            'range': f'{tab_name}!C{i+1}',
                            'values': [[new_display_name]]
                        })
                        logger.info(f"更新: 行{i+1} {old_display_name} → {new_display_name}")

        # バッチ更新を実行
        if updates:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }

            self.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body=body
            ).execute()

            logger.success(f"✅ {len(updates)}件の表示名を更新しました")
        else:
            logger.info("更新が必要な表示名はありません")

    async def run(self):
        """メイン処理"""
        logger.info("=" * 50)
        logger.info("Discord表示名更新処理を開始")
        logger.info("=" * 50)

        # 既存のユーザーIDを取得
        sheet_name = 'discord_slack_mapping'
        query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives'
        ).execute()

        sheets = results.get('files', [])
        if not sheets:
            logger.error("マッピングシートが見つかりません")
            return

        sheet_id = sheets[0]['id']
        tab_name = self.config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')
        logger.info(f"タブ名: {tab_name}")

        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f'{tab_name}!A:D'
            ).execute()

            values = result.get('values', [])
        except Exception as e:
            logger.error(f"シート読み込みエラー: {e}")
            # Sheet1がない場合は最初のシートを使う
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range='A:D'
            ).execute()
            values = result.get('values', [])
        user_ids = set()

        logger.info(f"シートの行数: {len(values)}")

        for i, row in enumerate(values):
            if i == 0:
                logger.info(f"ヘッダー: {row}")
                continue
            if row and len(row) > 0 and row[0]:
                user_ids.add(row[0])
                logger.debug(f"ユーザーID追加: {row[0]}")

        logger.info(f"{len(user_ids)}人のユーザーIDを取得")

        # Discord APIから表示名を取得
        logger.info("\n📱 Discord APIから表示名を取得中...")
        display_names = await self.get_discord_display_names(user_ids)
        logger.info(f"{len(display_names)}人の表示名を取得")

        # スプレッドシートを更新
        if display_names:
            logger.info("\n📝 スプレッドシートを更新中...")
            self.update_sheet_display_names(display_names)

        logger.info("\n" + "=" * 50)
        logger.info("処理完了")
        logger.info("=" * 50)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Discord表示名を更新')
    parser.add_argument('--env', type=int, default=2, choices=[0, 1, 2],
                        help='環境 (0=本番, 1=テスト, 2=開発)')
    args = parser.parse_args()

    env = Environment(args.env)
    updater = DisplayNameUpdater(env)
    asyncio.run(updater.run())