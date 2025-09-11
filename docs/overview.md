# Discord VC Tracker Bot 詳細仕様書

## システム構成

### 1. Discord Bot モジュール (`discord_client.py`)

**責務**: Discord接続とVCメンバー取得

```python
class DiscordVCPoller:
    def __init__(self, token: str, allowed_channel_ids: list[str])
    async def get_vc_members(self) -> list[VCMember]
```

**VCMember データ構造**:
```python
@dataclass
class VCMember:
    guild_id: str
    channel_id: str
    user_id: str
    user_name: str
    timestamp: datetime
```

### 2. Google Sheets モジュール (`sheets_client.py`)

**責務**: スプレッドシート操作

```python
class SheetsClient:
    def __init__(self, credentials_path: str, sheet_name: str)
    def upsert_presence(self, date_jst: str, members: list[VCMember])
    def get_total_days(self, user_id: str) -> int
```

**データ操作仕様**:
- Upsert: `(date_jst, guild_id, user_id)` をキーとして存在確認
- 存在する場合: スキップ（すでにTRUEなので更新不要）
- 存在しない場合: 新規行追加（present=TRUE）

### 3. Slack通知モジュール (`slack_notifier.py`)

**責務**: Slack通知送信

```python
class SlackNotifier:
    def __init__(self, token: str, channel_id: str)
    def send_login_notification(self, user_name: str, total_days: int)
```

**通知ロジック**:
- 通常: `🎤 {user_name} さんがログインしました！（通算 {total_days} 日目）`
- 100日刻み: `🎉` アイコンと「おめでとう！」メッセージ追加

### 4. メインスクリプト (`poll_once.py`)

**処理フロー**:
1. 環境変数読み込み
2. Discord接続 → VCメンバー取得
3. Google Sheets更新
4. 通算日数計算
5. Slack通知送信
6. 終了

## エラーハンドリング

### Discord接続エラー
- リトライ: 3回まで（指数バックオフ）
- 最終失敗時: エラーログ出力、処理継続（次回実行に期待）

### Google Sheets API エラー
- Rate Limit: 60秒待機後リトライ
- 認証エラー: 即座に終了（設定ミス）

### Slack API エラー
- 通知失敗: エラーログのみ（メイン処理は継続）

## パフォーマンス考慮事項

### バッチ処理
- Sheets API: `batch_update` で複数行を一括更新
- Slack API: 複数ユーザーを1メッセージにまとめる

### キャッシュ
- 通算日数: 実行中はメモリにキャッシュ（同一ユーザーの重複計算回避）

## セキュリティ

### トークン管理
- 環境変数または GitHub Secrets で管理
- ログ出力時はマスキング
- コミットに含めない（.gitignore）

### 権限最小化
- Discord Bot: 必要最小限のIntents
- Google Sheets: 特定シートのみ編集権限
- Slack Bot: `chat:write` のみ

## テスト戦略

### ユニットテスト
```bash
pytest tests/
```

### モック対象
- Discord API レスポンス
- Google Sheets API
- Slack API
- 日時（固定値でテスト）

### CI/CD
- GitHub Actions でテスト自動実行
- Pull Request時に必須チェック

## 監視・アラート

### ログ出力
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### メトリクス
- 実行時間
- 検出ユーザー数
- API呼び出し回数
- エラー率

## 将来の拡張性

### 機能追加案
1. **滞在時間記録**: 入室・退室時刻を記録
2. **週次レポート**: 週間アクティビティサマリー
3. **ランキング**: 月間ログイン日数ランキング
4. **カスタムメッセージ**: ユーザーごとの通知カスタマイズ

### スケーラビリティ
- 複数サーバー対応: guild_id ごとに処理
- 並列処理: asyncio で複数VCを同時監視
- データベース移行: Sheets → PostgreSQL（大規模化時）

## データベース設計

### `daily_presence` テーブル

| カラム | 型 | 説明 | 制約 |
|---|---|---|---|
| date_jst | DATE | 日本時間の日付 | NOT NULL |
| guild_id | VARCHAR(20) | DiscordサーバーID | NOT NULL |
| user_id | VARCHAR(20) | DiscordユーザーID | NOT NULL |
| user_name | VARCHAR(100) | ユーザー名#識別子 | NOT NULL |
| present | BOOLEAN | ログイン有無 | DEFAULT TRUE |
| created_at | TIMESTAMP | レコード作成日時 | DEFAULT NOW() |
| updated_at | TIMESTAMP | レコード更新日時 | DEFAULT NOW() |

**インデックス**:
- PRIMARY KEY: `(date_jst, guild_id, user_id)`
- INDEX: `user_id` (通算日数集計用)
- INDEX: `date_jst` (日別集計用)

## API仕様

### 内部API（将来のWebダッシュボード用）

#### GET /api/users/{user_id}/stats
**レスポンス**:
```json
{
  "user_id": "111111111111111111",
  "user_name": "kawashima#1234",
  "total_days": 150,
  "current_streak": 5,
  "longest_streak": 23,
  "last_login": "2025-09-11",
  "milestones": [100]
}
```

#### GET /api/leaderboard
**クエリパラメータ**:
- `period`: `week` | `month` | `all`
- `limit`: 整数（デフォルト: 10）

**レスポンス**:
```json
{
  "period": "month",
  "rankings": [
    {
      "rank": 1,
      "user_id": "111111111111111111",
      "user_name": "kawashima#1234",
      "days": 28
    }
  ]
}
```

## 実行スケジュール詳細

### GitHub Actions Cron設定

```yaml
# JST 4:00, 4:30, 5:00, 5:30, 6:00, 6:30, 7:00
- cron: "0 19 * * *"    # UTC 19:00 = JST 4:00
- cron: "30 19 * * *"   # UTC 19:30 = JST 4:30
- cron: "0 20 * * *"    # UTC 20:00 = JST 5:00
- cron: "30 20 * * *"   # UTC 20:30 = JST 5:30
- cron: "0 21 * * *"    # UTC 21:00 = JST 6:00
- cron: "30 21 * * *"   # UTC 21:30 = JST 6:30
- cron: "0 22 * * *"    # UTC 22:00 = JST 7:00
```

### 実行タイミングの考慮事項
- **早朝選択理由**: 深夜活動ユーザーの検出
- **30分間隔**: 短時間滞在ユーザーも検出
- **7:00終了**: 通常の朝活動開始前に完了

## 依存関係

### requirements.txt
```
discord.py==2.3.2
gspread==6.0.0
google-auth==2.28.0
google-auth-oauthlib==1.2.0
slack-sdk==3.26.0
python-dotenv==1.0.0
pytz==2024.1
```

### requirements-dev.txt
```
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-mock==3.12.0
black==24.2.0
flake8==7.0.0
mypy==1.8.0
```