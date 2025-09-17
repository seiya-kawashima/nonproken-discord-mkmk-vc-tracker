#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive上のCSVファイルを確認するスクリプト
"""

import os
import sys
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import get_config, get_environment_from_arg, Environment


def search_files(service, parent_id, query_suffix="", fields="files(id, name, mimeType)"):
    """フォルダ内のファイルを検索する共通関数"""
    query = f"'{parent_id}' in parents"  # 親フォルダ指定
    if query_suffix:  # 追加条件がある場合
        query += f" and {query_suffix}"

    results = service.files().list(
        q=query,
        fields=fields,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    return results.get('files', [])


def display_folder_contents(service, folder_id, folder_name, target_file, indent="    "):
    """フォルダ内容を表示する共通関数"""
    print(f"{indent}📂 {folder_name} (ID: {folder_id})")  # フォルダ情報表示

    # フォルダ内のファイルを取得
    files = search_files(service, folder_id)

    if files:
        for file in files:
            file_name = file['name']
            is_csv = 'csv' in file['mimeType'] or file_name.endswith('.csv')  # CSV判定
            file_type = "📄" if is_csv else "📁"  # アイコン選択
            print(f"{indent}  {file_type} {file_name}")  # ファイル情報表示

            # ターゲットファイルのチェック
            if file_name == target_file:
                print(f"{indent}    🎯 ターゲットファイル発見！")  # 発見ログ
    else:
        print(f"{indent}  (空のフォルダ)")  # 空フォルダ表示


def check_folder_structure(service, root_folder_id, base_folder_name, target_csv_file):
    """フォルダ構造をチェックする関数"""

    # 1. 旧構造をチェック: base_folder/csv/[VCチャンネル名]/
    print(f"\n📦 旧構造: {base_folder_name}/csv/")  # 旧構造表示
    csv_folders = search_files(
        service, root_folder_id,
        "name='csv' and mimeType='application/vnd.google-apps.folder'"
    )

    if csv_folders:
        csv_folder_id = csv_folders[0]['id']
        print(f"  ✅ csv (ID: {csv_folder_id})")  # CSVフォルダ確認

        # VCチャンネルフォルダを検索
        channel_folders = search_files(
            service, csv_folder_id,
            "mimeType='application/vnd.google-apps.folder'"
        )

        print(f"  📁 {len(channel_folders)}個のVCチャンネルフォルダ:")  # フォルダ数表示
        for channel_folder in channel_folders:
            display_folder_contents(
                service, channel_folder['id'],
                channel_folder['name'], target_csv_file
            )

    # 2. 新構造をチェック: base_folder/[VCチャンネル名]/csv/
    print(f"\n🆕 新構造: {base_folder_name}/[VCチャンネル名]/csv/")  # 新構造表示
    all_folders = search_files(
        service, root_folder_id,
        "mimeType='application/vnd.google-apps.folder'"
    )

    # csvフォルダ以外をVCチャンネルフォルダとして扱う
    vc_channel_folders = [f for f in all_folders if f['name'] != 'csv']
    print(f"  📁 {len(vc_channel_folders)}個のVCチャンネルフォルダ:")  # フォルダ数表示

    for vc_folder in vc_channel_folders:
        vc_folder_id = vc_folder['id']
        vc_folder_name = vc_folder['name']
        print(f"    📂 {vc_folder_name} (ID: {vc_folder_id})")  # VCフォルダ情報

        # csvサブフォルダを検索
        csv_subfolders = search_files(
            service, vc_folder_id,
            "name='csv' and mimeType='application/vnd.google-apps.folder'"
        )

        if csv_subfolders:
            csv_subfolder_id = csv_subfolders[0]['id']
            print(f"      📁 csv (ID: {csv_subfolder_id})")  # CSVサブフォルダ確認

            # csvフォルダ内のファイルを表示
            files = search_files(service, csv_subfolder_id)

            if files:
                for file in files:
                    file_name = file['name']
                    is_csv = 'csv' in file['mimeType'] or file_name.endswith('.csv')  # CSV判定
                    file_type = "📄" if is_csv else "📁"  # アイコン選択
                    print(f"        {file_type} {file_name}")  # ファイル表示

                    # ターゲットファイルをチェック
                    if file_name == target_csv_file:
                        print(f"          🎯 ターゲットファイル発見！")  # 発見ログ
            else:
                print(f"        (空のフォルダ)")  # 空フォルダ表示
        else:
            print(f"      (まだcsvフォルダがありません)")  # CSVフォルダなし表示


def main(env_arg=None):
    """メイン処理"""
    # 環境を取得
    try:
        env = get_environment_from_arg(env_arg)  # 環境を取得
    except ValueError as e:
        print(f"エラー: {e}")  # エラー表示
        sys.exit(1)  # 異常終了

    # 設定を取得
    config = get_config(env)  # 環境設定を取得

    # 必要な設定値を取得
    service_account_json = config['google_drive_service_account_json']  # 認証ファイルパス
    shared_drive_id = config.get('google_drive_shared_drive_id')  # 共有ドライブID
    base_folder_name = config['google_drive_base_folder']  # ベースフォルダ名
    suffix = config['suffix']  # 環境サフィックス（0_PRD/1_TST/2_DEV）
    target_csv_file = f"{suffix}.csv"  # 探すCSVファイル名

    # 認証
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
        scopes=['https://www.googleapis.com/auth/drive']
    )

    # Drive APIサービスの構築
    service = build('drive', 'v3', credentials=credentials)

    print("🔍 Google Drive上のファイル構造を確認します...")  # 開始メッセージ
    print("=" * 60)

    # 共有ドライブ情報を表示
    if shared_drive_id:
        print(f"🔗 共有ドライブID: {shared_drive_id}")  # 共有ドライブID表示
    else:
        print("🔗 マイドライブを使用")  # マイドライブ使用表示

    # ベースフォルダを検索
    query = f"name='{base_folder_name}' and mimeType='application/vnd.google-apps.folder'"
    corpora = 'allDrives' if shared_drive_id else 'user'  # 検索範囲設定

    results = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora=corpora
    ).execute()

    folders = results.get('files', [])

    if not folders:
        print(f"❌ {base_folder_name}フォルダが見つかりません")  # フォルダなしエラー
        return

    root_folder_id = folders[0]['id']
    print(f"✅ {base_folder_name} (ID: {root_folder_id})")  # ベースフォルダ確認

    # フォルダ構造をチェック
    check_folder_structure(service, root_folder_id, base_folder_name, target_csv_file)

    print("=" * 60)

    # ターゲットファイルを直接検索
    print(f"\n📍 {target_csv_file}を直接検索...")  # 直接検索開始
    query = f"name='{target_csv_file}'"
    results = service.files().list(
        q=query,
        fields="files(id, name, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora=corpora
    ).execute()

    files = results.get('files', [])

    if files:
        print(f"✅ {len(files)}個の{target_csv_file}ファイルが見つかりました:")  # ファイル発見
        for file in files:
            print(f"  - {file['name']} (ID: {file['id']}, Parents: {file.get('parents', [])})")  # ファイル詳細
    else:
        print(f"❌ {target_csv_file}ファイルが見つかりません")  # ファイルなし


if __name__ == '__main__':
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(
        description='Google Drive上のCSVファイル構造を確認'
    )
    parser.add_argument(
        '--env',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='環境を指定 (0=本番, 1=テスト, 2=開発、デフォルト=2)'
    )

    args = parser.parse_args()
    main(args.env)