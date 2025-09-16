"""
環境設定管理モジュール (config.py)
このファイルは、開発用とテスト用と本番用で使い分けるための設定を管理します。
例えば、テストではテスト用のDiscordサーバーで動かし、本番では実際のサーバーで動かします。
環境ごとに異なるトークン（パスワードのようなもの）や設定値を自動的に切り替えることで、
間違えて本番サーバーでテストしてしまうような事故を防ぎます。
"""

import os  # 環境変数（パソコンの設定値）を読み込むためのツール
from enum import IntEnum  # 環境を番号で管理するためのツール
from dotenv import load_dotenv  # .envファイルから設定を読み込むためのツール

load_dotenv()  # .envファイルから環境変数を読み込む（パスワードなどの秘密情報を安全に管理）


class Environment(IntEnum):
    """
    環境の定義（3つのモードを番号で管理）
    スマホのマナーモードのように、場面に応じて切り替えます
    """
    PRD = 0  # 本番環境（実際にユーザーが使う環境）
    TST = 1  # テスト環境（新機能を試す環境）
    DEV = 2  # 開発環境（プログラマーが開発する環境）


def get_config(env: Environment = Environment.DEV) -> dict:
    """
    指定された環境（本番/テスト/開発）の設定値をすべて取得する関数
    環境に応じて異なるパスワードやサーバー情報を返します
    """

    suffix = ['0_PRD', '1_TST', '2_DEV'][env]  # 環境ごとの識別子（例：0_PRD = 本番環境用の印）

    return {
        'discord_token': os.getenv(f'DISCORD_BOT_TOKEN_{suffix}'),  # Discord Botの認証トークン（Botがログインするためのパスワード）
        'discord_channel_ids': [id.strip() for id in os.getenv(f'ALLOWED_VOICE_CHANNEL_IDS_{suffix}', '').split(',') if id.strip()],  # 監視対象のボイスチャンネルIDリスト（カンマ区切りで複数指定可能）
        'google_drive_service_account_json': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON_{suffix}', 'service_account.json'),  # Google Driveにアクセスするための認証ファイルのパス
        'google_drive_service_account_json_base64': os.getenv(f'GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_{suffix}'),  # 認証情報をテキスト形式で保存したもの（GitHub Actionsなどで使用）
        'google_drive_shared_drive_id': os.getenv(f'GOOGLE_SHARED_DRIVE_ID_{suffix}'),  # Google共有ドライブのID（共有ドライブを使う場合のみ）
        'google_drive_base_folder': 'discord_mokumoku_tracker',  # Google Drive上のベースフォルダ名（すべてのデータはこのフォルダ内に保存）
        'google_drive_csv_path': 'discord_mokumoku_tracker/{vc_name}/csv/' + f'{suffix}.csv',  # CSVファイルのフルパス（例: discord_mokumoku_tracker/一般/csv/0_PRD.csv）
        'google_drive_spreadsheet_path': 'discord_mokumoku_tracker/{vc_name}/' + f'もくもくトラッカー_{suffix}',  # スプレッドシートのフルパス（例: discord_mokumoku_tracker/一般/もくもくトラッカー_0_PRD）
        'slack_token': os.getenv(f'SLACK_BOT_TOKEN_{suffix}'),  # Slack通知用のBotトークン（Slackにメッセージを送るためのパスワード）
        'slack_channel': os.getenv(f'SLACK_CHANNEL_ID_{suffix}'),  # 通知先のSlackチャンネルID
        'suffix': suffix,  # 環境識別子（0_PRD/1_TST/2_DEV）を他の処理でも使えるように保存
    }


def get_environment_from_arg(env_arg: int = None) -> Environment:
    """
    コマンドライン引数（実行時に指定する数字）から環境を判定する関数
    例：python script.py --env 0 → 本番環境として実行
    """
    if env_arg is None:  # 環境が指定されていない場合
        return Environment.DEV  # デフォルトは開発環境（一番安全な選択）
    try:
        return Environment(env_arg)  # 指定された番号を環境に変換（0→PRD、1→TST、2→DEV）
    except (ValueError, TypeError):  # 無効な番号が指定された場合（例：3や"abc"など）
        raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")  # エラーメッセージを表示