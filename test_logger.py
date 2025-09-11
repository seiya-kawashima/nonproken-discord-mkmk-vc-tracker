"""
ロガークラスのテストスクリプト
実際にログファイルを出力して動作確認
"""

from src.logger import VCTrackerLogger
import time
import random

def test_basic_logging():
    """基本的なログ出力テスト"""
    logger = VCTrackerLogger.get_logger("test_basic", level="DEBUG")
    
    print("=" * 60)
    print("基本ログレベルテスト")
    print("=" * 60)
    
    # 各レベルのログ出力
    logger.debug("🔍 デバッグ: プログラムの詳細な動作情報")
    logger.info("ℹ️ 情報: 正常な処理の進行状況")
    logger.warning("⚠️ 警告: 注意が必要な状況")
    logger.error("❌ エラー: エラーが発生したが処理は継続")
    logger.critical("🚨 重大: システムに重大な問題が発生")
    
    print("\n✅ 基本ログ出力完了")

def test_structured_logging():
    """構造化ログのテスト"""
    logger = VCTrackerLogger.get_logger("test_structured", enable_json=True)
    
    print("\n" + "=" * 60)
    print("構造化ログテスト（JSON形式）")
    print("=" * 60)
    
    # ユーザー情報付きログ
    logger.info("ユーザーがVCに参加", extra={
        "user_id": "123456789012345678",
        "user_name": "test_user#1234",
        "channel_id": "987654321098765432",
        "channel_name": "一般VC",
        "guild_id": "111111111111111111",
        "guild_name": "テストサーバー"
    })
    
    print("✅ JSON形式のログ出力完了")

def test_sensitive_masking():
    """機密情報マスキングのテスト"""
    logger = VCTrackerLogger.get_logger("test_masking")
    
    print("\n" + "=" * 60)
    print("機密情報マスキングテスト")
    print("=" * 60)
    
    # マスキング対象の情報を含むログ
    logger.info("Discord接続情報: token='MTA1234567890.GYh8Xw.abcdefghijklmnop' server='discord.gg'")
    logger.info("API設定: api_key='sk-proj-abcdef123456' endpoint='https://api.example.com'")
    logger.info("認証情報: password='super_secret_password' username='admin'")
    logger.info("環境変数: SECRET='my_secret_value' PUBLIC='this_is_public'")
    
    print("✅ 機密情報は自動的にマスキングされます")

def test_operation_flow():
    """処理フローのログテスト"""
    logger = VCTrackerLogger.get_logger("test_operation")
    
    print("\n" + "=" * 60)
    print("処理フローログテスト")
    print("=" * 60)
    
    # VC監視処理のシミュレーション
    operation = "VC監視処理"
    
    # 処理開始
    logger.log_start(operation, 
                    target_channels=3,
                    interval_seconds=30)
    
    # 処理中のログ
    time.sleep(0.5)  # 処理のシミュレーション
    detected_users = random.randint(5, 15)
    
    if detected_users > 10:
        logger.warning(f"多数のユーザーを検出: {detected_users}名")
    else:
        logger.info(f"ユーザーを検出: {detected_users}名")
    
    # メトリクス記録
    logger.log_metric("detected_users", detected_users, "users")
    logger.log_metric("processing_time", 523.45, "ms")
    logger.log_metric("memory_usage", 45.2, "MB")
    
    # 処理成功
    logger.log_success(operation,
                      processed=detected_users,
                      duration=0.523,
                      new_users=3)
    
    print("✅ 処理フローログ出力完了")

def test_api_logging():
    """API呼び出しログのテスト"""
    logger = VCTrackerLogger.get_logger("test_api")
    
    print("\n" + "=" * 60)
    print("API呼び出しログテスト")
    print("=" * 60)
    
    # Discord API呼び出し
    logger.log_api_call("Discord", "/guilds/123/channels", 200,
                       response_time=45.3,
                       rate_limit_remaining=4995)
    
    # Google Sheets API呼び出し
    logger.log_api_call("GoogleSheets", "/spreadsheets/abc123/values/A1:E100", 200,
                       rows_updated=5)
    
    # Slack API呼び出し（エラー）
    logger.log_api_call("Slack", "/chat.postMessage", 429,
                       error="rate_limited",
                       retry_after=60)
    
    print("✅ API呼び出しログ出力完了")

def test_exception_logging():
    """例外ログのテスト"""
    logger = VCTrackerLogger.get_logger("test_exception")
    
    print("\n" + "=" * 60)
    print("例外ログテスト")
    print("=" * 60)
    
    try:
        # 意図的に例外を発生させる
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.exception("計算処理でエラーが発生しました")
        logger.log_failure("数値計算処理", error=e,
                         input_value=10,
                         calc_operation="division")
    
    try:
        # 別の例外
        data = {"key": "value"}
        value = data["missing_key"]
    except KeyError as e:
        logger.error("データアクセスエラー", exc_info=True)
    
    print("✅ 例外ログ出力完了（スタックトレース付き）")

def test_performance_simulation():
    """パフォーマンス監視のシミュレーション"""
    logger = VCTrackerLogger.get_logger("test_performance")
    
    print("\n" + "=" * 60)
    print("パフォーマンス監視シミュレーション")
    print("=" * 60)
    
    # 5回の処理をシミュレート
    for i in range(5):
        start_time = time.time()
        
        # 処理のシミュレーション
        logger.debug(f"処理 {i+1}/5 開始")
        time.sleep(random.uniform(0.1, 0.3))
        
        # 処理時間計測
        duration = (time.time() - start_time) * 1000  # ミリ秒
        
        # パフォーマンスメトリクス
        logger.log_metric(f"process_{i+1}_duration", round(duration, 2), "ms")
        
        if duration > 200:
            logger.warning(f"処理 {i+1} が遅延: {duration:.2f}ms")
        else:
            logger.debug(f"処理 {i+1} 完了: {duration:.2f}ms")
    
    print("✅ パフォーマンス監視ログ出力完了")

def check_log_files():
    """生成されたログファイルの確認"""
    import os
    from pathlib import Path
    
    print("\n" + "=" * 60)
    print("📁 生成されたログファイル")
    print("=" * 60)
    
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        for log_file in sorted(log_files):
            size = os.path.getsize(log_file)
            print(f"  ✓ {log_file.name:<30} ({size:,} bytes)")
    else:
        print("  ⚠️ logsディレクトリが見つかりません")
    
    print("\n💡 ヒント: logsディレクトリ内のファイルを確認してください")
    print("   - 通常ログ: test_*.log")
    print("   - エラーログ: test_*_error.log")
    print("   - JSON形式: test_structured.log")

def main():
    """メイン処理"""
    print("\n" + "🚀 VC Tracker ロガーテスト開始 🚀".center(60))
    print("=" * 60)
    
    # 各種テスト実行
    test_basic_logging()
    test_structured_logging()
    test_sensitive_masking()
    test_operation_flow()
    test_api_logging()
    test_exception_logging()
    test_performance_simulation()
    
    # ログファイル確認
    check_log_files()
    
    print("\n" + "=" * 60)
    print("🎉 すべてのテスト完了！".center(60))
    print("=" * 60)
    print("\n📝 注意事項:")
    print("  1. logsディレクトリにログファイルが生成されています")
    print("  2. 機密情報は自動的にマスキングされています")
    print("  3. エラーログは別ファイルに記録されています")
    print("  4. JSON形式のログは構造化データとして解析可能です")

if __name__ == "__main__":
    main()