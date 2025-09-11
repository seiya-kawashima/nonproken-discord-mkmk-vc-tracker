"""
simple_loggerの簡単なテスト
"""

import pytest  # テストフレームワーク
import logging  # 標準logging
import sys  # システム操作
from pathlib import Path  # パス操作

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from simple_logger import setup_logger  # テスト対象


class TestSimpleLogger:
    """シンプルロガーのテスト"""
    
    def test_logger_creation(self):
        """ロガー作成のテスト"""
        logger = setup_logger("test")  # ロガー作成
        assert logger is not None  # ロガーが作成されたか確認
        assert logger.name == "test"  # 名前が正しいか確認
    
    def test_log_levels(self):
        """ログレベルのテスト"""
        logger = setup_logger("test", level="DEBUG")  # DEBUGレベルで作成
        assert logger.level <= logging.DEBUG  # DEBUGレベル以下か確認
        
        logger = setup_logger("test2", level="ERROR")  # ERRORレベルで作成
        assert logger.level <= logging.ERROR  # ERRORレベル以下か確認
    
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