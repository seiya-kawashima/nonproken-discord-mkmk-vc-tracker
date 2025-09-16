#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive上のCSVファイルを確認するスクリプト
"""

import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import EnvConfig, Environment

def main():
    """メイン処理"""
    # 開発環境の設定を取得
    env = Environment.DEV
    drive_config = EnvConfig.get_google_drive_config(env)

    # 認証
    service_account_json = drive_config.get('service_account_json')
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
        scopes=['https://www.googleapis.com/auth/drive']
    )

    # Drive APIサービスの構築
    service = build('drive', 'v3', credentials=credentials)

    print("🔍 Google Drive上のファイル構造を確認します...")
    print("=" * 60)

    # 共有ドライブIDを取得
    shared_drive_id = drive_config.get('shared_drive_id', '0ANixFe4JBQskUk9PVA')
    print(f"🔗 共有ドライブID: {shared_drive_id}")

    # discord_mokumoku_trackerフォルダを検索（共有ドライブをサポート）
    query = "name='discord_mokumoku_tracker' and mimeType='application/vnd.google-apps.folder'"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora='allDrives'
    ).execute()
    folders = results.get('files', [])

    if not folders:
        print("❌ discord_mokumoku_trackerフォルダが見つかりません")
        return

    root_folder_id = folders[0]['id']
    print(f"✅ discord_mokumoku_tracker (ID: {root_folder_id})")

    # csvサブフォルダを検索
    query = f"'{root_folder_id}' in parents and name='csv' and mimeType='application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    csv_folders = results.get('files', [])

    if not csv_folders:
        print("  ❌ csvフォルダが見つかりません")
        return

    csv_folder_id = csv_folders[0]['id']
    print(f"  ✅ csv (ID: {csv_folder_id})")

    # VCチャンネルフォルダを検索
    query = f"'{csv_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    channel_folders = results.get('files', [])

    print(f"  📁 {len(channel_folders)}個のVCチャンネルフォルダ:")

    for channel_folder in channel_folders:
        channel_id = channel_folder['id']
        channel_name = channel_folder['name']
        print(f"    📂 {channel_name} (ID: {channel_id})")

        # チャンネルフォルダ内のすべてのファイルを表示
        query = f"'{channel_id}' in parents"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        files = results.get('files', [])

        if files:
            for file in files:
                file_name = file['name']
                file_type = "📄" if 'csv' in file['mimeType'] or file_name.endswith('.csv') else "📁"
                print(f"      {file_type} {file_name}")

                # 2_DEV.csvを特に探す
                if file_name == "2_DEV.csv":
                    print(f"        🎯 ターゲットファイル発見！")
        else:
            print(f"      (空のフォルダ)")

    print("=" * 60)

    # 特定のファイルを直接検索
    print("\n📍 2_DEV.csvを直接検索...")
    query = "name='2_DEV.csv'"
    results = service.files().list(q=query, fields="files(id, name, parents)").execute()
    files = results.get('files', [])

    if files:
        print(f"✅ {len(files)}個の2_DEV.csvファイルが見つかりました:")
        for file in files:
            print(f"  - {file['name']} (ID: {file['id']}, Parents: {file.get('parents', [])})")
    else:
        print("❌ 2_DEV.csvファイルが見つかりません")

if __name__ == '__main__':
    main()