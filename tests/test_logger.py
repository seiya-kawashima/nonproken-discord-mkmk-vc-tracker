import pytest  # テストフレームワーク
import os  # OS操作用
import sys  # システムパス操作用
from pathlib import Path  # パス操作用
from unittest.mock import patch, MagicMock  # モック用

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from logger import VCTrackerLogger  # テスト対象のloggerクラス


class TestLogger:
    """loggerクラスのテストスイート"""
    
    def test_logger_initialization(self):
        """ロガーの初期化テスト"""
        test_logger = VCTrackerLogger("test_module")  # テスト用ロガーを作成
        assert test_logger.name == "test_module"  # 名前が正しく設定されているか確認
        assert test_logger.logger is not None  # ロガーインスタンスが作成されているか確認
    
    def test_debug_logging(self, caplog):
        """デバッグログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("DEBUG"):  # DEBUGレベルでログをキャプチャ
            test_logger.debug("Debug message")  # デバッグメッセージをログ出力
        assert "Debug message" in caplog.text  # メッセージがログに含まれているか確認
    
    def test_info_logging(self, caplog):
        """情報ログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("INFO"):  # INFOレベルでログをキャプチャ
            test_logger.info("Info message")  # 情報メッセージをログ出力
        assert "Info message" in caplog.text  # メッセージがログに含まれているか確認
    
    def test_warning_logging(self, caplog):
        """警告ログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("WARNING"):  # WARNINGレベルでログをキャプチャ
            test_logger.warning("Warning message")  # 警告メッセージをログ出力
        assert "Warning message" in caplog.text  # メッセージがログに含まれているか確認
    
    def test_error_logging(self, caplog):
        """エラーログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("ERROR"):  # ERRORレベルでログをキャプチャ
            test_logger.error("Error message")  # エラーメッセージをログ出力
        assert "Error message" in caplog.text  # メッセージがログに含まれているか確認
    
    def test_critical_logging(self, caplog):
        """クリティカルログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("CRITICAL"):  # CRITICALレベルでログをキャプチャ
            test_logger.critical("Critical message")  # クリティカルメッセージをログ出力
        assert "Critical message" in caplog.text  # メッセージがログに含まれているか確認
    
    def test_log_with_extra_params(self, caplog):
        """追加パラメータ付きログのテスト"""
        test_logger = VCTrackerLogger("test")  # テスト用ロガーを作成
        with caplog.at_level("INFO"):  # INFOレベルでログをキャプチャ
            test_logger.info("Message with %s", "parameter")  # パラメータ付きメッセージをログ出力
        assert "Message with parameter" in caplog.text  # フォーマットされたメッセージが含まれているか確認
    
    @patch('logger.logging.FileHandler')
    def test_file_handler_creation(self, mock_file_handler):
        """ファイルハンドラー作成のテスト"""
        test_logger = VCTrackerLogger("test", log_file="test.log")  # ファイル出力付きロガーを作成
        mock_file_handler.assert_called()  # FileHandlerが呼ばれたか確認
    
    def test_logger_level_setting(self):
        """ログレベル設定のテスト"""
        test_logger = VCTrackerLogger("test", level="WARNING")  # WARNINGレベルでロガーを作成
        assert test_logger.logger.level == 30  # WARNING = 30であることを確認