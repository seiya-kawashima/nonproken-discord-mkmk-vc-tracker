# ログ設定ガイド

## 概要
このプロジェクトではPython標準の`logging`モジュールを使用します。
追加のロガーライブラリは不要です。

## 基本的な使い方

### シンプルな設定
```python
import logging
import os

# 環境変数からログレベルを取得（デフォルトはINFO）
log_level = os.getenv('LOG_LEVEL', 'INFO')

# ログ設定
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ロガー取得
logger = logging.getLogger(__name__)

# 使用例
logger.info("処理開始")
logger.error("エラー発生")
```

## 各モジュールでの使い方

### discord_client.py
```python
import logging

logger = logging.getLogger(__name__)

class DiscordVCPoller:
    def __init__(self):
        logger.info("Discord Bot初期化")
    
    async def get_vc_members(self):
        logger.debug("VCメンバー取得開始")
        # 処理
        logger.info(f"VCメンバー{len(members)}名を検出")
```

### sheets_client.py
```python
import logging

logger = logging.getLogger(__name__)

class SheetsClient:
    def upsert_presence(self, data):
        logger.info(f"Sheetsに{len(data)}件のデータを書き込み")
        try:
            # 処理
            logger.debug("書き込み成功")
        except Exception as e:
            logger.error(f"Sheets書き込みエラー: {e}")
```

## メインスクリプト（poll_once.py）での設定

```python
import logging
import os

def setup_logging():
    """ログ設定の初期化"""
    # 環境変数からログレベル取得
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # CI環境の検出
    is_ci = os.getenv('GITHUB_ACTIONS') == 'true'
    
    # フォーマット設定
    if is_ci:
        # CI環境：シンプルなフォーマット
        log_format = '%(levelname)s: %(message)s'
    else:
        # ローカル環境：詳細なフォーマット
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 設定適用
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        force=True  # 既存の設定を上書き
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("VC Tracker起動")
    # メイン処理
```

## ログレベル

| レベル | 数値 | 使用場面 |
|---|---|---|
| DEBUG | 10 | 詳細なデバッグ情報 |
| INFO | 20 | 通常の処理フロー |
| WARNING | 30 | 警告（処理は継続） |
| ERROR | 40 | エラー（復旧可能） |
| CRITICAL | 50 | 致命的エラー |

## 環境変数

### LOG_LEVEL
ログレベルを制御します。

```bash
# ローカル開発
export LOG_LEVEL=DEBUG

# 本番環境
export LOG_LEVEL=INFO

# エラーのみ
export LOG_LEVEL=ERROR
```

## GitHub Actions での設定

### ワークフロー例
```yaml
- name: Run poll script
  env:
    LOG_LEVEL: INFO
  run: python poll_once.py
```

## ベストプラクティス

### 1. 適切なログレベルの使用
```python
logger.debug(f"変数の値: {variable}")  # デバッグ時のみ
logger.info("処理完了")                # 正常フロー
logger.warning("リトライ実行")         # 注意が必要
logger.error("API接続失敗", exc_info=True)  # エラー情報
```

### 2. 構造化された情報
```python
# Good
logger.info(f"ユーザー検出: user_id={user_id}, channel_id={channel_id}")

# Better（辞書形式で後から解析しやすい）
logger.info("ユーザー検出", extra={
    "user_id": user_id,
    "channel_id": channel_id
})
```

### 3. エラー時の詳細情報
```python
try:
    risky_operation()
except Exception as e:
    logger.error("処理失敗", exc_info=True)  # スタックトレース付き
```

### 4. 機密情報の扱い
```python
# Bad
logger.info(f"Token: {token}")

# Good
logger.info("認証成功")  # トークンは出力しない
```

## なぜカスタムロガーを使わないのか

1. **シンプルさ**: 標準loggingで十分な機能
2. **保守性**: 追加コード不要
3. **互換性**: 他のライブラリと統合しやすい
4. **学習コスト**: Pythonエンジニアなら誰でも知っている
5. **軽量**: 追加依存なし

## トラブルシューティング

### ログが出力されない
```python
# ルートロガーのレベルを確認
print(logging.getLogger().level)

# 強制的に設定を上書き
logging.basicConfig(level=logging.DEBUG, force=True)
```

### 複数回basicConfigを呼んでも反映されない
```python
# force=Trueを使用
logging.basicConfig(level=logging.INFO, force=True)
```

### テスト時のログ抑制
```python
# pytest実行時
pytest --log-cli-level=ERROR  # ERRORレベル以上のみ表示
```