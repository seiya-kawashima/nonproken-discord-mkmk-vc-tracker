"""Slack通知クライアント - ログイン通知と節目のお祝い"""  # モジュールの説明

import logging  # ログ出力用
from typing import Optional, Dict, Any  # 型ヒント用
from slack_sdk import WebClient  # Slack Web API用
from slack_sdk.errors import SlackApiError  # Slackエラー用

# ロガーの設定
logger = logging.getLogger(__name__)  # このモジュール用のロガー


class SlackNotifier:
    """Slackへの通知を管理するクラス"""  # クラスの説明

    def __init__(self, bot_token: str, channel_id: str):
        """初期化処理

        Args:
            bot_token: Slack Botトークン
            channel_id: 通知先チャンネルID
        """  # 初期化処理の説明
        self.bot_token = bot_token  # Botトークンを保存
        self.channel_id = channel_id  # チャンネルIDを保存
        self.client = WebClient(token=bot_token)  # Slackクライアントを作成

    def send_login_notification(self, user_name: str, total_days: int) -> bool:
        """ログイン通知を送信

        Args:
            user_name: ユーザー名
            total_days: 通算ログイン日数

        Returns:
            送信成功の可否
        """  # メソッドの説明
        try:
            # メッセージを作成
            if total_days % 100 == 0:  # 100日ごとの節目の場合
                message = f"🎉 {user_name} さんがログインしました！（通算 {total_days} 日目！おめでとう！）"  # お祝いメッセージ
            else:  # 通常の場合
                message = f"🎤 {user_name} さんがログインしました！（通算 {total_days} 日目）"  # 通常メッセージ

            # Slackに送信
            response = self.client.chat_postMessage(  # メッセージ送信API
                channel=self.channel_id,  # 送信先チャンネル
                text=message  # メッセージ内容
            )
            
            if response["ok"]:  # 送信成功の場合
                logger.info(f"Slack notification sent: {message}")  # 成功をログ出力
                return True  # 成功を返す
            else:  # 送信失敗の場合
                logger.error(f"Failed to send Slack notification: {response}")  # 失敗をログ出力
                return False  # 失敗を返す
                
        except SlackApiError as e:  # Slack APIエラーの場合
            logger.error(f"Slack API error: {e.response['error']}")  # エラーをログ出力
            return False  # 失敗を返す
        except Exception as e:  # その他のエラーの場合
            logger.error(f"Unexpected error sending Slack notification: {e}")  # エラーをログ出力
            return False  # 失敗を返す

    def send_daily_summary(self, members_count: int, members_list: list) -> bool:
        """日次サマリーを送信

        Args:
            members_count: ログインメンバー数
            members_list: メンバー名のリスト

        Returns:
            送信成功の可否
        """  # メソッドの説明
        try:
            # メッセージを作成
            if members_count == 0:  # メンバーがいない場合
                message = "📊 本日のVCログイン: なし"  # メンバーなしメッセージ
            else:  # メンバーがいる場合
                members_str = ", ".join(members_list[:10])  # 最初の10名を表示
                if members_count > 10:  # 10名を超える場合
                    members_str += f" 他{members_count - 10}名"  # 残りの人数を表示
                message = f"📊 本日のVCログイン: {members_count}名\n{members_str}"  # サマリーメッセージ

            # Slackに送信
            response = self.client.chat_postMessage(  # メッセージ送信API
                channel=self.channel_id,  # 送信先チャンネル
                text=message  # メッセージ内容
            )
            
            if response["ok"]:  # 送信成功の場合
                logger.info(f"Daily summary sent: {members_count} members")  # 成功をログ出力
                return True  # 成功を返す
            else:  # 送信失敗の場合
                logger.error(f"Failed to send daily summary: {response}")  # 失敗をログ出力
                return False  # 失敗を返す
                
        except SlackApiError as e:  # Slack APIエラーの場合
            logger.error(f"Slack API error: {e.response['error']}")  # エラーをログ出力
            return False  # 失敗を返す
        except Exception as e:  # その他のエラーの場合
            logger.error(f"Unexpected error sending daily summary: {e}")  # エラーをログ出力
            return False  # 失敗を返す

    def test_connection(self) -> bool:
        """Slack接続をテスト

        Returns:
            接続成功の可否
        """  # メソッドの説明
        try:
            # 認証テストを実行
            response = self.client.auth_test()  # 認証テストAPI
            
            if response["ok"]:  # テスト成功の場合
                logger.info(f"Slack connection test successful: {response['team']}")  # 成功をログ出力
                return True  # 成功を返す
            else:  # テスト失敗の場合
                logger.error(f"Slack connection test failed: {response}")  # 失敗をログ出力
                return False  # 失敗を返す
                
        except SlackApiError as e:  # Slack APIエラーの場合
            logger.error(f"Slack API error during test: {e.response['error']}")  # エラーをログ出力
            return False  # 失敗を返す
        except Exception as e:  # その他のエラーの場合
            logger.error(f"Unexpected error during Slack test: {e}")  # エラーをログ出力
            return False  # 失敗を返す