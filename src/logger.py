"""
強力なロガークラスモジュール
開発時のデバッグ、本番環境での監視、トラブルシューティングに対応
"""

import logging
import sys
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler
import traceback


class ColoredFormatter(logging.Formatter):
    """
    カラー付きのコンソール出力用フォーマッター
    """
    
    # ANSIカラーコード定義
    COLORS = {
        'DEBUG': '\033[36m',     # シアン
        'INFO': '\033[32m',      # 緑
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 赤
        'CRITICAL': '\033[35m',  # マゼンタ
        'RESET': '\033[0m'       # リセット
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをフォーマット"""
        # 元のレベル名を保存
        levelname = record.levelname
        
        # カラーコードを適用
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # 基底クラスのフォーマットを実行
        result = super().format(record)
        
        # レベル名を元に戻す
        record.levelname = levelname
        
        return result


class JSONFormatter(logging.Formatter):
    """
    JSON形式でログを出力するフォーマッター（構造化ログ）
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式でフォーマット"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),  # ISO形式のタイムスタンプ
            'level': record.levelname,                   # ログレベル
            'logger': record.name,                       # ロガー名
            'module': record.module,                     # モジュール名
            'function': record.funcName,                 # 関数名
            'line': record.lineno,                       # 行番号
            'message': record.getMessage(),              # メッセージ本文
            'thread': record.thread,                     # スレッドID
            'thread_name': record.threadName,            # スレッド名
            'process': record.process,                   # プロセスID
        }
        
        # エラーの場合は例外情報を追加
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,                    # 例外タイプ
                'message': str(record.exc_info[1]),                     # 例外メッセージ
                'traceback': traceback.format_exception(*record.exc_info)  # スタックトレース
            }
        
        # 追加のデータがある場合は含める
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)  # 日本語対応


class MaskingFormatter(logging.Formatter):
    """
    機密情報をマスキングするフォーマッター
    """
    
    # マスキング対象のパターン
    SENSITIVE_PATTERNS = [
        ('token', r'(token["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1***MASKED***\3'),  # トークン
        ('key', r'(api[_-]?key["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1***MASKED***\3'),  # APIキー
        ('password', r'(password["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1***MASKED***\3'),  # パスワード
        ('secret', r'(secret["\']?\s*[:=]\s*["\']?)([^"\']+)(["\']?)', r'\1***MASKED***\3'),  # シークレット
    ]
    
    def format(self, record: logging.LogRecord) -> str:
        """機密情報をマスキングしてフォーマット"""
        import re
        
        # 基底クラスでフォーマット
        message = super().format(record)
        
        # 機密情報をマスキング
        for name, pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        
        return message


