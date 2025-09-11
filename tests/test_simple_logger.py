"""
標準loggingの簡単なテスト
"""

import pytest  # テストフレームワーク
import logging  # 標準logging
import os  # 環境変数


class TestStandardLogging:
    """標準loggingのテスト"""
    
    def test_logger_creation(self):
        """ロガー作成のテスト"""
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test")  # ロガー作成
        assert logger is not None  # ロガーが作成されたか確認
        assert logger.name == "test"  # 名前が正しいか確認
    
    def test_log_levels(self):
        """ログレベルのテスト"""
        logging.basicConfig(level=logging.DEBUG, force=True)
        logger = logging.getLogger("test_debug")  # DEBUGレベルで作成
        assert logging.getLogger().level == logging.DEBUG  # DEBUGレベルか確認
        
        logging.basicConfig(level=logging.ERROR, force=True)
        logger = logging.getLogger("test_error")  # ERRORレベルで作成
        assert logging.getLogger().level == logging.ERROR  # ERRORレベルか確認
    
    def test_info_logging(self):
        """INFOログのテスト（出力があることを確認）"""
        logger = setup_logger("test_info", level="INFO")  # INFOレベルで作成
        # ログ出力ができることを確認（エラーが出なければOK）
        try:
            logger.info("Test message")  # テストメッセージ
            success = True
        except Exception:
            success = False
        assert success  # エラーなく実行できたか確認
    
    def test_error_logging(self):
        """ERRORログのテスト（出力があることを確認）"""
        logger = setup_logger("test_error", level="INFO")  # INFOレベルで作成
        # ログ出力ができることを確認（エラーが出なければOK）
        try:
            logger.error("Error message")  # エラーメッセージ
            success = True
        except Exception:
            success = False
        assert success  # エラーなく実行できたか確認
    
    def test_ci_environment_detection(self, monkeypatch):
        """CI環境検出のテスト"""
        # CI環境をシミュレート
        monkeypatch.setenv("GITHUB_ACTIONS", "true")  # GitHub Actions環境変数
        logger = setup_logger("ci_test")  # CI環境でロガー作成
        assert logger is not None  # ロガーが作成されたか確認