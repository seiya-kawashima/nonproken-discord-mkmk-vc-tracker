# テスト仕様書

## 1. 概要

本仕様書は、Discord VC Trackerシステムの品質保証のためのテスト戦略、テストケース、カバレッジ目標を定義します。

### 1.1 テスト目的
- コードの品質保証
- リグレッションの防止
- 仕様への適合性確認
- 継続的インテグレーション（CI）の実現

### 1.2 テストスコープ
- 単体テスト（Unit Tests）
- 統合テスト（Integration Tests）
- カバレッジ測定
- CI/CDパイプライン

## 2. テストフレームワーク

### 2.1 使用ツール
| ツール | バージョン | 用途 |
|---|---|---|
| pytest | 8.3+ | テストフレームワーク |
| pytest-asyncio | 1.1+ | 非同期テストサポート |
| pytest-cov | 6.1+ | カバレッジ測定 |
| coverage | 7.0+ | カバレッジレポート |
| unittest.mock | 標準ライブラリ | モッキング |

### 2.2 ディレクトリ構造
```
tests/
├── __init__.py
├── test_discord_client.py         # Discord Botクライアントのテスト
├── test_discord_client_additional.py  # 追加テスト
├── test_sheets_client.py          # Google Sheetsクライアントのテスト
├── test_slack_notifier.py         # Slack通知クライアントのテスト
└── test_poll_once.py              # メイン処理のテスト
```

## 3. テストカバレッジ目標

### 3.1 全体目標
- **最小カバレッジ**: 83%
- **推奨カバレッジ**: 85%
- **理想カバレッジ**: 90%

### 3.2 モジュール別目標
| モジュール | 現在 | 目標 | 備考 |
|---|---|---|---|
| poll_once.py | 90.91% | 90% | 達成済み |
| src/discord_client.py | 64.00% | 70% | 非同期処理のため困難 |
| src/sheets_client.py | 92.86% | 90% | 達成済み |
| src/slack_notifier.py | 79.45% | 80% | ほぼ達成 |

### 3.3 カバレッジ除外項目
- Discord APIの実際の接続部分（モックで代替）
- エラーハンドリングの一部（外部要因）
- メインブロック（`if __name__ == "__main__"`）

## 4. Discord Botクライアントテスト

### 4.1 テストクラス: TestDiscordVCPoller

#### 4.1.1 test_init
**目的**: 初期化処理の検証
**検証項目**:
- トークンとチャンネルIDの正しい設定
- Intentsの適切な設定
- 初期状態の確認

#### 4.1.2 test_get_vc_members_success
**目的**: 正常なVCメンバー取得
**モック対象**:
- Discord Client
- Guild、Channel、Member オブジェクト
**検証項目**:
- メンバー情報の正確な取得
- データ形式の確認

#### 4.1.3 test_get_vc_members_no_members
**目的**: VCが空の場合の処理
**検証項目**:
- 空リストの返却
- エラーが発生しないこと

#### 4.1.4 test_get_vc_members_not_monitored_channel
**目的**: 監視対象外チャンネルの除外
**検証項目**:
- 対象外チャンネルのメンバーを含まない
- フィルタリングの正確性

#### 4.1.5 test_context_manager
**目的**: 非同期コンテキストマネージャーの動作
**検証項目**:
- `__aenter__`と`__aexit__`の正常動作
- リソースのクリーンアップ

### 4.2 追加テストクラス: TestDiscordVCPollerAdditional

#### 4.2.1 test_get_vc_members_with_error
**目的**: エラーハンドリングの検証
**検証項目**:
- 例外の適切な伝播
- エラーログの出力

#### 4.2.2 test_get_vc_members_multiple_guilds
**目的**: 複数サーバーの処理
**検証項目**:
- 複数ギルドからのメンバー取得
- データの統合

#### 4.2.3 test_get_vc_members_with_logging
**目的**: ログ出力の検証
**検証項目**:
- 適切なログメッセージ
- ログレベルの確認

