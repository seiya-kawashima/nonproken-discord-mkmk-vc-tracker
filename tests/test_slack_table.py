#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Slack表形式メッセージのテストプログラム
"""

import sys
import os
from datetime import date
from unittest.mock import MagicMock, patch

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# モジュールをインポート
from slack_notifier_attendance import DailyAggregator
from config import Environment

def test_slack_table_format():
    """表形式メッセージのテスト"""

    # テストデータを準備
    user_data = {
        '123456789': {
            'user_name': '川島誠也',
            'display_name': '川島誠也',
            'vc_channels': '☁もくもく広場',
            'login_count': 1,
            'records': []
        },
        '987654321': {
            'user_name': 'ichihuku',
            'display_name': 'ichihuku',
            'vc_channels': '☁もくもく広場',
            'login_count': 1,
            'records': []
        },
        '555555555': {
            'user_name': 'テストユーザー',
            'display_name': 'テストユーザー',
            'vc_channels': '☁もくもく広場',
            'login_count': 1,
            'records': []
        }
    }

    # 統計データ
    stats_dict = {
        '123456789': {
            'user_name': '川島誠也',
            'last_login_date': '2025/09/22',
            'consecutive_days': 5,  # 5日連続
            'total_days': 10,  # 合計10日
            'last_updated': '2025/09/22 09:00:00'
        },
        '987654321': {
            'user_name': 'ichihuku',
            'last_login_date': '2025/09/22',
            'consecutive_days': 3,  # 3日連続
            'total_days': 15,  # 合計15日
            'last_updated': '2025/09/22 09:00:00'
        },
        '555555555': {
            'user_name': 'テストユーザー',
            'last_login_date': '2025/09/22',
            'consecutive_days': 1,  # 今日から
            'total_days': 1,  # 初日
            'last_updated': '2025/09/22 09:00:00'
        }
    }

    # DailyAggregatorのインスタンスを作成（ドライランモード）
    aggregator = DailyAggregator(
        target_date=date(2025, 9, 22),
        env=Environment.DEV,
        output_pattern='discord',  # Discord名で表示（メンション無し）
        dry_run=True
    )

    # Slackクライアントをモック化
    aggregator.slack_client = None  # ドライランなのでNone

    # post_to_slackメソッドを呼び出し
    result = aggregator.post_to_slack(user_data, stats_dict)

    # 結果を表示
    print("="*60)
    print("生成されたメッセージ（テキスト形式）:")
    print("="*60)
    print(result)
    print("="*60)

    # Block Kit形式もテスト（Slackクライアントがある場合の想定）
    aggregator.output_pattern = 'slack'
    aggregator.slack_client = MagicMock()
    aggregator.slack_channel = 'C09FJLRBMQS'

    # ユーザーマッピングを設定（テスト用）
    aggregator.user_mapping = {
        '123456789': 'U12345',
        '987654321': 'U67890'
        # 555555555 はマッピングなし
    }

    # モックを使って呼び出し
    with patch.object(aggregator.slack_client, 'chat_postMessage') as mock_post:
        mock_post.return_value = {'ok': True, 'ts': '1234567890.123456'}
        result2 = aggregator.post_to_slack(user_data, stats_dict)

        # Block Kitの呼び出しを確認
        if mock_post.called:
            call_args = mock_post.call_args
            blocks = call_args.kwargs.get('blocks', [])

            print("\n生成されたBlock Kit形式:")
            print("="*60)
            import json
            print(json.dumps(blocks, ensure_ascii=False, indent=2))
            print("="*60)

    print("\nテスト完了!")

if __name__ == '__main__':
    test_slack_table_format()