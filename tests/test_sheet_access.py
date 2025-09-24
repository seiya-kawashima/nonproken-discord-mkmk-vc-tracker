#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Googleスプレッドシートアクセステストツール
Google Sheets APIを使用してスプレッドシートへのアクセスをテストする
認証やAPI接続の動作確認用スクリプト
"""

from google.oauth2 import service_account  # Google認証用
from googleapiclient.discovery import build  # Google APIクライアント作成用
from config import get_config, Environment  # 設定取得用

config = get_config(Environment.DEV)  # 開発環境の設定を取得
creds = service_account.Credentials.from_service_account_file(  # 認証情報を作成
    config['google_drive_service_account_json'],  # サービスアカウントJSONファイル
    scopes=['https://www.googleapis.com/auth/spreadsheets']  # スプレッドシート読み書き権限
)

service = build('sheets', 'v4', credentials=creds)  # Sheets APIサービスを作成

# 直接IDでアクセス
sheet_id = '1YbYoDIiQfA1NNPl2hiRSZ6iYXQ22E-Pk1-WWQ9i0PWk'  # テスト用スプレッドシートID

print("=== Sheet1タブを試す ===")  # テスト1：Sheet1タブへのアクセス
try:  # エラーハンドリング
    result = service.spreadsheets().values().get(  # シートデータを取得
        spreadsheetId=sheet_id,  # スプレッドシートID
        range='Sheet1!A:D'  # Sheet1タブのAからD列を取得
    ).execute()  # API実行
    values = result.get('values', [])  # 取得した値を取得（デフォルト空リスト）
    print(f"成功: {len(values)}行取得")  # 取得行数を表示
    if values:  # データがある場合
        print(f"ヘッダー: {values[0]}")  # ヘッダー行を表示
except Exception as e:  # エラー発生時
    print(f"エラー: {e}")  # エラーメッセージを表示

print("\n=== タブ名なしでアクセス ===")  # テスト2：タブ名省略アクセス
try:  # エラーハンドリング
    result = service.spreadsheets().values().get(  # シートデータを取得
        spreadsheetId=sheet_id,  # スプレッドシートID
        range='A:D'  # タブ名を省略してAからD列を取得
    ).execute()  # API実行
    values = result.get('values', [])  # 取得した値を取得
    print(f"成功: {len(values)}行取得")  # 取得行数を表示
    if values:  # データがある場合
        print(f"ヘッダー: {values[0]}")  # ヘッダー行を表示
except Exception as e:  # エラー発生時
    print(f"エラー: {e}")  # エラーメッセージを表示

print("\n=== スプレッドシート情報を取得 ===")  # テスト3：シート情報取得
try:  # エラーハンドリング
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()  # スプレッドシート情報を取得
    sheets = spreadsheet.get('sheets', [])  # タブ情報のリストを取得
    for sheet in sheets:  # 各タブをループ
        props = sheet.get('properties', {})  # タブのプロパティを取得
        print(f"タブ名: {props.get('title')}, ID: {props.get('sheetId')}")  # タブ名とIDを表示
except Exception as e:  # エラー発生時
    print(f"エラー: {e}")  # エラーメッセージを表示