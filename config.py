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

    suffix = ['0_PRD', '1_TST', '2_DEV'][env]  # サフィックス (0_PRD/1_TST/2_DEV)

    return {
        'discord_token': os.getenv(f'DISCORD_BOT_TOKEN_{suffix}'),
        'discord_channel_ids': [id.strip() for id in os.getenv(f'ALLOWED_VOICE_CHANNEL_IDS_{suffix}', '').split(',') if id.strip()],
        'google_drive_service_account_json': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON_{suffix}', 'service_account.json'),
        'google_drive_service_account_json_base64': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_{suffix}'),
        'google_drive_shared_drive_id': os.getenv(f'GOOGLE_SHARED_DRIVE_ID_{suffix}'),
        'google_drive_folder_path': 'discord_mokumoku_tracker',  # Google Driveベースフォルダパス
        'google_drive_folder_structure': {  # Google Driveフォルダ構造定義
            'base': 'discord_mokumoku_tracker',  # ベースフォルダ名
            'vc_folder': '{vc_name}',  # VCチャンネルフォルダ名のテンプレート
            'csv_folder': 'csv',  # CSVフォルダ名
            'csv_file': f'{suffix}.csv',  # CSVファイル名 (例: 0_PRD.csv)
            'spreadsheet': f'もくもくトラッカー_{suffix}'  # スプレッドシート名 (例: もくもくトラッカー_0_PRD)
        },
        'slack_token': os.getenv(f'SLACK_BOT_TOKEN_{suffix}'),
        'slack_channel': os.getenv(f'SLACK_CHANNEL_ID_{suffix}'),
        'suffix': suffix,  # サフィックス (0_PRD/1_TST/2_DEV)
    }


def get_environment_from_arg(env_arg: int = None) -> Environment:
    """コマンドライン引数から環境を取得"""
    if env_arg is None:
        return Environment.DEV
    try:
        return Environment(env_arg)
    except (ValueError, TypeError):
        raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")