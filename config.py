"""環境変数の設定を一元管理するモジュール

このモジュールで全ての環境変数名を定義し、
プロジェクト全体で一貫した環境変数の使用を保証します。
"""

import os
from enum import IntEnum
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Environment(IntEnum):
    """環境の定義
    
    0: PRODUCTION - 本番環境
    1: TEST - テスト環境
    2: DEVELOPMENT - 開発環境
    """
    PRODUCTION = 0  # 本番環境（デフォルト）
    TEST = 1        # テスト環境
    DEVELOPMENT = 2  # 開発環境
    
    @classmethod
    def from_value(cls, value):
        """数値から環境を取得"""
        if value is None:
            return cls.PRODUCTION  # デフォルトは本番
        return cls(value)


class EnvConfig:
    """環境変数の設定を管理するクラス"""
    
    # Discord関連の環境変数名
    DISCORD_BOT_TOKEN = 'DISCORD_BOT_TOKEN'
    TEST_DISCORD_BOT_TOKEN = 'TEST_DISCORD_BOT_TOKEN'
    
    ALLOWED_VOICE_CHANNEL_IDS = 'ALLOWED_VOICE_CHANNEL_IDS'
    TEST_ALLOWED_VOICE_CHANNEL_IDS = 'TEST_ALLOWED_VOICE_CHANNEL_IDS'
    
    # Google Sheets関連の環境変数名
    GOOGLE_SHEET_NAME = 'GOOGLE_SHEET_NAME'
    TEST_GOOGLE_SHEET_NAME = 'TEST_GOOGLE_SHEET_NAME'
    
    GOOGLE_SERVICE_ACCOUNT_JSON = 'GOOGLE_SERVICE_ACCOUNT_JSON'
    TEST_GOOGLE_SERVICE_ACCOUNT_JSON = 'TEST_GOOGLE_SERVICE_ACCOUNT_JSON'
    
    GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 = 'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64'
    TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 = 'TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64'
    
    # Slack関連の環境変数名
    SLACK_BOT_TOKEN = 'SLACK_BOT_TOKEN'
    TEST_SLACK_BOT_TOKEN = 'TEST_SLACK_BOT_TOKEN'
    
    SLACK_CHANNEL_ID = 'SLACK_CHANNEL_ID'
    TEST_SLACK_CHANNEL_ID = 'TEST_SLACK_CHANNEL_ID'
    
    # GitHub Actions環境の判定
    GITHUB_ACTIONS = 'GITHUB_ACTIONS'
    
    @classmethod
    def get(cls, key, default=None):
        """環境変数を取得"""
        return os.getenv(key, default)
    
    @classmethod
    def get_with_test_prefix(cls, base_key, default=None):
        """TEST_プレフィックス付きを優先的に取得
        
        Args:
            base_key: プレフィックスなしの環境変数名
            default: デフォルト値
            
        Returns:
            環境変数の値（TEST_プレフィックス付きを優先）
        """
        test_key = f'TEST_{base_key}'
        return os.getenv(test_key) or os.getenv(base_key, default)
    
    @classmethod
    def is_github_actions(cls):
        """GitHub Actions環境かどうかを判定"""
        return cls.get(cls.GITHUB_ACTIONS) == 'true'
    
    @classmethod
    def is_test_environment(cls):
        """テスト環境かどうかを判定（TEST_プレフィックス付き環境変数の存在で判定）"""
        test_vars = [
            cls.TEST_GOOGLE_SHEET_NAME,
            cls.TEST_DISCORD_BOT_TOKEN,
            cls.TEST_GOOGLE_SERVICE_ACCOUNT_JSON,
            cls.TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
        ]
        return any(os.getenv(var) for var in test_vars)
    
    @classmethod
    def get_environment_name(cls):
        """現在の環境名を取得"""
        if cls.is_test_environment():
            return "テスト環境"
        elif cls.is_github_actions():
            return "本番環境"
        else:
            return "開発環境"
    
    @classmethod
    def get_discord_config(cls, env=Environment.PRODUCTION):
        """Discord関連の設定を取得
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
        
        Returns:
            dict: Discord設定の辞書
        """
        if env == Environment.TEST:
            return {
                'token': cls.get(cls.TEST_DISCORD_BOT_TOKEN),
                'channel_ids': cls.get(cls.TEST_ALLOWED_VOICE_CHANNEL_IDS, '').split(',')
            }
        else:
            # 本番と開発は同じ設定を使用
            return {
                'token': cls.get(cls.DISCORD_BOT_TOKEN),
                'channel_ids': cls.get(cls.ALLOWED_VOICE_CHANNEL_IDS, '').split(',')
            }
    
    @classmethod
    def get_google_sheets_config(cls, env=Environment.PRODUCTION):
        """Google Sheets関連の設定を取得
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
        
        Returns:
            dict: Google Sheets設定の辞書
        """
        if env == Environment.TEST:
            return {
                'sheet_name': cls.get(cls.TEST_GOOGLE_SHEET_NAME),
                'service_account_json': cls.get(cls.TEST_GOOGLE_SERVICE_ACCOUNT_JSON),
                'service_account_json_base64': cls.get(cls.TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64)
            }
        else:
            # 本番と開発は同じ設定を使用
            return {
                'sheet_name': cls.get(cls.GOOGLE_SHEET_NAME),
                'service_account_json': cls.get(cls.GOOGLE_SERVICE_ACCOUNT_JSON, 'service_account.json'),
                'service_account_json_base64': cls.get(cls.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64)
            }
    
    @classmethod
    def get_slack_config(cls, use_test=None):
        """Slack関連の設定を取得
        
        Args:
            use_test: Trueの場合はテスト環境、Falseの場合は本番/開発環境
                     Noneの場合は自動判定
        
        Returns:
            dict: Slack設定の辞書
        """
        if use_test is None:
            use_test = cls.is_test_environment()
        
        if use_test:
            return {
                'token': cls.get(cls.TEST_SLACK_BOT_TOKEN),
                'channel_id': cls.get(cls.TEST_SLACK_CHANNEL_ID)
            }
        else:
            return {
                'token': cls.get(cls.SLACK_BOT_TOKEN),
                'channel_id': cls.get(cls.SLACK_CHANNEL_ID)
            }
    
    @classmethod
    def get_all_configs(cls):
        """全環境の設定を取得（デバッグ用）"""
        return {
            '開発環境': {
                'discord': cls.get_discord_config(use_test=False),
                'google_sheets': cls.get_google_sheets_config(use_test=False),
                'slack': cls.get_slack_config(use_test=False)
            },
            'テスト環境': {
                'discord': cls.get_discord_config(use_test=True),
                'google_sheets': cls.get_google_sheets_config(use_test=True),
                'slack': cls.get_slack_config(use_test=True)
            }
        }


# エクスポート用のインスタンス
config = EnvConfig()