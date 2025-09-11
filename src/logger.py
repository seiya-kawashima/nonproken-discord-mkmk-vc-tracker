"""
強力なロガークラスモジュール
開発時のデバッグ、本番環境での監視、トラブルシューティングに対応
6段階のログレベル: TRACE, DEBUG, INFO, WARN, ERROR, FATAL
"""

import logging
import sys
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union
from pathlib import Path
from logging.handlers import RotatingFileHandler
import traceback


# カスタムログレベルの定義
TRACE = 5  # 最も詳細なトレース情報
DEBUG = 10  # デバッグ情報（Python標準）
INFO = 20  # 一般情報（Python標準）
WARN = 30  # 警告（Python標準のWARNINGと同じ）
ERROR = 40  # エラー（Python標準）
FATAL = 50  # 致命的エラー（Python標準のCRITICALと同じ）

# ログレベルマッピング
LOG_LEVELS = {
    0: TRACE,  # 0: TRACE
    1: DEBUG,  # 1: DEBUG
    2: INFO,   # 2: INFO
    3: WARN,   # 3: WARN
    4: ERROR,  # 4: ERROR
    5: FATAL,  # 5: FATAL
}

# ログレベル名マッピング
LOG_LEVEL_NAMES = {
    TRACE: 'TRACE',
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARN: 'WARN',
    ERROR: 'ERROR',
    FATAL: 'FATAL',
}

# Pythonのloggingモジュールにカスタムレベルを追加
logging.addLevelName(TRACE, 'TRACE')
logging.addLevelName(WARN, 'WARN')
logging.addLevelName(FATAL, 'FATAL')


