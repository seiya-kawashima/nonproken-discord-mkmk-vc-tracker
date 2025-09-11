# ロガークラス (logger.py) 仕様書

## 概要
Discord VC Trackerプロジェクト用の強力なロガークラス。開発時のデバッグ、本番環境での監視、トラブルシューティングを支援する包括的なログ機能を提供。

## 主要機能

### 1. 多様な出力形式
- **コンソール出力**: カラー付きで視覚的に分かりやすい
- **ファイル出力**: ローテーション機能付き
- **JSON出力**: 構造化ログで解析しやすい
- **エラー専用ログ**: エラー以上のレベルを別ファイルに記録

### 2. セキュリティ機能
- **機密情報マスキング**: トークン、APIキー、パスワードを自動マスク
- **マスキング対象**:
  - token
  - api_key
  - password
  - secret

### 3. 開発支援機能
- **カラー出力**: ログレベルごとに色分け
  - DEBUG: シアン
  - INFO: 緑
  - WARNING: 黄色
  - ERROR: 赤
  - CRITICAL: マゼンタ
- **詳細情報**: モジュール名、関数名、行番号を自動記録
- **スタックトレース**: 例外発生時の完全なトレースバック

### 4. 運用支援機能
- **ログローテーション**: ファイルサイズ制限（デフォルト10MB）
- **バックアップ**: 古いログの自動アーカイブ（デフォルト5世代）
- **メトリクスログ**: パフォーマンス計測用
- **API呼び出しログ**: 外部API連携の監視

## クラス構成

### VCTrackerLogger
メインのロガークラス

#### 初期化パラメータ
| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| name | str | "vc_tracker" | ロガー名 |
| level | str | "INFO" | ログレベル |
| log_dir | Path | "logs" | ログ保存ディレクトリ |
| enable_file | bool | True | ファイル出力有効化 |
| enable_console | bool | True | コンソール出力有効化 |
| enable_json | bool | False | JSON形式出力 |
| mask_sensitive | bool | True | 機密情報マスキング |
| max_file_size | int | 10MB | ログファイル最大サイズ |
| backup_count | int | 5 | バックアップ世代数 |

#### 主要メソッド

##### 基本ログメソッド
```python
debug(message: str, extra: Optional[Dict] = None)
info(message: str, extra: Optional[Dict] = None)
warning(message: str, extra: Optional[Dict] = None)
error(message: str, extra: Optional[Dict] = None, exc_info: bool = False)
critical(message: str, extra: Optional[Dict] = None, exc_info: bool = False)
exception(message: str, extra: Optional[Dict] = None)
```

##### 専用ログメソッド
```python
log_start(operation: str, **kwargs)      # 処理開始
log_success(operation: str, **kwargs)    # 処理成功
log_failure(operation: str, error: Optional[Exception] = None, **kwargs)  # 処理失敗
log_metric(metric_name: str, value: Any, unit: Optional[str] = None, **kwargs)  # メトリクス
log_api_call(api_name: str, endpoint: str, status_code: Optional[int] = None, **kwargs)  # API呼び出し
```

### ColoredFormatter
コンソール出力用のカラーフォーマッター

### JSONFormatter
構造化ログ用のJSONフォーマッター

### MaskingFormatter
機密情報をマスキングするフォーマッター

## 使用例

### 基本的な使い方
```python
from src.logger import VCTrackerLogger

# ロガー取得
logger = VCTrackerLogger.get_logger("my_module")

# 各レベルのログ
logger.debug("デバッグ情報")
logger.info("処理完了")
logger.warning("リトライ実行")
logger.error("接続失敗")
```

### 処理フローのログ
```python
# 処理開始
logger.log_start("VC監視処理", target_channels=3)

try:
    # 処理実行
    result = process_vc_members()
    
    # 成功ログ
    logger.log_success("VC監視処理", 
                      processed=result.count,
                      duration=result.duration)
except Exception as e:
    # 失敗ログ
    logger.log_failure("VC監視処理", error=e)
```

### メトリクスとAPI呼び出し
```python
# メトリクス記録
logger.log_metric("active_users", 42, "users")
logger.log_metric("response_time", 123.45, "ms")

# API呼び出し記録
logger.log_api_call("Discord", "/guilds/123/channels", 200)
logger.log_api_call("Slack", "/chat.postMessage", 429, retry_after=60)
```

### 追加データ付きログ
```python
logger.info("ユーザーログイン検出", extra={
    "user_id": "123456789",
    "user_name": "test_user",
    "channel_id": "987654321",
    "guild_id": "111111111"
})
```

## ログファイル構成

```
logs/
├── vc_tracker.log         # 通常ログ（全レベル）
├── vc_tracker.log.1       # ローテーションされた古いログ
├── vc_tracker.log.2
├── vc_tracker_error.log   # エラー専用ログ
└── vc_tracker_error.log.1
```

## 環境変数

| 変数名 | 説明 | 例 |
|---|---|---|
| LOG_LEVEL | デフォルトログレベル | DEBUG, INFO, WARNING, ERROR |
| LOG_JSON | JSON形式出力の有効化 | true, false |

## ログフォーマット

### コンソール出力
```
2025-09-11 10:30:15,123 [    INFO] vc_tracker - poll_vc:45 - VC監視処理開始
```

### ファイル出力（テキスト）
```
2025-09-11 10:30:15,123 [INFO] vc_tracker - discord_client.poll_vc:45 - VC監視処理開始
```

### JSON出力
```json
{
  "timestamp": "2025-09-11T01:30:15.123456",
  "level": "INFO",
  "logger": "vc_tracker",
  "module": "discord_client",
  "function": "poll_vc",
  "line": 45,
  "message": "VC監視処理開始",
  "thread": 12345,
  "thread_name": "MainThread",
  "process": 67890
}
```

## エラーハンドリング

### 例外ログの自動記録
```python
try:
    risky_operation()
except Exception:
    logger.exception("処理中にエラーが発生")
    # 自動的にスタックトレースが記録される
```

### マスキング例
入力:
```
logger.info("Connection: token='abc123' api_key='secret'")
```

出力:
```
Connection: token='***MASKED***' api_key='***MASKED***'
```

## パフォーマンス考慮事項

1. **ログレベル**: 本番環境ではINFO以上を推奨
2. **ファイルサイズ**: 10MBでローテーション
3. **バックアップ**: 5世代まで保持
4. **非同期処理**: 大量ログ時は別スレッドでの処理を検討

## 拡張性

### カスタムフォーマッター追加
```python
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # カスタムフォーマット処理
        return super().format(record)
```

### カスタムハンドラー追加
```python
# Slackへの通知ハンドラーなど
custom_handler = SlackHandler()
logger.logger.addHandler(custom_handler)
```

## トラブルシューティング

### ログが出力されない
1. ログレベルの確認
2. ハンドラーの有効化確認
3. ログディレクトリの権限確認

### ファイルが大きくなりすぎる
- max_file_sizeを調整
- backup_countを調整
- ログレベルを上げる

### 機密情報が漏れる
- mask_sensitive=Trueを確認
- カスタムパターンを追加