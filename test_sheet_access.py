#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""シートアクセステスト"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import get_config, Environment

config = get_config(Environment.DEV)
creds = service_account.Credentials.from_service_account_file(
    config['google_drive_service_account_json'],
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

service = build('sheets', 'v4', credentials=creds)

# 直接IDでアクセス
sheet_id = '1YbYoDIiQfA1NNPl2hiRSZ6iYXQ22E-Pk1-WWQ9i0PWk'

print("=== Sheet1タブを試す ===")
try:
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='Sheet1!A:D'
    ).execute()
    values = result.get('values', [])
    print(f"成功: {len(values)}行取得")
    if values:
        print(f"ヘッダー: {values[0]}")
except Exception as e:
    print(f"エラー: {e}")

print("\n=== タブ名なしでアクセス ===")
try:
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='A:D'
    ).execute()
    values = result.get('values', [])
    print(f"成功: {len(values)}行取得")
    if values:
        print(f"ヘッダー: {values[0]}")
except Exception as e:
    print(f"エラー: {e}")

print("\n=== スプレッドシート情報を取得 ===")
try:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    for sheet in sheets:
        props = sheet.get('properties', {})
        print(f"タブ名: {props.get('title')}, ID: {props.get('sheetId')}")
except Exception as e:
    print(f"エラー: {e}")