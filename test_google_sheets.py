"""Google Sheets接続テスト用スクリプト

このスクリプトを実行して、Google Sheetsの設定が正しくできているか確認できます。
使い方: python test_google_sheets.py
"""

import gspread  # Google Sheets操作ライブラリ
from google.oauth2.service_account import Credentials  # 認証用
import os  # 環境変数取得用
from dotenv import load_dotenv  # .envファイル読み込み用
from datetime import datetime  # 現在時刻取得用

# .envファイルから環境変数を読み込み
load_dotenv()

print("=" * 50)
print("Google Sheets 接続テスト開始")
print("=" * 50)

# 認証情報を設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # スプレッドシート編集権限

# テスト環境の設定を優先的に読み込み（TEST_プレフィックス付きを先に確認）
SERVICE_ACCOUNT_FILE = os.getenv('TEST_GOOGLE_SERVICE_ACCOUNT_JSON') or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')  # 認証ファイルパス
SHEET_NAME = os.getenv('TEST_GOOGLE_SHEET_NAME') or os.getenv('GOOGLE_SHEET_NAME')  # スプレッドシート名

# 環境の判定
IS_TEST_ENV = bool(os.getenv('TEST_GOOGLE_SHEET_NAME') or os.getenv('TEST_GOOGLE_SERVICE_ACCOUNT_JSON'))
ENV_TYPE = "テスト環境" if IS_TEST_ENV else "本番環境"

# 設定値の確認
print(f"\n📋 設定確認:")
print(f"  - 認証ファイル: {SERVICE_ACCOUNT_FILE}")
print(f"  - スプレッドシート名: {SHEET_NAME}")

if not SHEET_NAME:
    print("\n❌ エラー: GOOGLE_SHEET_NAMEが設定されていません")
    print("   .envファイルに以下を追加してください:")
    print("   GOOGLE_SHEET_NAME=あなたのスプレッドシート名")
    exit(1)

if not os.path.exists(SERVICE_ACCOUNT_FILE):
    print(f"\n❌ エラー: 認証ファイル '{SERVICE_ACCOUNT_FILE}' が見つかりません")
    print("   service_account.jsonファイルをプロジェクトフォルダに配置してください")
    exit(1)

try:
    print(f"\n🔐 認証処理中...")
    
    # 認証
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    print("   ✅ 認証成功")
    
    print(f"\n📊 スプレッドシート '{SHEET_NAME}' に接続中...")
    
    # スプレッドシートを開く
    sheet = client.open(SHEET_NAME)
    worksheet = sheet.get_worksheet(0)  # 最初のシートを取得
    print("   ✅ 接続成功")
    
    print(f"\n✏️ テストデータを書き込み中...")
    
    # 現在時刻を取得
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # テストデータを書き込み
    test_data = [
        ["テスト実行日時", now],
        ["ステータス", "接続成功！"],
        ["メッセージ", "Google Sheetsの設定が正しく完了しています"]
    ]
    
    # A1から3行分のデータを書き込み
    worksheet.update('A1:B3', test_data)
    print("   ✅ 書き込み成功")
    
    # 書き込んだデータを読み取って確認
    print(f"\n📖 書き込んだデータの確認:")
    values = worksheet.get('A1:B3')
    for row in values:
        if len(row) >= 2:
            print(f"   {row[0]}: {row[1]}")
    
    print("\n" + "=" * 50)
    print("🎉 テスト成功！")
    print("=" * 50)
    print("\n✅ Google Sheetsの設定は正しく完了しています")
    print(f"✅ スプレッドシート '{SHEET_NAME}' にアクセスできます")
    print(f"✅ A1〜B3セルにテストデータを書き込みました")
    print("\n📌 次のステップ:")
    print("   1. Google Sheetsを開いて、データが書き込まれていることを確認")
    print("   2. 他の環境設定（Discord Bot、Slack Bot）を続ける")
    
except gspread.exceptions.SpreadsheetNotFound:
    print(f"\n❌ エラー: スプレッドシート '{SHEET_NAME}' が見つかりません")
    print("\n📌 確認事項:")
    print("   1. スプレッドシート名が正しいか確認")
    print("   2. サービスアカウントにスプレッドシートが共有されているか確認")
    print("      - スプレッドシートの「共有」ボタンをクリック")
    print("      - サービスアカウントのメールアドレスを追加")
    print("      - 「編集者」権限を付与")
    
except gspread.exceptions.APIError as e:
    print(f"\n❌ Google API エラー: {e}")
    print("\n📌 確認事項:")
    print("   1. Google Sheets APIが有効化されているか確認")
    print("   2. サービスアカウントの権限が正しいか確認")
    
except Exception as e:
    print(f"\n❌ 予期しないエラー: {e}")
    print("\n📌 エラーの詳細を確認して、設定を見直してください")

print("\n" + "-" * 50)
print("テスト終了")