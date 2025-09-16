"""
環境設定管理モジュール (config.py)
本番環境、テスト環境、開発環境ごとに異なる設定を切り替えます
"""

import os
from enum import IntEnum
from dotenv import load_dotenv

load_dotenv()


class Environment(IntEnum):
    """環境の定義"""
    PRD = 0  # 本番環境
    TST = 1  # テスト環境
    DEV = 2  # 開発環境


def get_config(env: Environment = Environment.DEV) -> dict:
    """指定環境のすべての設定を取得"""

    suffix = ['_0_PRD', '_1_TST', '_2_DEV'][env]
    channel_ids_str = os.getenv(f'ALLOWED_VOICE_CHANNEL_IDS{suffix}', '')

    return {
        'discord_token': discord_token,
        'channel_ids': [id.strip() for id in channel_ids_str.split(',') if id.strip()],
        'sheet_name': f'もくもくトラッカー_{env}_{["PRD","TST","DEV"][env]}',
        'service_account_json': service_json,
        'service_account_json_base64': service_base64,
        'folder_path': 'discord_mokumoku_tracker',
        'shared_drive_id': shared_drive,
        'env_name': ['PRD', 'TST', 'DEV'][env],
        'env_number': str(env),
        'slack_token': slack_token,
        'slack_channel': slack_channel
    }


def get_environment_from_arg(env_arg: int = None) -> Environment:
    """コマンドライン引数から環境を取得"""
    if env_arg is None:
        return Environment.DEV
    try:
        return Environment(env_arg)
    except (ValueError, TypeError):
        raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")


# ===== 後方互換性のため（段階的に削除予定） =====

def get_env_var_name(base_name: str, env: Environment = Environment.PRD) -> str:
    """後方互換性のため"""
    suffix = {Environment.PRD: '_0_PRD', Environment.TST: '_1_TST', Environment.DEV: '_2_DEV'}
    return f'{base_name}{suffix.get(env, "")}'


def get_discord_config(env: Environment = Environment.PRD) -> dict:
    """後方互換性のため"""
    config = get_config(env)
    return {'token': config['discord_token'], 'channel_ids': config['channel_ids']}


def get_google_sheets_config(env: Environment = Environment.PRD) -> dict:
    """後方互換性のため"""
    config = get_config(env)
    return {
        'sheet_name': config['sheet_name'],
        'service_account_json': config['service_account_json'],
        'service_account_json_base64': config['service_account_json_base64']
    }


def get_google_drive_config(env: Environment = Environment.PRD) -> dict:
    """後方互換性のため"""
    config = get_config(env)
    return {
        'folder_path': config['folder_path'],
        'folder_id': None,
        'shared_drive_id': config['shared_drive_id'],
        'service_account_json': config['service_account_json'],
        'service_account_json_base64': config['service_account_json_base64'],
        'env_name': config['env_name'],
        'env_number': config['env_number']
    }


def get_slack_config(env: Environment = Environment.PRD) -> dict:
    """後方互換性のため"""
    config = get_config(env)
    return {'bot_token': config['slack_token'], 'channel_id': config['slack_channel']}


def get_environment_name(env: Environment = Environment.PRD) -> str:
    """後方互換性のため"""
    return {Environment.PRD: "本番環境", Environment.TST: "テスト環境", Environment.DEV: "開発環境"}[env]


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
        return {'PRD': '0', 'TST': '1', 'DEV': '2'}.get(env_name, '9')