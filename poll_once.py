"""Discord VC Tracker - メイン処理スクリプト"""  # スクリプトの説明

import os  # 環境変数の取得用
import sys  # システム関連操作用
import asyncio  # 非同期処理用
import logging  # ログ出力用
from dotenv import load_dotenv  # 環境変数読み込み用

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))  # srcディレクトリをインポートパスに追加

from src.discord_client import DiscordVCPoller  # Discord VCポーリングクラス
from src.sheets_client import SheetsClient  # Google Sheetsクライアント
from src.slack_notifier import SlackNotifier  # Slack通知クライアント

# ロギング設定
logging.basicConfig(  # ロギングの基本設定
    level=logging.INFO,  # INFOレベル以上を出力
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # ログフォーマット
    handlers=[  # ハンドラー設定
        logging.StreamHandler()  # コンソール出力
    ]
)
logger = logging.getLogger(__name__)  # このモジュール用のロガー


async def main():
    """メイン処理"""  # 関数の説明
    
    # .envファイルから環境変数を読み込み
    load_dotenv()  # .envファイルを読み込み
    
    # 環境変数を取得
    discord_token = os.getenv('DISCORD_BOT_TOKEN')  # Discord Botトークン
    sheet_name = os.getenv('GOOGLE_SHEET_NAME')  # スプレッドシート名
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')  # サービスアカウントJSON
    channel_ids = os.getenv('ALLOWED_VOICE_CHANNEL_IDS', '').split(',')  # 監視対象VCチャンネルID
    slack_token = os.getenv('SLACK_BOT_TOKEN')  # Slack Botトークン
    slack_channel = os.getenv('SLACK_CHANNEL_ID')  # Slackチャンネル ID
    
    # 必須環境変数のチェック
    if not discord_token:  # Discordトークンがない場合
        logger.error("DISCORD_BOT_TOKEN is not set")  # エラーログ出力
        sys.exit(1)  # 異常終了
    
    if not sheet_name:  # シート名がない場合
        logger.error("GOOGLE_SHEET_NAME is not set")  # エラーログ出力
        sys.exit(1)  # 異常終了
    
    if not channel_ids or channel_ids == ['']:  # チャンネルIDがない場合
        logger.error("ALLOWED_VOICE_CHANNEL_IDS is not set")  # エラーログ出力
        sys.exit(1)  # 異常終了
    
    # サービスアカウントJSONファイルの存在確認
    if not os.path.exists(service_account_json):  # JSONファイルが存在しない場合
        logger.error(f"Service account JSON file not found: {service_account_json}")  # エラーログ出力
        sys.exit(1)  # 異常終了
    
    try:
        # 1. Discord VCからメンバー情報を取得
        logger.info("Fetching VC members from Discord...")  # 処理開始ログ
        discord_client = DiscordVCPoller(discord_token, channel_ids)  # Discordクライアント作成
        vc_members = await discord_client.get_vc_members()  # VCメンバー取得
        
        if not vc_members:  # メンバーがいない場合
            logger.info("No members found in monitored VCs")  # メンバーなしログ
            return  # 処理終了
        
        logger.info(f"Found {len(vc_members)} members in VCs")  # メンバー数ログ
        
        # 2. Google Sheetsに記録
        logger.info("Connecting to Google Sheets...")  # 接続開始ログ
        sheets_client = SheetsClient(service_account_json, sheet_name)  # Sheetsクライアント作成
        sheets_client.connect()  # 接続
        
        logger.info("Recording presence data...")  # 記録開始ログ
        result = sheets_client.upsert_presence(vc_members)  # 出席データ記録
        logger.info(f"Recorded: {result['new']} new, {result['updated']} updated")  # 記録結果ログ
        
        # 3. Slack通知（設定されている場合）
        if slack_token and slack_channel:  # Slack設定がある場合
            logger.info("Sending Slack notifications...")  # 通知開始ログ
            slack_client = SlackNotifier(slack_token, slack_channel)  # Slackクライアント作成
            
            # 各メンバーの通算日数を取得して通知
            for member in vc_members:  # メンバーリストをループ
                total_days = sheets_client.get_total_days(member['user_id'])  # 通算日数取得
                
                # 新規ログインの場合のみ通知（今回新規追加されたメンバー）
                if result['new'] > 0:  # 新規メンバーがいる場合
                    success = slack_client.send_login_notification(  # ログイン通知送信
                        member['user_name'],  # ユーザー名
                        total_days  # 通算日数
                    )
                    if success:  # 送信成功の場合
                        logger.info(f"Notified: {member['user_name']} (Day {total_days})")  # 通知成功ログ
        else:
            logger.info("Slack notification skipped (not configured)")  # Slack設定なしログ
        
        logger.info("Poll completed successfully")  # 処理完了ログ
        
    except Exception as e:  # エラー発生時
        logger.error(f"Error during polling: {e}")  # エラーログ出力
        sys.exit(1)  # 異常終了


if __name__ == "__main__":  # スクリプト直接実行時
    asyncio.run(main())  # メイン処理を非同期実行