class ColoredFormatter(logging.Formatter):
    """
    カラー付きのコンソール出力用フォーマッター
    """
    
    # ANSIカラーコード定義（6段階対応）
    COLORS = {
        'TRACE': '\033[90m',     # 灰色
        'DEBUG': '\033[36m',     # シアン
        'INFO': '\033[32m',      # 緑
        'WARN': '\033[33m',      # 黄色
        'WARNING': '\033[33m',   # 黄色（互換性）
        'ERROR': '\033[31m',     # 赤
        'FATAL': '\033[35m',     # マゼンタ
        'CRITICAL': '\033[35m',  # マゼンタ（互換性）
        'RESET': '\033[0m'       # リセット
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをフォーマット"""
        # 元のレベル名を保存
        levelname = record.levelname
        
        # カラーコードを適用
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname:5}{self.COLORS['RESET']}"  # 5文字幅で揃える
        
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
            'level_no': record.levelno,                  # ログレベル番号
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
    6段階のログレベル対応: TRACE, DEBUG, INFO, WARN, ERROR, FATAL
    """
    
    def __init__(
        self,
        name: str = "vc_tracker",
        level: Union[int, str] = 2,  # デフォルトはINFO (2)
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
            level: ログレベル（0-5の整数、または 'TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'）
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
        
        # ログレベルの設定（整数または文字列対応）
        if isinstance(level, int):
            if 0 <= level <= 5:
                log_level = LOG_LEVELS[level]  # 0-5の整数をログレベルに変換
            else:
                log_level = INFO  # 範囲外はINFOにフォールバック
        else:
            # 文字列の場合
            level_map = {
                'TRACE': TRACE,
                'DEBUG': DEBUG,
                'INFO': INFO,
                'WARN': WARN,
                'WARNING': WARN,  # 互換性
                'ERROR': ERROR,
                'FATAL': FATAL,
                'CRITICAL': FATAL,  # 互換性
            }
            log_level = level_map.get(level.upper(), INFO)  # デフォルトはINFO
        
        self.logger.setLevel(log_level)  # ログレベル設定
        self.logger.handlers = []  # 既存のハンドラーをクリア
        self.current_level = log_level  # 現在のログレベルを保存
        
        # ログディレクトリの設定
        if log_dir is None:
            log_dir = Path("logs")  # デフォルトはlogsディレクトリ
        log_dir.mkdir(parents=True, exist_ok=True)  # ディレクトリ作成
        self.log_dir = log_dir
        
        # フォーマット定義
        console_format = "%(asctime)s [%(levelname)5s] %(name)s - %(funcName)s:%(lineno)d - %(message)s"
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
            
            # エラー専用ログファイル（ERROR以上）
            error_file = log_dir / f"{name}_error.log"
            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(ERROR)  # ERRORレベル以上のみ
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
    
    def set_level(self, level: Union[int, str]):
        """
        ログレベルを動的に変更
        
        Args:
            level: 0-5の整数、または 'TRACE', 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'
        """
        if isinstance(level, int):
            if 0 <= level <= 5:
                log_level = LOG_LEVELS[level]
            else:
                return  # 範囲外は無視
        else:
            level_map = {
                'TRACE': TRACE,
                'DEBUG': DEBUG,
                'INFO': INFO,
                'WARN': WARN,
                'WARNING': WARN,
                'ERROR': ERROR,
                'FATAL': FATAL,
                'CRITICAL': FATAL,
            }
            log_level = level_map.get(level.upper())
            if log_level is None:
                return  # 不正な文字列は無視
        
        self.logger.setLevel(log_level)
        self.current_level = log_level
    
    def trace(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """TRACEレベルのログ出力（最も詳細）"""
        self._log(TRACE, message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """DEBUGレベルのログ出力"""
        self._log(DEBUG, message, extra)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """INFOレベルのログ出力"""
        self._log(INFO, message, extra)
    
    def warn(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """WARNレベルのログ出力"""
        self._log(WARN, message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """WARNINGレベルのログ出力（warnのエイリアス）"""
        self.warn(message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """ERRORレベルのログ出力"""
        self._log(ERROR, message, extra, exc_info=exc_info)
    
    def fatal(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """FATALレベルのログ出力（致命的エラー）"""
        self._log(FATAL, message, extra, exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """CRITICALレベルのログ出力（fatalのエイリアス）"""
        self.fatal(message, extra, exc_info=exc_info)
    
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
            self.warn(f"⚠️ API呼び出し: {api_name} - {endpoint} (status: {status_code})", extra=api_data)
    
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
        level_env = os.getenv('LOG_LEVEL')
        if level_env:
            # 環境変数が整数の場合
            try:
                level = int(level_env)
            except ValueError:
                # 文字列の場合
                level = level_env
        else:
            level = kwargs.get('level', 2)  # デフォルトはINFO (2)
        
        enable_json = os.getenv('LOG_JSON', 'false').lower() == 'true'
        
        kwargs['level'] = level
        kwargs.setdefault('enable_json', enable_json)
        
        return cls(name=name, **kwargs)


# グローバルロガーインスタンス
logger = VCTrackerLogger.get_logger()


# 使用例とテスト
if __name__ == "__main__":
    # ロガー作成（整数レベル指定）
    test_logger = VCTrackerLogger.get_logger("test", level=0)  # TRACE (0)
    
    print("=" * 60)
    print("6段階ログレベルテスト（整数指定: level=0 でTRACE）")
    print("=" * 60)
    
    # 各レベルのログ出力テスト
    test_logger.trace("トレースメッセージ（最も詳細）")
    test_logger.debug("デバッグメッセージ")
    test_logger.info("情報メッセージ")
    test_logger.warn("警告メッセージ")
    test_logger.error("エラーメッセージ")
    test_logger.fatal("致命的エラーメッセージ")
    
    print("\n" + "=" * 60)
    print("ログレベル動的変更テスト")
    print("=" * 60)
    
    # レベルを3 (WARN) に変更
    test_logger.set_level(3)
    print("→ レベルを3 (WARN) に設定")
    
    test_logger.trace("このトレースは表示されない")
    test_logger.debug("このデバッグは表示されない")
    test_logger.info("この情報は表示されない")
    test_logger.warn("この警告は表示される")
    test_logger.error("このエラーは表示される")
    test_logger.fatal("この致命的エラーは表示される")
    
    print("\n" + "=" * 60)
    print("文字列でのレベル指定テスト")
    print("=" * 60)
    
    # 文字列でレベル指定
    test_logger2 = VCTrackerLogger.get_logger("test2", level="DEBUG")
    test_logger2.trace("トレースは表示されない（DEBUG以上）")
    test_logger2.debug("デバッグは表示される")
    test_logger2.info("情報は表示される")
    
    # 追加データ付きログ
    test_logger.info("ユーザーログイン", extra={
        "user_id": "123456",
        "user_name": "test_user",
        "ip": "192.168.1.1"
    })
    
    # 機密情報のマスキングテスト
    test_logger.info("接続情報: token='abc123def456' api_key='secret123'")
    
    # 例外のログ
    try:
        raise ValueError("テスト例外")
    except Exception:
        test_logger.exception("例外が発生しました")