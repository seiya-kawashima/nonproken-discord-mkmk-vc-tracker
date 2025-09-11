# シンプルロガー (simple_logger.py) 仕様書

## 概要
標準の`logging`モジュールを使用したシンプルなロガー実装。
GitHub Actions環境とローカル開発環境の両方に対応。

## 特徴
- **軽量**: 64行のシンプルな実装
- **標準ライブラリのみ**: 追加パッケージ不要
- **CI/CD対応**: 環境を自動検出してフォーマット切り替え

## 関数仕様

### setup_logger()
```python
def setup_logger(name: str = "app", level: str = None) -> logging.Logger
```

#### パラメータ
| 名前 | 型 | デフォルト | 説明 |
|---|---|---|---|
| name | str | "app" | ロガー名 |
| level | str | None | ログレベル（None時は環境変数から取得） |

#### 返り値
- `logging.Logger`: 設定済みのロガーインスタンス

## ログレベル
Python標準の5段階：
- **DEBUG**: デバッグ情報
- **INFO**: 一般情報
- **WARNING**: 警告
- **ERROR**: エラー
- **CRITICAL**: 致命的エラー

## 環境判定

### CI環境の検出
以下の環境変数で判定：
- `CI`: 汎用CI環境変数
- `GITHUB_ACTIONS`: GitHub Actions
- `JENKINS_URL`: Jenkins
- `TRAVIS`: Travis CI

### フォーマット切り替え
| 環境 | フォーマット | 例 |
|---|---|---|
| CI環境 | `%(levelname)s: %(message)s` | `INFO: User logged in` |
| ローカル | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | `2025-09-11 10:00:00 - app - INFO - User logged in` |

## 使用例

### 基本的な使い方
```python
from src.simple_logger import logger

# デフォルトロガーを使用
logger.info("処理開始")
logger.error("エラー発生")
```

### カスタムロガー作成
```python
from src.simple_logger import setup_logger

# カスタム名とレベルで作成
my_logger = setup_logger("my_module", level="DEBUG")
my_logger.debug("デバッグ情報")
```

### 環境変数での制御
```bash
# 環境変数でログレベル設定
export LOG_LEVEL=DEBUG
python poll_once.py
```

## メリット

1. **シンプル**: 理解しやすく保守しやすい
2. **軽量**: 本番環境での負荷が最小限
3. **互換性**: Python標準loggingなので既存コードと統合しやすい
4. **CI/CD最適化**: GitHub Actionsでの見やすさを考慮

## デメリット

1. **機能限定**: 高度なログ機能（ローテーション等）なし
2. **カスタマイズ性**: 設定オプションが少ない

→ 本プロジェクトの要件では問題なし（GitHub Actionsで30分ごとの短時間実行）