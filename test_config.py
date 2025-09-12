#!/usr/bin/env python3
"""config.pyのテストスクリプト

環境変数の設定と取得をテストします。
使い方: python test_config.py [環境番号]
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from config import EnvConfig, Environment


def main():
    """設定のテスト"""
    
    # コマンドライン引数から環境を取得
    env_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("=" * 70)
    print("Config.py 動作確認")
    print("=" * 70)
    
    # 環境を取得
    try:
        env = EnvConfig.get_environment_from_arg(env_arg)
        env_name = EnvConfig.get_environment_name(env)
        print(f"\n環境: {env_name} (値: {env})")
    except ValueError as e:
        print(f"\n❌ エラー: {e}")
        sys.exit(1)
    
    print("\n設定取得テスト:")
    print("-" * 40)
    
    # Discord設定
    print("\n📱 Discord設定:")
    try:
        discord_config = EnvConfig.get_discord_config(env)
        print(f"  ✅ トークン: {discord_config['token'][:20]}...")
        print(f"  ✅ チャンネルID: {discord_config['channel_ids']}")
    except ValueError as e:
        print(f"  ❌ エラー: {e}")
    
    # Google Sheets設定
    print("\n📊 Google Sheets設定:")
    try:
        sheets_config = EnvConfig.get_google_sheets_config(env)
        print(f"  ✅ シート名: {sheets_config['sheet_name']}")
        print(f"  ✅ JSONファイル: {sheets_config['service_account_json']}")
        if sheets_config['service_account_json_base64']:
            print(f"  ✅ Base64: 設定済み")
        else:
            print(f"  ⚠️ Base64: 未設定")
    except ValueError as e:
        print(f"  ❌ エラー: {e}")
    
    # Slack設定（オプション）
    print("\n💬 Slack設定:")
    slack_config = EnvConfig.get_slack_config(env)
    if slack_config['token']:
        print(f"  ✅ トークン: {slack_config['token'][:20]}...")
        print(f"  ✅ チャンネルID: {slack_config['channel_id']}")
    else:
        print("  ⚠️ 未設定（オプション）")
    
    print("\n" + "=" * 70)
    print("テスト完了")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())