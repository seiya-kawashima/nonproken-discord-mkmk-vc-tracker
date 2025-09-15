"""
========================================
環境設定管理モジュール (config.py)
========================================
概要: このファイルは、プログラムの設定を管理する重要なファイルです
      本番環境、テスト環境、開発環境ごとに異なる設定を切り替えます
      環境変数（パスワードやトークンなどの秘密情報）を安全に管理します

用途:
  - Discord Botのトークン管理
  - Google Sheets認証情報の管理
  - Slack通知設定の管理
  - 環境ごとの設定切り替え

環境の種類:
  - PRD (Production) = 本番環境：実際に使用する環境
  - TST (Test) = テスト環境：動作確認用の環境
  - DEV (Development) = 開発環境：開発者が使う環境
========================================
"""

import os  # オペレーティングシステムの機能を使うためのモジュール
from enum import IntEnum  # 列挙型（番号付きの定数リスト）を作るためのモジュール
from dotenv import load_dotenv  # .envファイルから環境変数を読み込むためのモジュール

# .envファイルを読み込み（プロジェクトルートの.envファイルから環境変数を読み込む）
load_dotenv()  # この行で.envファイルの内容が環境変数として利用可能になる


class Environment(IntEnum):
    """環境の定義クラス

    プログラムが動作する環境を番号で管理します
    0: PRD - 本番環境（実際のユーザーが使う環境）
    1: TST - テスト環境（動作確認用の環境）
    2: DEV - 開発環境（開発者がテストする環境）
    """
    PRD = 0  # 本番環境を0番とする（デフォルト）
    TST = 1  # テスト環境を1番とする
    DEV = 2  # 開発環境を2番とする

    @classmethod  # クラスメソッド（インスタンスを作らずに使えるメソッド）
    def from_value(cls, value):  # 数値から環境を判定するメソッド
        """数値から環境を取得する便利メソッド"""
        if value is None:  # 値が指定されていない場合
            return cls.PRD  # デフォルトは本番環境を返す
        return cls(value)  # 指定された値に対応する環境を返す


