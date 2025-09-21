#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""マッピングシートの内容を確認"""

import os
from config import get_config, Environment
from google.oauth2 import service_account
from googleapiclient.discovery import build

def check_mapping_sheet():
    """マッピングシートの内容を確認"""
    config = get_config(Environment.DEV)  # 開発環境

    # Google API認証
    service_account_json = config['google_drive_service_account_json']
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    )

    drive_service = build('drive', 'v3', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # シートを検索
    sheet_name = 'discord_slack_mapping'
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
        print(f"シートが見つかりません: {sheet_name}")
        return

    sheet_id = sheets[0]['id']
    print(f"シート発見: {sheet_name} (ID: {sheet_id})")

    # データを読み込み
    tab_name = config.get('google_drive_discord_slack_mapping_sheet_tab_name', 'Sheet1')
    range_name = f'{tab_name}!A:D'

    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    print(f"\n=== {tab_name}タブの内容（最初の5行） ===")
    for i, row in enumerate(values[:6]):
        if i == 0:
            print(f"ヘッダー: {row}")
        else:
            # 各列を安全に取得
            discord_id = row[0] if len(row) > 0 else ""
            discord_name = row[1] if len(row) > 1 else ""
            discord_display = row[2] if len(row) > 2 else ""
            slack_id = row[3] if len(row) > 3 else ""

            print(f"{i}. ID: {discord_id[:10]}..., Name: {discord_name}, Display: {discord_display}, Slack: {slack_id[:5] if slack_id else '(空)'}")

    # kawashima_noguchiさんの行を探す
    print(f"\n=== kawashima_noguchiさんの情報 ===")
    for row in values[1:]:
        if len(row) > 1 and 'kawashima' in row[1].lower():
            print(f"Discord ID: {row[0]}")
            print(f"Discord Name: {row[1]}")
            print(f"Discord Display Name: {row[2] if len(row) > 2 else '(空)'}")
            print(f"Slack ID: {row[3] if len(row) > 3 else '(空)'}")
            break

if __name__ == "__main__":
    check_mapping_sheet()