## 5. Google Sheetsクライアントテスト

### 5.1 テストクラス: TestSheetsClient

#### 5.1.1 test_init
**目的**: 初期化処理の検証
**検証項目**:
- パラメータの保存
- 初期状態の確認

#### 5.1.2 test_connect_success
**目的**: 正常な接続処理
**モック対象**:
- gspread.authorize
- Credentials
**検証項目**:
- 認証処理の実行
- ワークシートの取得

#### 5.1.3 test_connect_create_worksheet
**目的**: ワークシート自動作成
**検証項目**:
- ワークシートが存在しない場合の作成
- ヘッダー行の設定

#### 5.1.4 test_upsert_presence_not_connected
**目的**: 未接続時のエラー処理
**検証項目**:
- RuntimeErrorの発生
- 適切なエラーメッセージ

#### 5.1.5 test_upsert_presence_new_records
**目的**: 新規レコードの追加
**モック対象**:
- datetime（日付固定）
- worksheet.append_rows
**検証項目**:
- 新規データの正確な追加
- 戻り値の確認

#### 5.1.6 test_upsert_presence_existing_records
**目的**: 既存レコードの処理
**検証項目**:
- 重複データの除外
- 更新カウントの正確性

#### 5.1.7 test_get_total_days_success
**目的**: 通算日数の計算
**検証項目**:
- 正確なカウント
- フィルタリングの動作

#### 5.1.8 test_get_today_members_success
**目的**: 今日のメンバー取得
**モック対象**:
- datetime（今日の日付）
**検証項目**:
- 日付フィルタリング
- データ形式の確認

## 6. Slack通知クライアントテスト

### 6.1 テストクラス: TestSlackNotifier

#### 6.1.1 test_init
**目的**: 初期化処理の検証
**検証項目**:
- パラメータの保存
- WebClientの作成

#### 6.1.2 test_send_login_notification_normal
**目的**: 通常のログイン通知
**モック対象**:
- WebClient.chat_postMessage
**検証項目**:
- メッセージフォーマット
- API呼び出しパラメータ

#### 6.1.3 test_send_login_notification_milestone
**目的**: 節目（100日）の通知
**検証項目**:
- 特別メッセージフォーマット
- 絵文字の使い分け

#### 6.1.4 test_send_login_notification_api_error
**目的**: APIエラーのハンドリング
**検証項目**:
- SlackApiErrorの処理
- Falseの返却

#### 6.1.5 test_send_daily_summary_no_members
**目的**: メンバーなしのサマリー
**検証項目**:
- 適切なメッセージ
- エラーなし

#### 6.1.6 test_send_daily_summary_with_members
**目的**: メンバーありのサマリー
**検証項目**:
- メンバーリストの表示
- フォーマットの確認

#### 6.1.7 test_send_daily_summary_many_members
**目的**: 多数メンバーの処理
**検証項目**:
- 10名制限の動作
- "他X名"の表示

#### 6.1.8 test_test_connection_success
**目的**: 接続テストの成功
**モック対象**:
- WebClient.auth_test
**検証項目**:
- 認証テストの実行
- Trueの返却

## 7. メイン処理テスト

### 7.1 テストクラス: TestPollOnce

#### 7.1.1 test_main_success
**目的**: 正常な全体フロー
**モック対象**:
- 全モジュール
- 環境変数
**検証項目**:
- 各モジュールの呼び出し順序
- データの受け渡し

#### 7.1.2 test_main_no_discord_token
**目的**: Discordトークン未設定
**検証項目**:
- sys.exit(1)の呼び出し
- エラーログ

#### 7.1.3 test_main_no_sheet_name
**目的**: シート名未設定
**検証項目**:
- sys.exit(1)の呼び出し
- エラーログ

#### 7.1.4 test_main_no_members
**目的**: VCメンバーなし
**検証項目**:
- 正常終了
- Sheets/Slackのスキップ

#### 7.1.5 test_main_exception
**目的**: 例外処理
**検証項目**:
- 例外のキャッチ
- sys.exit(1)の呼び出し

