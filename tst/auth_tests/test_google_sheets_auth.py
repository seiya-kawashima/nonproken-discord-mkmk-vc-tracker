#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Sheets認証テスト（GitHub Actions用）

このスクリプトはGitHub ActionsでGoogle Sheets APIの認証をテストします。
各環境（本番・テスト・開発）の設定を確認し、認証が成功するかを検証します。

実行方法:
    python test_google_sheets_auth.py [--env {0|1|2}]

    --env オプション:
        0: 本番環境 (PRD)
        1: テスト環境 (TST)
        2: 開発環境 (DEV) - デフォルト

必要な環境変数:
    - *_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_[0_PRD|1_TST|2_DEV]: Base64エンコードされた認証情報
    または
    - *_GOOGLE_SERVICE_ACCOUNT_JSON_[0_PRD|1_TST|2_DEV]: 認証ファイルのパス
"""

import gspread  # Google Sheets操作ライブラリ
from google.oauth2.service_account import Credentials  # 認証用
import os  # 環境変数取得用
import sys  # パス追加用
from datetime import datetime  # 現在時刻取得用
import base64  # Base64デコード用
import json  # JSON処理用
import tempfile  # 一時ファイル作成用
import argparse  # コマンドライン引数処理用

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import get_config, Environment  # 環境変数設定モジュール

print("=" * 70)
print("Google Sheets 接続テスト")
print("=" * 70)
print(f"\n実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)


def test_google_sheets_connection(env: Environment = Environment.DEV):
    """
    Google Sheets APIへの接続をテスト

    Args:
        env: テスト対象の環境

    Returns:
        bool: テスト成功の場合True
    """
    env_name = {
        Environment.PRD: "本番環境 (PRD)",
        Environment.TST: "テスト環境 (TST)",
        Environment.DEV: "開発環境 (DEV)"
    }[env]

    print(f"\n🔍 {env_name}の接続テスト")
    print("-" * 50)

    try:
        # 環境設定を取得
        config = get_config(env)

        # 認証情報の取得
        service_account_json = config.get('google_drive_service_account_json')
        service_account_json_base64 = config.get('google_drive_service_account_json_base64')

        # 認証ファイルの準備
        auth_file = None
        temp_file = None

        if service_account_json_base64:
            # Base64からデコード
            print("📦 Base64認証情報をデコード中...")
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
                return False
        elif service_account_json and os.path.exists(service_account_json):
            # ファイルパスを使用
            auth_file = service_account_json
            print(f"📄 認証ファイル使用: {auth_file}")
        else:
            print("❌ 認証情報が見つかりません")
            print("  以下のいずれかを設定してください:")
            suffix = ['0_PRD', '1_TST', '2_DEV'][env]
            print(f"  - GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_{suffix}")
            print(f"  - GOOGLE_SERVICE_ACCOUNT_JSON_{suffix}")
            return False

        # Google Sheets APIに接続
        print("\n🔐 Google Sheets APIに接続中...")

        # 認証スコープの設定
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # 認証情報を作成
        creds = Credentials.from_service_account_file(auth_file, scopes=SCOPES)

        # gspreadクライアントを作成
        client = gspread.authorize(creds)

        print("  ✅ 認証成功")

        # テスト用のスプレッドシートを作成
        print("\n📊 テストスプレッドシート作成中...")
        test_sheet_name = f"テスト_{env_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            sheet = client.create(test_sheet_name)
            print(f"  ✅ スプレッドシート作成成功: {test_sheet_name}")

            # ワークシートにテストデータを書き込み
            worksheet = sheet.get_worksheet(0)
            worksheet.update('A1', [
                ['テスト実行日時', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['環境', env_name],
                ['ステータス', '成功']
            ])
            print("  ✅ データ書き込み成功")

            # スプレッドシートを削除（クリーンアップ）
            print("\n🗑️ テストスプレッドシート削除中...")
            client.del_spreadsheet(sheet.id)
            print("  ✅ 削除成功")

        except Exception as e:
            print(f"  ❌ スプレッドシート操作失敗: {e}")
            return False

        print(f"\n✅ {env_name}の接続テスト成功")
        return True

    except Exception as e:
        print(f"\n❌ {env_name}の接続テスト失敗")
        print(f"  エラー: {e}")
        return False

    finally:
        # 一時ファイルのクリーンアップ
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
            print("  🧹 一時ファイル削除完了")


def main():
    """メイン処理"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description='Google Sheets認証テスト'
    )
    parser.add_argument(
        '--env',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='テスト環境 (0=本番, 1=テスト, 2=開発)'
    )
    args = parser.parse_args()

    # 環境を設定
    env = Environment(args.env)

    # GitHub Actions環境かどうか
    is_github = os.getenv('GITHUB_ACTIONS') == 'true'

    if is_github:
        print("\n🤖 GitHub Actions環境で実行中")
    else:
        print("\n💻 ローカル環境で実行中")

    # 環境変数の確認
    print("\n📋 環境変数の確認")
    print("-" * 50)

    config = get_config(env)
    suffix = ['0_PRD', '1_TST', '2_DEV'][env]

    # 必要な環境変数をチェック
    env_vars = {
        f'GOOGLE_SERVICE_ACCOUNT_JSON_{suffix}': config.get('google_drive_service_account_json'),
        f'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_{suffix}': config.get('google_drive_service_account_json_base64'),
        f'GOOGLE_SHARED_DRIVE_ID_{suffix}': config.get('google_drive_shared_drive_id'),
    }

    for key, value in env_vars.items():
        if value:
            if 'BASE64' in key:
                display_value = f"{value[:20]}... (Base64)" if len(value) > 20 else value
            else:
                display_value = value
            print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ⚠️ {key}: 未設定")

    # 接続テストを実行
    print("\n" + "=" * 70)
    success = test_google_sheets_connection(env)
    print("=" * 70)

    # 結果サマリー
    print("\n📊 テスト結果サマリー")
    print("-" * 50)
    if success:
        print("✅ すべてのテストが成功しました")
        sys.exit(0)
    else:
        print("❌ テストに失敗しました")
        if is_github:
            print("\n💡 GitHub Secretsの設定を確認してください")
        sys.exit(1)


if __name__ == "__main__":
    main()