"""
環境設定管理モジュール (config.py)
本番環境、テスト環境、開発環境ごとに異なる設定を切り替えます
"""

import os  # 環境変数取得用
from enum import IntEnum  # 列挙型用
from dotenv import load_dotenv  # .envファイル読み込み用

# .envファイルを読み込み
load_dotenv()


class Environment(IntEnum):
    """環境の定義"""
    PRD = 0  # 本番環境
    TST = 1  # テスト環境
    DEV = 2  # 開発環境


def get_env_var_name(base_name: str, env: Environment = Environment.PRD) -> str:
    """
    環境に応じた環境変数名を取得
    例: 'DISCORD_BOT_TOKEN' + DEV → 'DISCORD_BOT_TOKEN_2_DEV'
    """
    if env == Environment.PRD:
        return f'{base_name}_0_PRD'
    elif env == Environment.TST:
        return f'{base_name}_1_TST'
    elif env == Environment.DEV:
        return f'{base_name}_2_DEV'
    return base_name


def get_discord_config(env: Environment = Environment.PRD) -> dict:
    """Discord関連の設定を取得"""
    token_key = get_env_var_name('DISCORD_BOT_TOKEN', env)
    channel_ids_key = get_env_var_name('ALLOWED_VOICE_CHANNEL_IDS', env)

    token = os.getenv(token_key)
    if not token:
        raise ValueError(f"環境変数 {token_key} が設定されていません")

    channel_ids_str = os.getenv(channel_ids_key, '')
    channel_ids = [id.strip() for id in channel_ids_str.split(',') if id.strip()]

    return {
        'token': token,
        'channel_ids': channel_ids
    }


def get_google_sheets_config(env: Environment = Environment.PRD) -> dict:
    """Google Sheets関連の設定を取得"""
    # 環境ごとのシート名（ハードコード）
    sheet_names = {
        Environment.PRD: 'もくもくトラッカー_0_PRD',
        Environment.TST: 'もくもくトラッカー_1_TST',
        Environment.DEV: 'もくもくトラッカー_2_DEV'
    }

    json_key = get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON', env)
    base64_key = get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64', env)

    return {
        'sheet_name': sheet_names[env],
        'service_account_json': os.getenv(json_key, 'service_account.json'),
        'service_account_json_base64': os.getenv(base64_key)
    }


def get_google_drive_config(env: Environment = Environment.PRD) -> dict:
    """Google Drive関連の設定を取得"""
    # 環境名マップ
    env_names = {
        Environment.PRD: 'PRD',
        Environment.TST: 'TST',
        Environment.DEV: 'DEV'
    }

    # 環境番号マップ
    env_numbers = {
        Environment.PRD: '0',
        Environment.TST: '1',
        Environment.DEV: '2'
    }

    json_key = get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON', env)
    base64_key = get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64', env)
    shared_drive_key = get_env_var_name('GOOGLE_SHARED_DRIVE_ID', env)

    shared_drive_id = os.getenv(shared_drive_key, '0ANixFe4JBQskUk9PVA')
    if shared_drive_id == '':
        shared_drive_id = None

    return {
        'folder_path': 'discord_mokumoku_tracker',  # 固定値
        'folder_id': None,
        'shared_drive_id': shared_drive_id,
        'service_account_json': os.getenv(json_key, 'service_account.json'),
        'service_account_json_base64': os.getenv(base64_key),
        'env_name': env_names[env],
        'env_number': env_numbers[env]
    }


def get_slack_config(env: Environment = Environment.PRD) -> dict:
    """Slack関連の設定を取得"""
    token_key = get_env_var_name('SLACK_BOT_TOKEN', env)
    channel_key = get_env_var_name('SLACK_CHANNEL_ID', env)

    return {
        'bot_token': os.getenv(token_key),
        'channel_id': os.getenv(channel_key)
    }


def get_environment_name(env: Environment = Environment.PRD) -> str:
    """環境の日本語名を取得"""
    names = {
        Environment.PRD: "本番環境",
        Environment.TST: "テスト環境",
        Environment.DEV: "開発環境"
    }
    return names.get(env, "不明な環境")


def get_environment_from_arg(env_arg: int = None) -> Environment:
    """コマンドライン引数から環境を取得"""
    if env_arg is None:
        return Environment.DEV  # デフォルトは開発環境
    try:
        return Environment(env_arg)
    except (ValueError, TypeError):
        raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")


# 後方互換性のため（段階的に削除予定）
class EnvConfig:
    """後方互換性のためのラッパークラス"""

    @staticmethod
    def get_env_var_name(base_name, env=Environment.PRD):
        return get_env_var_name(base_name, env)

    @staticmethod
    def get_discord_config(env=Environment.PRD):
        return get_discord_config(env)

    @staticmethod
    def get_google_sheets_config(env=Environment.PRD):
        return get_google_sheets_config(env)

    @staticmethod
    def get_google_drive_config(env=Environment.PRD):
        return get_google_drive_config(env)

    @staticmethod
    def get_slack_config(env=Environment.PRD):
        return get_slack_config(env)

    @staticmethod
    def get_environment_name(env=Environment.PRD):
        return get_environment_name(env)

    @staticmethod
    def get_environment_from_arg(env_arg=None):
        return get_environment_from_arg(env_arg)

    @staticmethod
    def get_env_number(env_name: str) -> str:
        """環境名から番号を取得（CSVファイル名用）"""
        env_map = {'PRD': '0', 'TST': '1', 'DEV': '2'}
        return env_map.get(env_name, '9')