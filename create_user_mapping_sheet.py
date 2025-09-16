#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ユーザー名対照表シートを作成するスクリプト
Discord名とSlack名の紐付けを管理するためのGoogle Sheetsを作成
"""

import os
import sys
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import EnvConfig, Environment
from loguru import logger

# ログ設定
logger.remove()
logger.add(sys.stderr, level="INFO")


def create_user_mapping_sheet(env: Environment):
    """ユーザー名対照表シートを作成"""

    # 設定を取得
    sheets_config = EnvConfig.get_google_sheets_config(env)
    drive_config = EnvConfig.get_google_drive_config(env)

    # サービスアカウント認証
    service_account_json = sheets_config['service_account_json']
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
    )

    # APIサービスの構築
    drive_service = build('drive', 'v3', credentials=credentials)
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # スプレッドシート名
    sheet_name = f"ユーザー名対照表_{env.name}"

    # 既存のシートを検索
    query = f"name='{sheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora='allDrives'
    ).execute()

    sheets = results.get('files', [])

    if sheets:
        sheet_id = sheets[0]['id']
        logger.info(f"✅ 既存のユーザー名対照表を発見: {sheet_name} (ID: {sheet_id})")
    else:
        # 新しいスプレッドシートを作成
        spreadsheet = {
            'properties': {
                'title': sheet_name
            }
        }

        # 共有ドライブに作成する場合
        shared_drive_id = drive_config.get('shared_drive_id')
        if shared_drive_id:
            spreadsheet_metadata = {
                'name': sheet_name,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': [shared_drive_id]
            }
            file = drive_service.files().create(
                body=spreadsheet_metadata,
                supportsAllDrives=True
            ).execute()
            sheet_id = file.get('id')
        else:
            result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
            sheet_id = result['spreadsheetId']

        logger.info(f"✅ 新しいユーザー名対照表を作成: {sheet_name} (ID: {sheet_id})")

    # ヘッダーを設定
    headers = [
        ['Discord ID', 'Discord名', 'Slack ID', 'Slack名', 'Slackメンション', '備考', '最終更新']
    ]

    # サンプルデータ（実際のデータは手動で入力）
    sample_data = [
        ['1234567890', 'user1#0001', 'U1234567', 'user1', '<@U1234567>', 'サンプル', '2025/09/16'],
        ['0987654321', 'user2#0002', 'U7654321', 'user2', '<@U7654321>', 'サンプル', '2025/09/16'],
    ]

    # データを書き込み
    body = {
        'values': headers + sample_data
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='A1',
        valueInputOption='USER_ENTERED',
        body=body
    ).execute()

    # フォーマットを設定
    requests = [
        # ヘッダー行を太字に
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True
                        },
                        'backgroundColor': {
                            'red': 0.9,
                            'green': 0.9,
                            'blue': 0.9
                        }
                    }
                },
                'fields': 'userEnteredFormat(textFormat,backgroundColor)'
            }
        },
        # 列幅を調整
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 7
                },
                'properties': {
                    'pixelSize': 150
                },
                'fields': 'pixelSize'
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': requests}
    ).execute()

    logger.info(f"📊 ユーザー名対照表の準備が完了しました")
    logger.info(f"📝 シートURL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    logger.info(f"⚠️ Discord名とSlack名の紐付けを手動で入力してください")

    return sheet_id


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='ユーザー名対照表シートを作成')
    parser.add_argument('--env', type=int, default=2, choices=[0, 1, 2],
                       help='実行環境 (0=本番, 1=テスト, 2=開発, デフォルト=2)')

    args = parser.parse_args()
    env = Environment(args.env)
    env_name = EnvConfig.get_environment_name(env)

    logger.info(f"🌐 {env_name}で実行中です")

    create_user_mapping_sheet(env)


if __name__ == "__main__":
    main()