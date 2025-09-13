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
    
    # スプレッドシート名（環境ごとに固定）
    SHEET_NAMES = {
        Environment.PRODUCTION: 'VCトラッカー',  # 本番用シート名
        Environment.TEST: 'テスト用VCトラッカー',  # テスト用シート名
        Environment.DEVELOPMENT: '開発VCトラッカー'  # 開発用シート名
    }
    
    @classmethod
    def get_env_var_name(cls, base_name, env=Environment.PRODUCTION):
        """環境に応じた環境変数名を取得
        
        Args:
            base_name: ベースとなる環境変数名
            env: 環境
            
        Returns:
            str: 環境に応じた環境変数名
        """
        if env == Environment.TEST:
            return f'TEST_{base_name}'
        return base_name
    
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
        
        # 環境に応じた環境変数名を取得
        token_key = cls.get_env_var_name('DISCORD_BOT_TOKEN', env)
        channel_ids_key = cls.get_env_var_name('ALLOWED_VOICE_CHANNEL_IDS', env)
        
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
        
        # 環境ごとに固定のシート名を使用
        sheet_name = cls.SHEET_NAMES[env]
        
        # 環境に応じた環境変数名を取得
        json_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON', env)
        base64_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64', env)
        
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
        # 環境に応じた環境変数名を取得
        token_key = cls.get_env_var_name('SLACK_BOT_TOKEN', env)
        channel_id_key = cls.get_env_var_name('SLACK_CHANNEL_ID', env)
        
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