#!/usr/bin/env python3
"""Google Sheets接続テスト（CI/CD専用）

GitHub Actionsで実行され、Google Sheetsへの接続を確認します。
接続に失敗した場合はエラーコード1で終了します。

使い方: python tests/auth_tests/test_google_sheets_ci.py
"""

import sys
import os
import json
import base64
import tempfile
from datetime import datetime
import subprocess

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import gspread
from google.oauth2.service_account import Credentials
from config import EnvConfig, Environment


def get_github_secrets_list():
    """設定されているGitHub Secretsの一覧を取得
    
    Returns:
        list: Secrets名のリスト（取得できない場合は空リスト）
    """
    try:
        # gh CLIを使用してSecrets一覧を取得
        result = subprocess.run(
            ['gh', 'secret', 'list', '--json', 'name'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            secrets = json.loads(result.stdout)
            return [s['name'] for s in secrets]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        pass
    return []


def test_google_sheets_connection():
    """Google Sheets接続テストのメイン処理"""
    
    print("=" * 70)
    print("Google Sheets CI/CD 接続テスト")
    print("=" * 70)
    
    # GitHub Actions環境かチェック  
    is_github = EnvConfig.is_github_actions()
    print(f"\n実行環境: {'GitHub Actions' if is_github else 'ローカル'}")
    
    # テスト環境の設定を取得
    try:
        config = EnvConfig.get_google_sheets_config(Environment.TST)
    except ValueError as e:
        print(f"\n❗ 設定エラー: {e}")
        
        # GitHub Actions環境の場合はSecrets一覧を表示
        if is_github:
            print("\n🔑 現在設定されているGitHub Secrets:")
            secrets_list = get_github_secrets_list()
            if secrets_list:
                for secret in secrets_list:
                    print(f"  - {secret}")
            else:
                print("  (一覧を取得できませんでした)")
            
            print("\n💡 必要なSecrets:")
            print("  - TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
            print("\n※ TST_プレフィックス付きの環境変数が必要です")
        
        sys.exit(1)
    sheet_name = config['sheet_name']
    service_account_json = config['service_account_json']
    service_account_json_base64 = config['service_account_json_base64']
    
    print("\n📋 環境変数チェック:")
    print(f"  TST_GOOGLE_SHEET_NAME: ✅ {sheet_name}")
    print(f"  TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64: {'✅ 設定済み' if service_account_json_base64 else '❌ 未設定'}")
    print(f"  TST_GOOGLE_SERVICE_ACCOUNT_JSON: {'✅ 設定済み' if service_account_json else '❌ 未設定'}")
    
    # 認証ファイルの処理
    auth_file = None
    temp_file = None
    
    if service_account_json_base64:
        # Base64エンコードされた認証情報をデコード
        print("\n🔐 Base64認証情報をデコード中...")
        try:
            decoded_bytes = base64.b64decode(service_account_json_base64)
            decoded_str = decoded_bytes.decode('utf-8')
            json_data = json.loads(decoded_str)
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_data, f)
                temp_file = f.name
                auth_file = temp_file
            print("  ✅ デコード成功")
        except Exception as e:
            print(f"  ❌ デコード失敗: {e}")
            sys.exit(1)
    elif service_account_json and os.path.exists(service_account_json):
        # ファイルが存在する場合
        auth_file = service_account_json
        print(f"\n🔐 認証ファイル使用: {service_account_json}")
    else:
        # config.pyで既にチェック済みなのでここには来ないが、念のため
        print("\n❌ エラー: 認証情報が見つかりません")
        print("   以下のいずれかを設定してください:")
        print("   - TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 (GitHub Secrets)")
        print("   - TST_GOOGLE_SERVICE_ACCOUNT_JSON (ファイルパス)")
        sys.exit(1)
    
    # Google Sheetsへの接続テスト
    try:
        print(f"\n📊 Google Sheets '{sheet_name}' に接続中...")
        
        # 認証
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(auth_file, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # スプレッドシートを開く
        sheet = client.open(sheet_name)
        worksheet = sheet.get_worksheet(0)
        print("  ✅ 接続成功")
        
        # テストデータを書き込み
        print("\n✏️ テストデータを書き込み中...")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_data = [
            ["CI/CD Test", now],
            ["Status", "✅ Success"],
            ["Environment", "GitHub Actions" if is_github else "Local"]
        ]
        
        worksheet.update('A1:B3', test_data)
        print("  ✅ 書き込み成功")
        
        # 読み取りテスト
        print("\n📖 データ読み取りテスト...")
        values = worksheet.get('A1:B3')
        if values and len(values) > 0:
            print("  ✅ 読み取り成功")
            for row in values:
                if len(row) >= 2:
                    print(f"     {row[0]}: {row[1]}")
        
        print("\n" + "=" * 70)
        print("✅ 接続テスト成功！")
        print("=" * 70)
        print(f"スプレッドシート '{sheet_name}' への接続が確認されました")
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\n❌ エラー: スプレッドシート '{sheet_name}' が見つかりません")
        print("\n確認事項:")
        print("1. スプレッドシート名が正しいか確認")
        print(f"   期待されるシート名: 'TST_VCトラッカー'")
        print("2. サービスアカウントに共有されているか確認:")
        print("   - Google Sheetsで「共有」ボタンをクリック")
        print("   - サービスアカウントのメールアドレスを追加")
        print("   - 「編集者」権限を付与")
        
        # GitHub Actions環境の場合はSecrets一覧を表示
        if is_github:
            print("\n🔑 現在設定されているGitHub Secrets:")
            secrets_list = get_github_secrets_list()
            if secrets_list:
                for secret in secrets_list:
                    print(f"  - {secret}")
            else:
                print("  (一覧を取得できませんでした)")
        
        sys.exit(1)
        
    except gspread.exceptions.APIError as e:
        print(f"\n❌ Google API エラー: {e}")
        print("\n確認事項:")
        print("1. Google Sheets APIが有効化されているか")
        print("2. サービスアカウントの権限が正しいか")
        
        # GitHub Actions環境の場合はSecrets一覧を表示
        if is_github:
            print("\n🔑 現在設定されているGitHub Secrets:")
            secrets_list = get_github_secrets_list()
            if secrets_list:
                for secret in secrets_list:
                    print(f"  - {secret}")
            else:
                print("  (一覧を取得できませんでした)")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        
        # GitHub Actions環境の場合はSecrets一覧を表示
        if is_github:
            print("\n🔑 現在設定されているGitHub Secrets:")
            secrets_list = get_github_secrets_list()
            if secrets_list:
                for secret in secrets_list:
                    print(f"  - {secret}")
            else:
                print("  (一覧を取得できませんでした)")
            
            print("\n💡 必要なSecrets:")
            print("  - TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
            print("\n※ テスト環境ではTST_プレフィックス付きの環境変数が必要です")
        
        sys.exit(1)
        
    finally:
        # 一時ファイルの削除
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            print("\n🧹 一時ファイルを削除しました")
    
    return 0


if __name__ == "__main__":
    sys.exit(test_google_sheets_connection())