class VCTrackerLogger:
    """
    Discord VC Tracker用の強力なロガークラス
    """
    
    def __init__(
        self,
        name: str = "vc_tracker",
        level: str = "INFO",
        log_dir: Optional[Path] = None,
        enable_file: bool = True,
        enable_console: bool = True,
        enable_json: bool = False,
        mask_sensitive: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        ロガーの初期化
        
        Args:
            name: ロガー名
            level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
            log_dir: ログファイルの保存ディレクトリ
            enable_file: ファイル出力を有効化
            enable_console: コンソール出力を有効化
            enable_json: JSON形式での出力を有効化
            mask_sensitive: 機密情報のマスキングを有効化
            max_file_size: ログファイルの最大サイズ（バイト）
            backup_count: 保持するバックアップファイル数
        """
        self.name = name  # ロガー名
        self.logger = logging.getLogger(name)  # ロガーインスタンス作成
        self.logger.setLevel(getattr(logging, level.upper()))  # ログレベル設定
        self.logger.handlers = []  # 既存のハンドラーをクリア
        
        # ログディレクトリの設定
        if log_dir is None:
            log_dir = Path("logs")  # デフォルトはlogsディレクトリ
        log_dir.mkdir(parents=True, exist_ok=True)  # ディレクトリ作成
        self.log_dir = log_dir
        
        # フォーマット定義
        console_format = "%(asctime)s [%(levelname)8s] %(name)s - %(funcName)s:%(lineno)d - %(message)s"
        file_format = "%(asctime)s [%(levelname)s] %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
        
        # コンソール出力の設定
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)  # 標準出力へ
            
            # カラー出力またはマスキングフォーマッター
            if mask_sensitive:
                base_formatter = ColoredFormatter(console_format)
                formatter = MaskingFormatter(console_format)
                formatter._style = base_formatter._style
            else:
                formatter = ColoredFormatter(console_format)
            
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # ファイル出力の設定
        if enable_file:
            # 通常ログファイル
            log_file = log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,  # 最大ファイルサイズ
                backupCount=backup_count,  # バックアップ数
                encoding='utf-8'  # UTF-8エンコーディング
            )
            
            # JSON形式またはテキスト形式
            if enable_json:
                formatter = JSONFormatter()
            elif mask_sensitive:
                formatter = MaskingFormatter(file_format)
            else:
                formatter = logging.Formatter(file_format)
            
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # エラー専用ログファイル
            error_file = log_dir / f"{name}_error.log"
            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)  # ERRORレベル以上のみ
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """DEBUGレベルのログ出力"""
        self._log(logging.DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """INFOレベルのログ出力"""
        self._log(logging.INFO, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """WARNINGレベルのログ出力"""
        self._log(logging.WARNING, message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """ERRORレベルのログ出力"""
        self._log(logging.ERROR, message, extra, exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """CRITICALレベルのログ出力"""
        self._log(logging.CRITICAL, message, extra, exc_info=exc_info)
    
    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """例外情報付きでERRORログ出力"""
        self.error(message, extra, exc_info=True)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """内部ログ出力メソッド"""
        if extra:
            # 追加データをログレコードに含める
            log_extra = {'extra_data': extra}
            self.logger.log(level, message, extra=log_extra, exc_info=exc_info)
        else:
            self.logger.log(level, message, exc_info=exc_info)
    
    def log_start(self, operation: str, **kwargs):
        """処理開始のログ（統一フォーマット）"""
        self.info(f"🚀 {operation} 開始", extra=kwargs)
    
    def log_success(self, operation: str, **kwargs):
        """処理成功のログ（統一フォーマット）"""
        self.info(f"✅ {operation} 成功", extra=kwargs)
    
    def log_failure(self, operation: str, error: Optional[Exception] = None, **kwargs):
        """処理失敗のログ（統一フォーマット）"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_message'] = str(error)
        self.error(f"❌ {operation} 失敗", extra=kwargs, exc_info=bool(error))
    
    def log_metric(self, metric_name: str, value: Any, unit: Optional[str] = None, **kwargs):
        """メトリクスのログ（監視用）"""
        metric_data = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            **kwargs
        }
        self.info(f"📊 メトリクス: {metric_name}={value}{unit or ''}", extra=metric_data)
    
    def log_api_call(self, api_name: str, endpoint: str, status_code: Optional[int] = None, **kwargs):
        """API呼び出しのログ"""
        api_data = {
            'api': api_name,
            'endpoint': endpoint,
            'status_code': status_code,
            **kwargs
        }
        if status_code and 200 <= status_code < 300:
            self.info(f"🌐 API呼び出し成功: {api_name} - {endpoint}", extra=api_data)
        else:
            self.warning(f"⚠️ API呼び出し: {api_name} - {endpoint} (status: {status_code})", extra=api_data)
    
    @classmethod
    def get_logger(cls, name: str = "vc_tracker", **kwargs) -> 'VCTrackerLogger':
        """
        シングルトンパターンでロガーインスタンスを取得
        
        Args:
            name: ロガー名
            **kwargs: VCTrackerLoggerの初期化パラメータ
        
        Returns:
            VCTrackerLoggerインスタンス
        """
        # 環境変数からデフォルト値を取得
        level = os.getenv('LOG_LEVEL', kwargs.get('level', 'INFO'))
        enable_json = os.getenv('LOG_JSON', 'false').lower() == 'true'
        
        kwargs['level'] = level
        kwargs.setdefault('enable_json', enable_json)
        
        return cls(name=name, **kwargs)


# グローバルロガーインスタンス
logger = VCTrackerLogger.get_logger()


# 使用例とテスト
if __name__ == "__main__":
    # ロガー作成
    test_logger = VCTrackerLogger.get_logger("test", level="DEBUG")
    
    # 各レベルのログ出力テスト
    test_logger.debug("デバッグメッセージ")
    test_logger.info("情報メッセージ")
    test_logger.warning("警告メッセージ")
    test_logger.error("エラーメッセージ")
    test_logger.critical("重大エラーメッセージ")
    
    # 追加データ付きログ
    test_logger.info("ユーザーログイン", extra={
        "user_id": "123456",
        "user_name": "test_user",
        "ip": "192.168.1.1"
    })
    
    # 機密情報のマスキングテスト
    test_logger.info("接続情報: token='abc123def456' api_key='secret123'")
    
    # 処理フローのログ
    test_logger.log_start("VC監視処理")
    test_logger.log_success("VC監視処理", processed=10, duration=1.23)
    
    # メトリクスログ
    test_logger.log_metric("active_users", 42, "users")
    
    # API呼び出しログ
    test_logger.log_api_call("Discord", "/guilds/123/channels", 200)
    
    # 例外のログ
    try:
        raise ValueError("テスト例外")
    except Exception:
        test_logger.exception("例外が発生しました")