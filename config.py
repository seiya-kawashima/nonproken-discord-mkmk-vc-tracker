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
    ALLOWED_VOICE_CHANNEL_IDS = 'ALLOWED_VOICE_CHANNEL_IDS'
    
    # Google Sheets関連の環境変数名
    GOOGLE_SHEET_NAME = 'GOOGLE_SHEET_NAME'
    GOOGLE_SERVICE_ACCOUNT_JSON = 'GOOGLE_SERVICE_ACCOUNT_JSON'
    GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 = 'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64'
    
    # Slack関連の環境変数名
    SLACK_BOT_TOKEN = 'SLACK_BOT_TOKEN'
    SLACK_CHANNEL_ID = 'SLACK_CHANNEL_ID'
    
    # GitHub Actions環境の判定
    GITHUB_ACTIONS = 'GITHUB_ACTIONS'
    
    @classmethod
    def get(cls, key, default=None):
        """環境変数を取得"""
        return os.getenv(key, default)
    
    @classmethod
    def get_required(cls, key, env_name=""):
        """必須環境変数を取得（存在しない場合はエラー）
        
        Args:
            key: 環境変数名
            env_name: エラーメッセージ用の環境名
            
        Returns:
            環境変数の値
            
        Raises:
            ValueError: 環境変数が設定されていない場合
        """
        value = os.getenv(key)
        if not value:
            env_prefix = f"{env_name}環境用の" if env_name else ""
            raise ValueError(f"{env_prefix}環境変数 {key} が設定されていません")
        return value
    
    @classmethod
    def is_github_actions(cls):
        """GitHub Actions環境かどうかを判定"""
        return cls.get(cls.GITHUB_ACTIONS) == 'true'
    
    @classmethod
    def get_environment_from_arg(cls, env_arg=None):
        """引数から環境を取得
        
        Args:
            env_arg: 環境指定引数 (0=本番, 1=テスト, 2=開発)
            
        Returns:
            Environment: 環境の列挙型
        """
        if env_arg is None:
            return Environment.PRODUCTION
        try:
            return Environment(int(env_arg))
        except (ValueError, TypeError):
            raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")
    
    @classmethod
    def get_environment_name(cls, env=Environment.PRODUCTION):
        """環境名を取得
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
            
        Returns:
            str: 環境名
        """
        if env == Environment.TEST:
            return "テスト環境"
        elif env == Environment.DEVELOPMENT:
            return "開発環境"
        else:
            return "本番環境"
    
    @classmethod
    def get_discord_config(cls, env=Environment.PRODUCTION):
        """Discord関連の設定を取得
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
        
        Returns:
            dict: Discord設定の辞書
        """
        env_name = cls.get_environment_name(env)
        env_prefix = 'TEST_' if env == Environment.TEST else ''
        
        token_key = f'{env_prefix}{cls.DISCORD_BOT_TOKEN}'
        channel_ids_key = f'{env_prefix}{cls.ALLOWED_VOICE_CHANNEL_IDS}'
        
        token = cls.get_required(token_key, env_name)  # 必須値として取得
        channel_ids_str = cls.get_required(channel_ids_key, env_name)  # 必須値として取得
        
        # チャンネルIDのリストに変換
        channel_ids = [id.strip() for id in channel_ids_str.split(',') if id.strip()]
        if not channel_ids:
            raise ValueError(f"{env_name}環境用のチャンネルIDが正しく設定されていません")
        
        return {
            'token': token,
            'channel_ids': channel_ids
        }
    
    @classmethod
    def get_google_sheets_config(cls, env=Environment.PRODUCTION):
        """Google Sheets関連の設定を取得
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
        
        Returns:
            dict: Google Sheets設定の辞書
        """
        env_name = cls.get_environment_name(env)
        env_prefix = 'TEST_' if env == Environment.TEST else ''
        
        sheet_name_key = f'{env_prefix}{cls.GOOGLE_SHEET_NAME}'
        json_key = f'{env_prefix}{cls.GOOGLE_SERVICE_ACCOUNT_JSON}'
        base64_key = f'{env_prefix}{cls.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64}'
        
        sheet_name = cls.get_required(sheet_name_key, env_name)  # 必須値として取得
        
        # サービスアカウント認証はJSONファイルかBase64のいずれかが必須
        service_account_json = cls.get(json_key, 'service_account.json')
        service_account_json_base64 = cls.get(base64_key)
        
        # どちらも設定されていない場合はエラー
        if not service_account_json_base64 and not os.path.exists(service_account_json):
            raise ValueError(
                f"{env_name}環境用の認証情報が見つかりません。"
                f"{base64_key}または{json_key}（ファイル）を設定してください"
            )
        
        return {
            'sheet_name': sheet_name,
            'service_account_json': service_account_json,
            'service_account_json_base64': service_account_json_base64
        }
    
    @classmethod
    def get_slack_config(cls, env=Environment.PRODUCTION):
        """Slack関連の設定を取得（オプション）
        
        Args:
            env: 環境（Environment.PRODUCTION/TEST/DEVELOPMENT）
        
        Returns:
            dict: Slack設定の辞書（設定がない場合はNone値を含む）
        """
        env_prefix = 'TEST_' if env == Environment.TEST else ''
        
        token_key = f'{env_prefix}{cls.SLACK_BOT_TOKEN}'
        channel_id_key = f'{env_prefix}{cls.SLACK_CHANNEL_ID}'
        
        # Slackはオプションなので、設定がない場合はNoneを返す
        return {
            'token': cls.get(token_key),
            'channel_id': cls.get(channel_id_key)
        }
    
    @classmethod
    def get_all_configs(cls):
        """全環境の設定を取得（デバッグ用）"""
        configs = {}
        for env in Environment:
            env_name = cls.get_environment_name(env)
            try:
                configs[env_name] = {
                    'discord': cls.get_discord_config(env),
                    'google_sheets': cls.get_google_sheets_config(env),
                    'slack': cls.get_slack_config(env)
                }
            except ValueError as e:
                configs[env_name] = {'error': str(e)}
        return configs


# エクスポート用のインスタンス
config = EnvConfig()


# 直接実行時のテストコード
if __name__ == "__main__":
    import sys
    
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
    except ValueError as e:
        print(f"  ❌ エラー: {e}")
    
    # Slack設定
    print("\n💬 Slack設定:")
    slack_config = EnvConfig.get_slack_config(env)
    if slack_config['token']:
        print(f"  ✅ トークン: {slack_config['token'][:20]}...")
    else:
        print("  ⚠️ 未設定（オプション）")
    
    print("\n" + "=" * 70)
    print("テスト完了")
    print("=" * 70)