"""Discord VC Tracker - メイン処理スクリプト"""  # スクリプトの説明

import os  # 環境変数の取得用
import sys  # システム関連操作用
import asyncio  # 非同期処理用
import argparse  # コマンドライン引数処理用
from loguru import logger  # ログ出力用（loguru）

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  # srcディレクトリをインポートパスに追加

from config import EnvConfig, Environment  # 環境変数設定モジュールと環境列挙型
from src.discord_client import DiscordVCPoller  # Discord VCポーリングクラス
from src.drive_csv_client import DriveCSVClient  # Google Drive CSVクライアント

# loguruの設定
logger.remove()  # デフォルトハンドラーを削除
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # コンソール出力（ファイル名と関数名付き）
# logsフォルダが存在しない場合は作成
os.makedirs("logs", exist_ok=True)  # logsフォルダを作成（既に存在する場合はスキップ）
logger.add("logs/discord_vc_tracker.log", rotation="10 MB", retention="7 days", level="INFO", encoding="utf-8", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}.py | def: {function} | {message}")  # ファイル出力（10MBでローテーション、7日間保持、ファイル名と関数名付き）


async def main(env_arg=None):
    """メイン処理
    
    Args:
        env_arg: 環境指定 (0=本番, 1=テスト, 2=開発)
    """  # 関数の説明
    
    # 引数から環境を取得
    try:
        env = EnvConfig.get_environment_from_arg(env_arg)  # 環境を引数から取得
    except ValueError as e:
        logger.error(str(e))  # エラーメッセージをログ出力
        sys.exit(1)  # 異常終了
    
    env_name = EnvConfig.get_environment_name(env)  # 環境名を取得
    logger.info(f"実行環境: {env_name}")  # 環境名をログ出力
    
    # 環境に応じた設定を取得（必須値チェック付き）
    try:
        discord_config = EnvConfig.get_discord_config(env)  # Discord設定
        sheets_config = EnvConfig.get_google_sheets_config(env)  # Google Sheets設定
        drive_config = EnvConfig.get_google_drive_config(env)  # Google Drive設定
    except ValueError as e:
        logger.error(f"設定エラー: {e}")  # 設定エラーをログ出力
        sys.exit(1)  # 異常終了
    
    # 設定値を展開（必須値は既にconfig.pyでチェック済み）
    discord_token = discord_config['token']  # Discord Botトークン
    channel_ids = discord_config['channel_ids']  # 監視対象VCチャンネルID
    sheet_name = sheets_config['sheet_name']  # スプレッドシート名
    service_account_json = sheets_config['service_account_json']  # サービスアカウントJSON
    service_account_json_base64 = sheets_config['service_account_json_base64']  # Base64エンコードされた認証情報
    
    # Base64エンコードされた認証情報がある場合はデコード
    import json  # JSON処理用
    import base64  # Base64デコード用
    import tempfile  # 一時ファイル作成用
    
    temp_file = None  # 一時ファイルパス
    if service_account_json_base64:  # Base64エンコードされた認証情報がある場合
        try:
            decoded_bytes = base64.b64decode(service_account_json_base64)  # Base64デコード
            decoded_str = decoded_bytes.decode('utf-8')  # UTF-8文字列に変換
            json_data = json.loads(decoded_str)  # JSONパース
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:  # 一時ファイル作成
                json.dump(json_data, f)  # JSONデータを書き込み
                temp_file = f.name  # ファイルパスを保存
                service_account_json = temp_file  # サービスアカウントJSONパスを更新
            logger.info("認証情報をBase64からデコードしました")  # デコード成功ログ
        except Exception as e:  # デコードエラー時
            logger.error(f"Base64デコードエラー: {e}")  # エラーログ出力
            sys.exit(1)  # 異常終了
    
    # サービスアカウントJSONファイルの存在確認
    elif not os.path.exists(service_account_json):  # JSONファイルが存在しない場合
        logger.error(f"サービスアカウントのJSONファイルが見つかりません: {service_account_json}")  # エラーログ出力
        sys.exit(1)  # 異常終了
    
    try:
        # 1. Discord VCからメンバー情報を取得
        logger.info("Discord VCからメンバー情報を取得中...")  # 処理開始ログ
        discord_client = DiscordVCPoller(discord_token, channel_ids)  # Discordクライアント作成
        vc_members = await discord_client.get_vc_members()  # VCメンバー取得
        
        if not vc_members:  # メンバーがいない場合
            logger.info("監視対象のVCにメンバーが見つかりませんでした")  # メンバーなしログ
            return  # 処理終了
        
        logger.info(f"VCに{len(vc_members)}人のメンバーを発見しました")  # メンバー数ログ
        
        # 2. Google Drive上のCSVに記録
        logger.info("Google Driveに接続中...")  # 接続開始ログ
        # Google Drive設定からフォルダパス、環境名、共有ドライブIDを取得
        drive_folder_path = drive_config.get('folder_path', 'discord_mokumoku_tracker/csv')  # フォルダパス取得
        env_name = drive_config.get('env_name', 'PRD')  # 環境名取得（PRD/TST/DEV）
        shared_drive_id = drive_config.get('shared_drive_id')  # 共有ドライブID取得
        csv_client = DriveCSVClient(service_account_json, drive_folder_path, env_name, shared_drive_id)  # CSVクライアント作成（フォルダパス、環境名、共有ドライブID指定）
        csv_client.connect()  # 接続

        logger.info("出席データをCSVファイルに記録中...")  # 記録開始ログ
        result = csv_client.upsert_presence(vc_members)  # 出席データ記録
        new_count = result.get('new', 0)  # 新規件数を取得
        updated_count = result.get('updated', 0)  # 更新件数を取得
        logger.info(f"記録完了: 新規 {new_count}件、更新 {updated_count}件")  # 記録結果ログ
        
        
        logger.info("処理が正常に完了しました")  # 処理完了ログ
        
    except Exception as e:  # エラー発生時
        import traceback  # トレースバック用
        logger.error(f"処理中にエラーが発生しました: {e}")  # エラーログ出力
        logger.error(f"詳細なエラー情報: {traceback.format_exc()}")  # スタックトレース出力
        sys.exit(1)  # 異常終了
    
    finally:
        # 一時ファイルの削除
        if temp_file and os.path.exists(temp_file):  # 一時ファイルが存在する場合
            os.unlink(temp_file)  # ファイル削除
            logger.debug("一時ファイルを削除しました")  # 削除ログ


if __name__ == "__main__":  # スクリプト直接実行時
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(  # 引数パーサー作成
        description='Discord VC Tracker - VCメンバーを記録'  # スクリプト説明
    )
    parser.add_argument(  # 環境引数追加
        '--env',  # オプション名
        type=int,  # 整数型
        choices=[0, 1, 2],  # 許可値
        default=0,  # デフォルト値
        help='0=本番環境(デフォルト), 1=テスト環境, 2=開発環境'  # ヘルプメッセージ
    )
    args = parser.parse_args()  # 引数パース
    
    # メイン処理を非同期実行
    asyncio.run(main(args.env))  # 環境引数を渡して実行