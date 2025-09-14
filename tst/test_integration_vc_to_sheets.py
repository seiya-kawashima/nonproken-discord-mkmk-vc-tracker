#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord VC → Google Sheets 統合テスト
=====================================
実際のDiscord VCメンバーを取得してGoogle Sheetsに記録するテスト
本番環境に近い形でエンドツーエンドのテストを実施
"""

import asyncio  # 非同期処理用ライブラリ
import os  # 環境変数取得用
import sys  # システム関連の処理用
from datetime import datetime  # 日時処理用
import json  # JSON処理用
from pathlib import Path  # ファイルパス処理用

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.discord_client import DiscordVCPoller  # Discord VC監視クライアント
from src.sheets_client import SheetsClient  # Google Sheetsクライアント
from src.logger import VCTrackerLogger  # ロガー


async def test_vc_to_sheets_integration():
    """Discord VCからGoogle Sheetsへの統合テスト"""

    # ロガー初期化
    logger = VCTrackerLogger("IntegrationTest", log_level="1")  # デバッグモード

    print("=" * 60)
    print("Discord VC → Google Sheets 統合テスト")
    print("=" * 60)
    print()

    # ========================================
    # 1. 環境変数の確認
    # ========================================
    print("📋 環境変数チェック:")

    # テスト環境用の環境変数を優先的に使用
    discord_token = os.getenv('TST_DISCORD_BOT_TOKEN') or os.getenv('DISCORD_BOT_TOKEN')
    vc_channel_ids_str = os.getenv('TST_ALLOWED_VOICE_CHANNEL_IDS') or os.getenv('ALLOWED_VOICE_CHANNEL_IDS')
    sheet_name = os.getenv('TST_GOOGLE_SHEET_NAME') or os.getenv('GOOGLE_SHEET_NAME')
    service_account_json = os.getenv('TST_GOOGLE_SERVICE_ACCOUNT_JSON') or os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

    # 環境変数の存在確認
    env_check = {
        'DISCORD_BOT_TOKEN': '✅' if discord_token else '❌',
        'ALLOWED_VOICE_CHANNEL_IDS': '✅' if vc_channel_ids_str else '❌',
        'GOOGLE_SHEET_NAME': f'✅ {sheet_name}' if sheet_name else '❌',
        'GOOGLE_SERVICE_ACCOUNT_JSON': '✅' if service_account_json else '❌'
    }

    for key, status in env_check.items():
        print(f"  {key}: {status}")

    # 必須環境変数が不足している場合はエラー
    if not all([discord_token, vc_channel_ids_str, sheet_name, service_account_json]):
        print("\n❌ 必須の環境変数が設定されていません")
        return False

    # VCチャンネルIDをリストに変換
    vc_channel_ids = [id.strip() for id in vc_channel_ids_str.split(',') if id.strip()]
    print(f"\n📍 監視対象VCチャンネルID: {vc_channel_ids}")

    # ========================================
    # 2. Discord VCメンバー取得
    # ========================================
    print("\n🤖 Discord VCに接続中...")

    try:
        # Discord VCポーラーを初期化
        discord_client = DiscordVCPoller(discord_token, vc_channel_ids)

        # VCメンバーを取得
        vc_members = await discord_client.get_vc_members()

        print(f"✅ Discord接続成功")
        print(f"📊 現在のVCメンバー数: {len(vc_members)}人")

        if vc_members:
            print("\n👥 VCメンバー一覧:")
            for channel_id, members in vc_members.items():
                print(f"  チャンネル {channel_id}:")
                for member in members:
                    print(f"    - {member['display_name']} (ID: {member['id']})")
        else:
            print("  （現在VCに誰もいません）")

    except Exception as e:
        print(f"❌ Discord接続エラー: {e}")
        logger.error(f"Discord接続エラー: {e}")
        return False

    # ========================================
    # 3. Google Sheetsへの記録
    # ========================================
    print(f"\n📊 Google Sheets '{sheet_name}' に接続中...")

    try:
        # Google Sheetsクライアントを初期化
        sheets_client = SheetsClient(service_account_json, sheet_name)
        sheets_client.connect()
        print("✅ Google Sheets接続成功")

        # テスト用のシート名（本番データを汚さないため）
        test_sheet_name = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # テスト用シートを作成
        print(f"\n📝 テスト用シート '{test_sheet_name}' を作成中...")
        sheets_client.spreadsheet.add_worksheet(title=test_sheet_name, rows=1000, cols=10)
        test_worksheet = sheets_client.spreadsheet.worksheet(test_sheet_name)

        # ヘッダー行を追加
        headers = ['Timestamp', 'Channel_ID', 'User_ID', 'Display_Name', 'Status']
        test_worksheet.append_row(headers)
        print("✅ ヘッダー行を追加")

        # VCメンバーデータを記録
        if vc_members:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows_to_add = []

            for channel_id, members in vc_members.items():
                for member in members:
                    row = [
                        timestamp,
                        channel_id,
                        member['id'],
                        member['display_name'],
                        'Active'
                    ]
                    rows_to_add.append(row)

            # バッチで追加（API制限対策）
            if rows_to_add:
                test_worksheet.append_rows(rows_to_add)
                print(f"✅ {len(rows_to_add)}件のメンバー情報を記録")
        else:
            # メンバーがいない場合も記録
            test_worksheet.append_row([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'N/A',
                'N/A',
                '(No members in VC)',
                'Empty'
            ])
            print("✅ VCが空であることを記録")

        # 記録したデータを読み返して確認
        print("\n📖 記録されたデータを確認中...")
        all_values = test_worksheet.get_all_values()
        print(f"✅ {len(all_values) - 1}行のデータを確認（ヘッダー除く）")

        # 最初の数行を表示
        for i, row in enumerate(all_values[:5]):
            if i == 0:
                print(f"  ヘッダー: {row}")
            else:
                print(f"  データ{i}: {row}")

        # テスト用シートの削除（オプション）
        print(f"\n🗑️ テスト用シート '{test_sheet_name}' を削除中...")
        sheets_client.spreadsheet.del_worksheet(test_worksheet)
        print("✅ テスト用シートを削除")

    except Exception as e:
        print(f"❌ Google Sheetsエラー: {e}")
        logger.error(f"Google Sheetsエラー: {e}")
        return False

    # ========================================
    # 4. テスト結果サマリー
    # ========================================
    print("\n" + "=" * 60)
    print("✅ 統合テスト成功")
    print("=" * 60)
    print("\n確認項目:")
    print("  ✅ Discord Bot接続")
    print("  ✅ VCメンバー取得")
    print("  ✅ Google Sheets接続")
    print("  ✅ データ記録")
    print("  ✅ データ読み取り確認")
    print("  ✅ テストデータクリーンアップ")

    return True


def main():
    """メイン関数"""
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python バージョン: {sys.version}")
    print()

    # 非同期処理を実行
    try:
        result = asyncio.run(test_vc_to_sheets_integration())
        if result:
            print("\n✅ すべてのテストが成功しました")
            sys.exit(0)
        else:
            print("\n❌ テストが失敗しました")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()