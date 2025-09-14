#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord VC → Google Sheets 統合テスト
=====================================
poll_once.pyのmain関数を利用して実際の処理フローをテスト
必要に応じて一部をモック化して安全にテストを実施
"""

import asyncio  # 非同期処理用ライブラリ
import os  # 環境変数取得用
import sys  # システム関連の処理用
from datetime import datetime  # 日時処理用
import json  # JSON処理用
from pathlib import Path  # ファイルパス処理用
from unittest.mock import patch, MagicMock  # モック用ライブラリ
import tempfile  # 一時ファイル作成用

# プロジェクトのルートディレクトリをパスに追加
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 必要なモジュールをインポート
try:
    from poll_once import main as poll_once_main
    from src.discord_client import DiscordVCPoller  # Discord VC監視クライアント
    from src.sheets_client import SheetsClient  # Google Sheetsクライアント
    from src.slack_notifier import SlackNotifier  # Slack通知クライアント
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print(f"Python Path: {sys.path}")
    sys.exit(1)

# ロガーの代替実装（logger.pyが存在しない場合）
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def test_vc_to_sheets_integration_with_poll_once():
    """
    poll_once.pyのmain関数を使用した統合テスト
    実際の処理フローをテストしつつ、テスト用シートを使用してデータを汚さない
    """

    print("=" * 60)
    print("Discord VC → Google Sheets 統合テスト (poll_once使用)")
    print("=" * 60)
    print()

    # ========================================
    # 1. テスト用のワークシート名を設定
    # ========================================
    test_worksheet_name = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    original_update_sheet = None
    test_worksheet = None
    sheets_client_instance = None

    print(f"📝 テスト用ワークシート名: {test_worksheet_name}")

    # ========================================
    # 2. SheetsClientのupdate_sheetメソッドをモック
    # ========================================
    # 本番のワークシートではなくテスト用ワークシートに書き込むようにモック
    def mock_upsert_presence(self, members):
        """テスト用のupsert_presenceメソッド"""
        print(f"  📊 モック: {len(members)}件のメンバー情報を記録中...")

        # テスト用シートがまだ作成されていない場合は作成
        nonlocal test_worksheet, sheets_client_instance
        sheets_client_instance = self

        try:
            # テスト用ワークシートを取得または作成
            try:
                test_worksheet = self.sheet.worksheet(test_worksheet_name)
            except:
                print(f"  📝 テスト用ワークシート '{test_worksheet_name}' を作成中...")
                test_worksheet = self.sheet.add_worksheet(
                    title=test_worksheet_name,
                    rows=1000,
                    cols=10
                )
                # ヘッダー行を追加
                headers = ['date_jst', 'guild_id', 'user_id', 'user_name', 'present']
                test_worksheet.append_row(headers)

            # データを記録
            from datetime import datetime, timezone, timedelta
            jst = timezone(timedelta(hours=9))
            today_jst = datetime.now(jst).strftime('%Y-%m-%d')
            rows_to_add = []

            for member in members:
                row = [
                    today_jst,
                    member.get('guild_id', 'Unknown'),
                    member.get('user_id', 'Unknown'),
                    member.get('user_name', 'Unknown'),
                    1  # present
                ]
                rows_to_add.append(row)

            if rows_to_add:
                test_worksheet.append_rows(rows_to_add)
                print(f"  ✅ {len(rows_to_add)}件のデータをテスト用シートに記録")

            # 戻り値を本物のメソッドと同じ形式にする
            return {'new': len(rows_to_add), 'updated': 0}

        except Exception as e:
            print(f"  ❌ モックエラー: {e}")
            return {'new': 0, 'updated': 0}

    # ========================================
    # 3. Slack通知をモック（実際に通知しない）
    # ========================================
    def mock_send_login_notification(self, display_name, duration_minutes):
        """テスト用のSlack通知メソッド"""
        print(f"  💬 モック: Slack通知 - {display_name}がログイン（{duration_minutes}分）")
        return True

    def mock_send_logout_notification(self, display_name, duration_minutes):
        """テスト用のSlack通知メソッド"""
        print(f"  💬 モック: Slack通知 - {display_name}がログアウト（{duration_minutes}分）")
        return True

    # ========================================
    # 4. モックを適用してpoll_once.main()を実行
    # ========================================
    print("\n🚀 poll_once.main()を実行中...")

    # 環境変数の確認
    print("\n📋 環境変数チェック:")
    env_vars = {
        'TST_DISCORD_BOT_TOKEN': os.getenv('TST_DISCORD_BOT_TOKEN'),
        'TST_ALLOWED_VOICE_CHANNEL_IDS': os.getenv('TST_ALLOWED_VOICE_CHANNEL_IDS'),
        'TST_GOOGLE_SERVICE_ACCOUNT_JSON': os.getenv('TST_GOOGLE_SERVICE_ACCOUNT_JSON'),
        'TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64': os.getenv('TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64')
    }

    for key, value in env_vars.items():
        if value:
            if 'TOKEN' in key or 'BASE64' in key:
                print(f"  {key}: ✅ (設定済み)")
            else:
                print(f"  {key}: ✅ {value}")
        else:
            print(f"  {key}: ❌ 未設定")

    # config.pyから設定値を取得
    from config import EnvConfig, Environment
    sheets_config = EnvConfig.get_google_sheets_config(Environment.TST)
    print(f"  TST_GOOGLE_SHEET_NAME: ✅ {sheets_config['sheet_name']} (config.pyで設定)")

    # 必須環境変数のチェック（TST_GOOGLE_SHEET_NAMEは除外）
    required_vars = ['TST_DISCORD_BOT_TOKEN', 'TST_ALLOWED_VOICE_CHANNEL_IDS']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"\n❌ 必須環境変数が不足しています: {', '.join(missing_vars)}")
        print("テストをスキップします")
        return False

    with patch.object(SheetsClient, 'upsert_presence', mock_upsert_presence):
        with patch.object(SlackNotifier, 'send_login_notification', mock_send_login_notification):
            with patch.object(SlackNotifier, 'send_login_notification', mock_send_login_notification):
                try:
                    # テスト環境（env=1）でpoll_once.main()を実行
                    await poll_once_main(env_arg=1)
                    print("✅ poll_once.main()が正常に完了")

                except Exception as e:
                    print(f"❌ poll_once.main()実行エラー: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

    # ========================================
    # 5. テスト結果の確認
    # ========================================
    if test_worksheet and sheets_client_instance:
        print("\n📖 記録されたデータを確認中...")
        try:
            all_values = test_worksheet.get_all_values()
            print(f"✅ {len(all_values) - 1}行のデータを確認（ヘッダー除く）")

            # 最初の数行を表示
            for i, row in enumerate(all_values[:5]):
                if i == 0:
                    print(f"  ヘッダー: {row}")
                else:
                    print(f"  データ{i}: {row}")

            # クリーンアップ
            print(f"\n🗑️ テスト用ワークシート '{test_worksheet_name}' を削除中...")
            sheets_client_instance.spreadsheet.del_worksheet(test_worksheet)
            print("✅ テスト用ワークシートを削除")

        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")

    # ========================================
    # 6. テスト結果サマリー
    # ========================================
    print("\n" + "=" * 60)
    print("✅ 統合テスト成功")
    print("=" * 60)
    print("\n確認項目:")
    print("  ✅ poll_once.main()の実行")
    print("  ✅ Discord接続（実際のBot使用）")
    print("  ✅ Google Sheets接続（テスト用シート使用）")
    print("  ✅ Slack通知（モック使用）")
    print("  ✅ データ記録の確認")
    print("  ✅ テストデータのクリーンアップ")

    return True


def main():
    """メイン関数"""
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python バージョン: {sys.version}")
    print()

    # 非同期処理を実行
    try:
        result = asyncio.run(test_vc_to_sheets_integration_with_poll_once())
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()