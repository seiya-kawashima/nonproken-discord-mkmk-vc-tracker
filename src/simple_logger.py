"""
シンプルな標準loggingの設定
GitHub Actions環境に最適化
"""

import logging  # 標準ライブラリのlogging
import os  # 環境変数取得用


def setup_logger(name: str = "app", level: str = None) -> logging.Logger:
    """
    シンプルなロガーをセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル（環境変数LOG_LEVELまたはデフォルトINFO）
    
    Returns:
        設定済みのloggerインスタンス
    """
    # 環境変数からログレベルを取得（CI環境対応）
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")  # 環境変数またはINFO
    
    # CI環境の検出
    is_ci = any([
        os.getenv("CI"),  # 汎用CI環境変数
        os.getenv("GITHUB_ACTIONS"),  # GitHub Actions
        os.getenv("JENKINS_URL"),  # Jenkins
        os.getenv("TRAVIS"),  # Travis CI
    ])
    
    # フォーマット設定（CI環境ではシンプルに）
    if is_ci:
        format_str = "%(levelname)s: %(message)s"  # CI用シンプルフォーマット
    else:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # ローカル用詳細フォーマット
    
    # 基本設定
    logging.basicConfig(
        level=getattr(logging, level.upper()),  # レベル設定
        format=format_str,  # フォーマット
        force=True  # 既存の設定を上書き
    )
    
    # ロガー取得
    logger = logging.getLogger(name)  # 名前付きロガー
    
    return logger  # ロガー返却


# デフォルトロガーのエクスポート
logger = setup_logger()  # デフォルトロガー作成


if __name__ == "__main__":
    # 使用例
    test_logger = setup_logger("test")  # テスト用ロガー
    
    test_logger.debug("デバッグメッセージ")  # DEBUG
    test_logger.info("情報メッセージ")  # INFO
    test_logger.warning("警告メッセージ")  # WARNING
    test_logger.error("エラーメッセージ")  # ERROR
    test_logger.critical("クリティカルメッセージ")  # CRITICAL