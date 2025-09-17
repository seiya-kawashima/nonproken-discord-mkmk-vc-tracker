#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord-Slackユーザーマッピングシートを更新するスクリプト
"""

import os
import sys
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import get_config, Environment
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def update_user_mapping(env: Environment):
    """Discord-Slackマッピングシートにデータを追加"""

    # 設定を取得
    config = get_config(env)

    # 認証
    service_account_json = config['google_drive_service_account_json']
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    )

    # APIサービス
    drive_service = build('drive', 'v3', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # マッピングシートを検索
    mapping_path = config.get('google_drive_discord_slack_mapping_sheet_path')
    if not mapping_path:
        logger.error("マッピングシートパスが設定されていません")
        return

    # パスからファイル名を取得
    sheet_name = mapping_path.split('/')[-1]

    query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora='allDrives'
    ).execute()

    sheets = results.get('files', [])
    if not sheets:
        logger.error(f"マッピングシートが見つかりません: {sheet_name}")
        return

    sheet_id = sheets[0]['id']
    logger.info(f"マッピングシートを発見: {sheet_name} (ID: {sheet_id})")

    # 既存データを確認
    tab_name = config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')
    range_name = f'{tab_name}!A:C'

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()

    existing_values = result.get('values', [])
    logger.info(f"既存データ: {len(existing_values)}行")

    # 実際のDiscordユーザーに対応するサンプルデータ
    # 本番環境で実際に存在するユーザーIDとSlackメンションIDのマッピング
    sample_data = [
        ['Discord User ID', 'Discord User Name', 'Slack Mention ID'],  # ヘッダー
        ['1088451169604857926', 'hotta3216', 'U001SAMPLE'],
        ['1130029613094588536', 'sakamo2', 'U002SAMPLE'],
        ['690495936872710207', 'honda9355', 'U003SAMPLE'],
        ['455620627615899648', 'hagy4491', 'U004SAMPLE'],
    ]

    # データを書き込み（全体を上書き）
    body = {
        'values': sample_data
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f'{tab_name}!A1:C{len(sample_data)}',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    logger.info(f"✅ マッピングデータを更新しました（{len(sample_data)-1}件）")
    logger.info(f"📝 シートURL: https://docs.google.com/spreadsheets/d/{sheet_id}")


def main():
    parser = argparse.ArgumentParser(
        description='Discord-Slackユーザーマッピングシートを更新'
    )
    parser.add_argument(
        '--env',
        type=int,
        default=2,
        choices=[0, 1, 2],
        help='環境 (0=本番, 1=テスト, 2=開発)'
    )
    args = parser.parse_args()

    env = Environment(args.env)
    env_name = {
        Environment.PRD: "本番環境",
        Environment.TST: "テスト環境",
        Environment.DEV: "開発環境"
    }[env]

    logger.info(f"環境: {env_name}")
    update_user_mapping(env)


if __name__ == "__main__":
    main()