class EnvConfig:
    """環境変数の設定を管理するクラス

    このクラスで全ての環境変数へのアクセスを一元管理します
    セキュリティ的に重要な情報を安全に扱うための仕組みです
    """

    # スプレッドシート名（環境ごとに異なる名前を使用可能）
    PRD_SHEET_NAME = 'VCトラッカー_PRD'  # 本番環境のGoogle Sheetsのシート名
    TST_SHEET_NAME = 'VCトラッカー_TST'  # テスト環境のGoogle Sheetsのシート名
    DEV_SHEET_NAME = 'VCトラッカー_DEV'  # 開発環境のGoogle Sheetsのシート名

    @classmethod  # クラスメソッド（インスタンスを作らずに使えるメソッド）
    def get_env_var_name(cls, base_name, env=Environment.PRD):  # 環境に応じた変数名を作るメソッド
        """環境に応じた環境変数名を取得

        例: base_name='DISCORD_BOT_TOKEN', env=TST の場合
        　　→ 'TST_DISCORD_BOT_TOKEN' を返す

        Args:
            base_name: ベースとなる環境変数名（例: 'DISCORD_BOT_TOKEN'）
            env: 環境（PRD/TST/DEV のいずれか）

        Returns:
            str: 環境に応じた環境変数名（例: 'TST_DISCORD_BOT_TOKEN'）
        """
        if env == Environment.TST:  # テスト環境の場合
            return f'TST_{base_name}'  # 先頭に'TST_'を付ける
        elif env == Environment.DEV:  # 開発環境の場合
            return f'DEV_{base_name}'  # 先頭に'DEV_'を付ける
        return base_name  # 本番環境の場合はそのまま返す

    # GitHub Actions環境かどうかを判定するための定数
    GITHUB_ACTIONS = 'GITHUB_ACTIONS'  # GitHub Actionsで自動的に設定される環境変数名

    @classmethod  # クラスメソッド
    def get(cls, key, default=None):  # 環境変数を取得するメソッド
        """環境変数を取得（存在しない場合はデフォルト値を返す）"""
        return os.getenv(key, default)  # os.getenvで環境変数を取得（なければdefaultを返す）

    @classmethod  # クラスメソッド
    def get_required(cls, key, env_name=""):  # 必須の環境変数を取得するメソッド
        """必須環境変数を取得（存在しない場合はエラーを発生させる）

        Args:
            key: 環境変数名（例: 'DISCORD_BOT_TOKEN'）
            env_name: エラーメッセージ用の環境名（例: 'テスト環境'）

        Returns:
            環境変数の値（必ず存在する値）

        Raises:
            ValueError: 環境変数が設定されていない場合にエラーを発生
        """
        value = os.getenv(key)  # 環境変数を取得
        if not value:  # 値が存在しない場合
            env_prefix = f"{env_name}環境用の" if env_name else ""  # エラーメッセージの接頭辞を作成
            raise ValueError(f"{env_prefix}環境変数 {key} が設定されていません")  # エラーを発生させる
        return value  # 値を返す

    @classmethod  # クラスメソッド
    def is_github_actions(cls):  # GitHub Actions環境かどうかを判定
        """GitHub Actions環境かどうかを判定（CI/CD環境での動作確認用）"""
        return cls.get(cls.GITHUB_ACTIONS) == 'true'  # GITHUB_ACTIONS環境変数が'true'ならTrue

    @classmethod  # クラスメソッド
    def get_environment_from_arg(cls, env_arg=None):  # コマンドライン引数から環境を判定
        """引数から環境を取得（コマンドラインから環境を指定するため）

        Args:
            env_arg: 環境指定引数 (0=本番, 1=テスト, 2=開発)

        Returns:
            Environment: 環境の列挙型（PRD/TST/DEV のいずれか）
        """
        if env_arg is None:  # 引数が指定されていない場合
            return Environment.PRD  # デフォルトは本番環境
        try:  # エラーが発生する可能性がある処理
            return Environment(int(env_arg))  # 数値を環境に変換
        except (ValueError, TypeError):  # 変換に失敗した場合
            raise ValueError(f"無効な環境指定: {env_arg}. 0(本番), 1(テスト), 2(開発)のいずれかを指定してください")  # エラーメッセージ

    @classmethod  # クラスメソッド
    def get_environment_name(cls, env=Environment.PRD):  # 環境の日本語名を取得
        """環境名を取得（人間が読みやすい形式で環境名を取得）

        Args:
            env: 環境（Environment.PRD/TST/DEV）

        Returns:
            str: 環境名（'本番環境'/'テスト環境'/'開発環境'）
        """
        if env == Environment.TST:  # テスト環境の場合
            return "テスト環境"  # 'テスト環境'を返す
        elif env == Environment.DEV:  # 開発環境の場合
            return "開発環境"  # '開発環境'を返す
        else:  # それ以外（本番環境）の場合
            return "本番環境"  # '本番環境'を返す

    @classmethod  # クラスメソッド
    def get_discord_config(cls, env=Environment.PRD):  # Discord関連の設定を取得
        """Discord関連の設定を取得（Discord Botの接続に必要な情報を取得）

        Args:
            env: 環境（Environment.PRD/TST/DEV）

        Returns:
            dict: Discord設定の辞書 {'token': 'xxx', 'channel_ids': ['111', '222']}
        """
        env_name = cls.get_environment_name(env)  # 環境の日本語名を取得

        # 環境に応じた環境変数名を取得（例: TST_DISCORD_BOT_TOKEN）
        token_key = cls.get_env_var_name('DISCORD_BOT_TOKEN', env)  # トークンの環境変数名を作成
        channel_ids_key = cls.get_env_var_name('ALLOWED_VOICE_CHANNEL_IDS', env)  # チャンネルIDの環境変数名を作成

        token = cls.get_required(token_key, env_name)  # Botトークンを取得（必須）

        # テスト環境では channel_ids も必須とする（テストには必ずチャンネルIDが必要）
        if env == Environment.TST:  # テスト環境の場合
            channel_ids_str = cls.get_required(channel_ids_key, env_name)  # チャンネルIDを必須で取得
        else:  # 本番・開発環境の場合
            channel_ids_str = cls.get(channel_ids_key, '')  # チャンネルIDをオプションで取得（なければ空文字）

        # チャンネルIDのリストに変換（カンマ区切りの文字列をリストに変換）
        channel_ids = []  # 空のリストを準備
        if channel_ids_str:  # チャンネルIDが設定されている場合
            channel_ids = [id.strip() for id in channel_ids_str.split(',') if id.strip()]  # カンマで分割してリスト化
            if env == Environment.TST and not channel_ids:  # テスト環境でリストが空の場合
                raise ValueError(f"{env_name}環境用のチャンネルIDが正しく設定されていません")  # エラーを発生

        return {  # 辞書形式で設定を返す
            'token': token,  # Botトークン
            'channel_ids': channel_ids  # 監視対象のチャンネルIDリスト
        }

    @classmethod  # クラスメソッド
    def get_google_sheets_config(cls, env=Environment.PRD):  # Google Sheets関連の設定を取得
        """Google Sheets関連の設定を取得（スプレッドシートへの接続に必要な情報）

        Args:
            env: 環境（Environment.PRD/TST/DEV）

        Returns:
            dict: Google Sheets設定の辞書
        """
        env_name = cls.get_environment_name(env)  # 環境の日本語名を取得

        # 環境に応じたシート名を使用
        if env == Environment.TST:  # テスト環境の場合
            sheet_name = cls.TST_SHEET_NAME  # テスト用のシート名を使用
        elif env == Environment.DEV:  # 開発環境の場合
            sheet_name = cls.DEV_SHEET_NAME  # 開発用のシート名を使用
        else:  # 本番環境の場合
            sheet_name = cls.PRD_SHEET_NAME  # 本番用のシート名を使用

        # 環境変数で上書き可能（オプション）
        sheet_name_key = cls.get_env_var_name('GOOGLE_SHEET_NAME', env)  # 環境変数名を作成
        sheet_name = cls.get(sheet_name_key, sheet_name)  # 環境変数があれば上書き

        # 環境に応じた環境変数名を取得
        json_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON', env)  # JSONファイルパスの環境変数名
        base64_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64', env)  # Base64形式の環境変数名

        # サービスアカウント認証はJSONファイルかBase64のいずれかが必須
        service_account_json = cls.get(json_key, 'service_account.json')  # JSONファイルパス（デフォルト: service_account.json）
        service_account_json_base64 = cls.get(base64_key)  # Base64形式の認証情報

        # どちらも設定されていない場合はエラー
        if not service_account_json_base64 and not os.path.exists(service_account_json):  # 両方とも存在しない場合
            raise ValueError(  # エラーを発生
                f"{env_name}環境用の認証情報が見つかりません。"
                f"{base64_key}または{json_key}（ファイル）を設定してください"
            )

        return {  # 辞書形式で設定を返す
            'sheet_name': sheet_name,  # スプレッドシート名
            'service_account_json': service_account_json,  # JSONファイルパス
            'service_account_json_base64': service_account_json_base64  # Base64形式の認証情報
        }

    @classmethod  # クラスメソッド
    def get_google_drive_config(cls, env=Environment.PRD):  # Google Drive関連の設定を取得
        """Google Drive関連の設定を取得（CSVファイル保存先の設定）

        Args:
            env: 環境（Environment.PRD/TST/DEV）

        Returns:
            dict: Google Drive設定の辞書
        """
        # デフォルトのフォルダ階層パス
        # discord_mokumoku_tracker/csv の形式（VCチャンネル名は実行時に追加）
        default_folder_path = "csv"  # 共有ドライブ内のベースフォルダパス

        # 環境に応じたフォルダパスの環境変数名を取得
        folder_path_key = cls.get_env_var_name('GOOGLE_DRIVE_FOLDER_PATH', env)  # 環境変数名を作成
        folder_id_key = cls.get_env_var_name('GOOGLE_DRIVE_FOLDER_ID', env)  # フォルダID環境変数名
        shared_drive_id_key = cls.get_env_var_name('GOOGLE_SHARED_DRIVE_ID', env)  # 共有ドライブID環境変数名

        # 環境変数から取得、なければデフォルトの階層パスを使用
        folder_path = cls.get(folder_path_key, default_folder_path)  # フォルダパスを取得
        folder_id = cls.get(folder_id_key)  # 既存フォルダのID（オプション）

        # 共有ドライブIDを取得（デフォルト値を設定）
        shared_drive_id = cls.get(shared_drive_id_key, '0ANixFe4JBQskUk9PVA')  # 共有ドライブID
        # 空文字列の場合はNoneに変換（マイドライブを使用）
        if shared_drive_id == '':  # 空文字列の場合
            shared_drive_id = None  # Noneに変換してマイドライブを使用

        # 環境に応じた認証情報の環境変数名を取得（Google Sheetsと同じ認証情報を使用）
        json_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON', env)  # JSONファイルパスの環境変数名
        base64_key = cls.get_env_var_name('GOOGLE_SERVICE_ACCOUNT_JSON_BASE64', env)  # Base64形式の環境変数名

        # サービスアカウント認証情報を取得
        service_account_json = cls.get(json_key, 'service_account.json')  # JSONファイルパス
        service_account_json_base64 = cls.get(base64_key)  # Base64形式の認証情報

        return {  # 辞書形式で設定を返す
            'folder_path': folder_path,  # Google Drive上のフォルダパス（階層構造）
            'folder_id': folder_id,  # 既存フォルダのID（オプション）
            'shared_drive_id': shared_drive_id,  # 共有ドライブID
            'env_name': env.name,  # 環境名（PRD/TST/DEV）をファイル名に使用
            'service_account_json': service_account_json,  # JSONファイルパス
            'service_account_json_base64': service_account_json_base64  # Base64形式の認証情報
        }

    @classmethod  # クラスメソッド
    def get_slack_config(cls, env=Environment.PRD):  # Slack関連の設定を取得
        """Slack関連の設定を取得（Slack通知はオプション機能）

        Args:
            env: 環境（Environment.PRD/TST/DEV）

        Returns:
            dict: Slack設定の辞書（設定がない場合はNone値を含む）
        """
        # 環境に応じた環境変数名を取得
        token_key = cls.get_env_var_name('SLACK_BOT_TOKEN', env)  # Slackトークンの環境変数名
        channel_id_key = cls.get_env_var_name('SLACK_CHANNEL_ID', env)  # SlackチャンネルIDの環境変数名

        # Slackはオプションなので、設定がない場合はNoneを返す
        return {  # 辞書形式で設定を返す
            'token': cls.get(token_key),  # Slackトークン（なければNone）
            'channel_id': cls.get(channel_id_key)  # SlackチャンネルID（なければNone）
        }

    @classmethod  # クラスメソッド
    def get_all_configs(cls):  # 全環境の設定を取得（デバッグ用）
        """全環境の設定を取得（デバッグ用：設定の確認に使用）"""
        configs = {}  # 結果を格納する辞書
        for env in Environment:  # 全ての環境（PRD/TST/DEV）について
            env_name = cls.get_environment_name(env)  # 環境名を取得
            try:  # エラーが発生する可能性がある処理
                configs[env_name] = {  # 各環境の設定を取得
                    'discord': cls.get_discord_config(env),  # Discord設定
                    'google_sheets': cls.get_google_sheets_config(env),  # Google Sheets設定
                    'slack': cls.get_slack_config(env)  # Slack設定
                }
            except ValueError as e:  # 設定取得でエラーが発生した場合
                configs[env_name] = {'error': str(e)}  # エラー内容を記録
        return configs  # 全環境の設定を返す


# エクスポート用のインスタンス（他のファイルから使いやすくするため）
config = EnvConfig()  # EnvConfigクラスのインスタンスを作成（このconfigを他のファイルからインポートして使う）