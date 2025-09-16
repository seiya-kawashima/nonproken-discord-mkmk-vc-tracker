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
    env_name = ['PRD', 'TST', 'DEV'][env]
    env_number = str(env)
    channel_ids_str = os.getenv(f'ALLOWED_VOICE_CHANNEL_IDS{suffix}', '')

    return {
        'discord_token': os.getenv(f'DISCORD_BOT_TOKEN{suffix}'),
        'discord_channel_ids': [id.strip() for id in channel_ids_str.split(',') if id.strip()],
        'google_drive_service_account_json': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON{suffix}', 'service_account.json'),
        'google_drive_service_account_json_base64': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64{suffix}'),
        'google_drive_shared_drive_id': os.getenv(f'GOOGLE_SHARED_DRIVE_ID{suffix}'),
        'google_drive_folder_path': 'discord_mokumoku_tracker',  # Google Driveベースフォルダパス
        'google_drive_folder_structure': {  # Google Driveフォルダ構造定義
            'base': 'discord_mokumoku_tracker',  # ベースフォルダ名
            'vc_folder': '{vc_name}',  # VCチャンネルフォルダ名のテンプレート
            'csv_folder': 'csv',  # CSVフォルダ名
            'csv_file': f'{env_number}_{env_name}.csv',  # CSVファイル名
            'spreadsheet': f'もくもくトラッカー_{env_number}_{env_name}'  # スプレッドシート名
        },
        'slack_token': os.getenv(f'SLACK_BOT_TOKEN{suffix}'),
        'slack_channel': os.getenv(f'SLACK_CHANNEL_ID{suffix}'),
        'env_name': env_name,  # 環境名 (PRD/TST/DEV)
        'env_number': env_number,  # 環境番号 (0/1/2)
        'suffix': suffix,  # サフィックス (_0_PRD/_1_TST/_2_DEV)
    }


def get_environment_from_arg(env_arg: int = None) -> Environment:
    """コマンドライン引数から環境を取得"""
    if env_arg is None:
        return Environment.DEV
    try:
        return Environment(env_arg)
    except (ValueError, TypeError):
        raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")