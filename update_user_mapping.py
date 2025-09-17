#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ユーザー名対照表にサンプルデータを追加するスクリプト
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
    """ユーザー名対照表にサンプルデータを追加"""

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

    # 対照表を検索
    sheet_name = f"ユーザー名対照表_{env.name}"
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
        logger.error(f"対照表が見つかりません: {sheet_name}")
        return

    sheet_id = sheets[0]['id']

    # 実際のDiscordユーザーに対応するサンプルデータ
    sample_data = [
        ['1088451169604857926', 'hotta3216#0', 'U001', 'hotta', '<@U001>', 'テストユーザー1', '2025/09/16'],
        ['1130029613094588536', 'sakamo2#0', 'U002', 'sakamoto', '<@U002>', 'テストユーザー2', '2025/09/16'],
        ['690495936872710207', 'honda9355#0', 'U003', 'honda', '<@U003>', 'テストユーザー3', '2025/09/16'],
        ['455620627615899648', 'hagy4491#0', 'U004', 'hagy', '<@U004>', 'テストユーザー4', '2025/09/16'],
    ]

    # データを追加（ヘッダー行の次から）
    body = {
        'values': sample_data
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='A2:G5',  # 2行目から5行目まで
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    logger.info(f"✅ サンプルデータを追加しました")
    logger.info(f"📝 シートURL: https://docs.google.com/spreadsheets/d/{sheet_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=int, default=2, choices=[0, 1, 2])
    args = parser.parse_args()

    env = Environment(args.env)
    update_user_mapping(env)


if __name__ == "__main__":
    main()