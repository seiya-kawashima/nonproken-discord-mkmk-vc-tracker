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

### 2. Google Drive CSV モジュール (`drive_csv_client.py`)

**責務**: Google Drive上のCSVファイル操作

```python
class DriveCSVClient:
    def __init__(self, service_account_json: str, folder_name: str = "VC_Tracker_Data")
    def connect()
    def upsert_presence(self, members: list[Dict[str, Any]]) -> Dict[str, int]
```

**データ操作仕様**:
- VCチャンネルごとに個別のCSVファイルを管理
- Upsert: `(date_jst, user_id)` をキーとして存在確認
- 存在する場合: スキップ（すでにTRUEなので更新不要）
- 存在しない場合: 新規行追加（present=TRUE）
- Google Drive上に`VC_Tracker_Data`フォルダを自動作成

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

### 4. メインスクリプト (`discord_attendance_collector.py`)

**処理フロー**:
1. 環境変数読み込み
2. Discord接続 → VCメンバー取得
3. Google Drive CSV更新
4. 通算日数計算（CSVファイルから集計）
5. Slack通知送信
6. 終了

## エラーハンドリング

### Discord接続エラー
- リトライ: 3回まで（指数バックオフ）
- 最終失敗時: エラーログ出力、処理継続（次回実行に期待）

### Google Drive API エラー
- Rate Limit: 60秒待機後リトライ
- 認証エラー: 即座に終了（設定ミス）

### Slack API エラー
- 通知失敗: エラーログのみ（メイン処理は継続）

## パフォーマンス考慮事項

### バッチ処理
- Drive API: VCごとのCSVファイルを一括更新
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
- Google Drive: ファイルの作成・編集権限
- Slack Bot: `chat:write` のみ

## テスト戦略

### ユニットテスト
```bash
pytest tests/
```

### モック対象
- Discord API レスポンス
- Google Drive API
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
- データベース移行: CSV → PostgreSQL（大規模化時）

## CSVファイル設計

### ファイル構成
- **保存場所**: Google Drive上の`VC_Tracker_Data`フォルダ
- **ファイル名**: `{VCチャンネル名}.csv` (例: `general-voice.csv`)

### CSVカラム構成

| カラム | 型 | 説明 | 例 |
|---|---|---|---|
| date_jst | STRING | 日本時間の日付 | 2025/9/11 |
| user_id | STRING | DiscordユーザーID | 111111111111111111 |
| user_name | STRING | ユーザー名#識別子 | kawashima#1234 |
| present | STRING | ログイン有無 | TRUE |

**ユニークキー**:
- `(date_jst, user_id)` の組み合わせ

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
google-api-python-client==2.100.0
google-auth==2.28.0
google-auth-httplib2==0.1.1
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