## 8. モッキング戦略

### 8.1 外部依存のモック
- **Discord API**: Client、Guild、Channel、Member
- **Google Sheets API**: gspread、Credentials
- **Slack API**: WebClient
- **日時**: datetime.now()
- **ファイルシステム**: os.path.exists()

### 8.2 モックの原則
1. 外部APIは必ずモック
2. 副作用のある操作はモック
3. 決定的でない値はモック（日時など）
4. 内部ロジックはモックしない

### 8.3 AsyncMockの使用
```python
from unittest.mock import AsyncMock

mock_client.start = AsyncMock()
mock_client.close = AsyncMock()
```

## 9. テスト実行

### 9.1 ローカル実行
```bash
# 全テスト実行
pytest tests/

# カバレッジ付き実行
pytest --cov=src --cov=poll_once tests/

# 詳細なカバレッジレポート
pytest --cov=src --cov-report=html tests/

# 特定のテストのみ
pytest tests/test_discord_client.py
```

### 9.2 CI/CD実行（GitHub Actions）
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=src --cov-report=xml --cov-report=html --cov-report=term tests/

- name: Check coverage threshold
  run: |
    coverage report --show-missing --fail-under=83
```

## 10. カバレッジレポート

### 10.1 レポート形式
- **term**: ターミナル出力
- **html**: HTMLレポート（htmlcov/）
- **xml**: XML形式（coverage.xml）

### 10.2 カバレッジの確認方法
```bash
# コマンドライン
coverage report --show-missing

# HTMLレポート
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

### 10.3 カバレッジ向上の方針
1. 未カバーの分岐を特定
2. エッジケースのテスト追加
3. エラーパスのテスト強化
4. 統合テストの充実

## 11. テストデータ

### 11.1 固定値
```python
# Discord
TEST_TOKEN = "test_token"
TEST_GUILD_ID = "999999999"
TEST_CHANNEL_ID = "123456789"
TEST_USER_ID = "111111111"
TEST_USER_NAME = "testuser#1234"

# Sheets
TEST_SHEET_NAME = "Test Sheet"
TEST_DATE_JST = "2025-09-11"

# Slack
TEST_BOT_TOKEN = "xoxb-test-token"
TEST_CHANNEL_ID = "C1234567890"
```

### 11.2 モックデータ生成
```python
def create_mock_member(user_id, user_name):
    mock = Mock()
    mock.id = user_id
    mock.name = user_name.split('#')[0]
    mock.discriminator = user_name.split('#')[1]
    return mock
```

## 12. エラーケースのテスト

### 12.1 テスト対象エラー
- 接続エラー
- 認証エラー
- API制限エラー
- データ形式エラー
- タイムアウト

### 12.2 エラーシミュレーション
```python
# 例外を発生させる
mock_client.start.side_effect = Exception("Connection failed")

# APIエラーレスポンス
mock_response = {"ok": False, "error": "channel_not_found"}
```

## 13. パフォーマンステスト

### 13.1 対象外の理由
- 外部API依存のため実測困難
- モック環境では意味がない
- 本番環境でのモニタリングで代替

### 13.2 将来の検討事項
- 負荷テスト
- スケーラビリティテスト
- 並行処理テスト

## 14. テストのメンテナンス

### 14.1 定期レビュー
- 月次でテストカバレッジ確認
- 四半期でテストケース見直し
- 年次でフレームワーク更新検討

### 14.2 テスト追加のタイミング
- 新機能実装時
- バグ修正時（リグレッションテスト）
- リファクタリング前

### 14.3 テストの削除基準
- 機能の削除
- 重複するテストケース
- メンテナンスコストが高い

## 15. 今後の改善点

### 15.1 短期目標
- Discord clientのカバレッジ70%達成
- E2Eテストの追加
- テストの並列実行

### 15.2 長期目標
- カバレッジ90%達成
- プロパティベーステスト導入
- ミューテーションテスト導入
- パフォーマンステスト自動化