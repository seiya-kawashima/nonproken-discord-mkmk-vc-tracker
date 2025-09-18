"""
テスト用のモックデータ定義
"""
from datetime import datetime, timedelta  # 日時操作用ライブラリ
from typing import List, Dict, Any  # 型ヒント用


class MockInputData:
    """テスト入力用のモックデータクラス（固定値）"""

    # Discord VCメンバーのモックデータ
    @staticmethod
    def get_mock_members() -> List[Dict[str, Any]]:
        """Discord VCの擬似メンバー情報を返す"""
        return [
            {
                "id": "123456789",  # ユーザーID
                "name": "田中太郎",  # ユーザー名
                "display_name": "田中",  # 表示名
                "joined_at": "2025-01-18 10:00:00",  # VC参加時刻
                "status": "online"  # オンラインステータス
            },
            {
                "id": "987654321",
                "name": "佐藤花子",
                "display_name": "佐藤",
                "joined_at": "2025-01-18 10:05:00",
                "status": "online"
            },
            {
                "id": "456789123",
                "name": "鈴木一郎",
                "display_name": "鈴木",
                "joined_at": "2025-01-18 10:10:00",
                "status": "online"
            }
        ]

    # CSVテンプレートデータ（既存の出席記録）
    @staticmethod
    def get_mock_template_csv() -> str:
        """既存のCSVテンプレートデータを返す"""
        return """日付,田中,佐藤,鈴木
2025-01-13,0,0,0
2025-01-14,1,0,1
2025-01-15,1,0,1
2025-01-16,1,1,0
2025-01-17,0,1,1"""

    # 新規メンバーが追加された後の期待されるCSVデータ
    @staticmethod
    def get_expected_csv_after_append() -> str:
        """メンバー追加後の期待されるCSVデータ"""
        return """日付,田中,佐藤,鈴木
2025-01-13,0,0,0
2025-01-14,1,0,1
2025-01-15,1,0,1
2025-01-16,1,1,0
2025-01-17,0,1,1
2025-01-18,1,1,1"""

    # 本日（2025-01-18）のメンバー出席データ
    @staticmethod
    def get_today_members() -> List[str]:
        """本日のVC参加メンバーリスト"""
        return ["田中", "佐藤", "鈴木"]

    # 期待されるSlack通知メッセージ
    @staticmethod
    def get_expected_slack_message() -> str:
        """期待されるSlack通知メッセージ"""
        # 土日祝を除いた連続出席日数の計算
        # 1/13(月):休み, 1/14(火):田中○鈴木○, 1/15(水):田中○鈴木○,
        # 1/16(木):田中○佐藤○, 1/17(金):佐藤○鈴木○, 1/18(土):全員○
        return """📊 【2025-01-18 もくもく会 出席統計】 📊

🎊 本日の出席者: 3名

👤 田中
  ├ 累計出席: 4日
  └ 連続出席: 3日 🔥🔥🔥

👤 佐藤
  ├ 累計出席: 3日
  └ 連続出席: 2日 🔥🔥

👤 鈴木
  ├ 累計出席: 4日
  └ 連続出席: 1日 🔥

────────────────────
✨ 素晴らしい継続です！みんなで頑張りましょう！"""

    # 集計用のテストデータ（1週間分）
    @staticmethod
    def get_aggregation_test_csv() -> str:
        """集計テスト用のCSVデータ（1週間分）"""
        return """日付,田中,佐藤,鈴木,山田
2025-01-13,1,0,1,1
2025-01-14,1,0,1,0
2025-01-15,1,1,0,1
2025-01-16,1,1,0,1
2025-01-17,0,1,1,0
2025-01-18,1,1,1,0"""

    # ボイスチャンネルIDは環境変数から取得するため、モックデータには含めない
    # channel_idは環境変数 DISCORD_VOICE_CHANNEL_IDS から実際に取得される

    # Discord Botトークンのモック（テスト用）
    @staticmethod
    def get_mock_bot_token() -> str:
        """テスト用のBotトークン（実際には使用されない）"""
        return "MOCK_BOT_TOKEN_FOR_TESTING_ONLY"

    # Slackの統計データ辞書
    @staticmethod
    def get_stats_dict() -> Dict[str, Dict[str, Any]]:
        """統計情報の辞書形式データ"""
        return {
            "田中": {
                "total_days": 4,  # 累計出席日数
                "consecutive_days": 3,  # 連続出席日数（土日祝除く）
                "last_attended": "2025-01-18"  # 最終出席日
            },
            "佐藤": {
                "total_days": 3,
                "consecutive_days": 2,
                "last_attended": "2025-01-18"
            },
            "鈴木": {
                "total_days": 4,
                "consecutive_days": 1,
                "last_attended": "2025-01-18"
            }
        }

    # ユーザーデータ（出席履歴）
    @staticmethod
    def get_user_data() -> Dict[str, Dict[str, Any]]:
        """ユーザー別の出席履歴データ"""
        return {
            "田中": {
                "dates": ["2025-01-14", "2025-01-15", "2025-01-16", "2025-01-18"],
                "total": 4,
                "consecutive": 3
            },
            "佐藤": {
                "dates": ["2025-01-15", "2025-01-16", "2025-01-17", "2025-01-18"],
                "total": 3,
                "consecutive": 2
            },
            "鈴木": {
                "dates": ["2025-01-13", "2025-01-14", "2025-01-17", "2025-01-18"],
                "total": 4,
                "consecutive": 1
            }
        }