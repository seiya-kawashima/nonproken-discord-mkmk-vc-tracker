# Discord VC Logger

Discord の特定ボイスチャンネルで
**「その日に一度でもログインしたか」** を記録し、さらに Slack に通知する Bot です。

本ツールは **GitHub Actions** を利用して定期実行するため、
サーバーやクラウドを常時稼働させる必要がありません。

---

## 機能概要

* **対象VC限定**で入室者をチェック
* **毎日4:00–7:00 JSTの間、30分ごと**にスナップショットを取得
* その日、1回でも在室が確認できたユーザーを **ログイン日（TRUE）** としてスプレッドシートに記録
* ログインしたユーザーを **Slackに自動通知**
* 通算ログイン日数を管理し、**100日ごとの節目にお祝い通知**

---

## シート設計

### `daily_presence` シート

| 列 | 名称          | 例                  |
| - | ----------- | ------------------ |
| A | `date_jst`  | 2025-09-11         |
| B | `guild_id`  | 123456789012345678 |
| C | `user_id`   | 111111111111111111 |
| D | `user_name` | kawashima#1234     |
| E | `present`   | TRUE               |

* `(date_jst, guild_id, user_id)` の組み合わせで **一意**
* すでに TRUE の場合は更新不要（Upsert方式）

### ログイン日数集計例

* 通算ログイン日数：

  ```excel
  =COUNTIF(FILTER(E:E, C:C=[user_id]), TRUE)
  ```

---

## 必要なもの

### Discord 側

* Discord Developer Portal で Bot を作成
* Bot Token を発行
* Intents で `Server Members` / `Voice States` を有効化
* Bot をサーバーに招待しておく（VCに参加する必要はなし）

### Google 側

* Google Cloud でサービスアカウントを作成
* JSON キーファイルを取得
* スプレッドシートをサービスアカウントのメールに **編集者権限で共有**

### Slack 側（通知用）

* [Slack API](https://api.slack.com/apps) で App を作成
* 権限：`chat:write`
* Bot Token (`xoxb-***`) を発行
* Bot をワークスペースにインストールし、通知チャンネルに招待

---

## GitHub Actions 運用

### 無料枠

* Free/Pro アカウント：**月 2,000 分まで無料**（Linuxランナーは1x消費）
* 本要件：

  * 1日7回実行（4:00〜7:00 JSTの30分刻み）
  * 実行時間：1回あたり1〜2分
  * 1か月 ≒ 420分
* → **無料枠内で運用可能**

### Secrets 設定

リポジトリの **Settings → Secrets and variables → Actions** に登録：

* `DISCORD_BOT_TOKEN` … Discord Botのトークン
* `GOOGLE_SERVICE_ACCOUNT_JSON` … サービスアカウントJSON（Base64化して登録推奨）
* `GOOGLE_SHEET_NAME` … スプレッドシート名
* `ALLOWED_VOICE_CHANNEL_IDS` … 対象VC ID（カンマ区切り）
* `SLACK_BOT_TOKEN` … Slack Bot のトークン
* `SLACK_CHANNEL_ID` … 通知先チャンネルの ID

---

## ワークフロー例

`.github/workflows/poll.yml`

```yaml
name: VC Presence Poller

on:
  schedule:
    # JST 4:00〜7:00 の間、30分ごと（GitHubのcronはUTC基準）
    - cron: "0,30 19-22 * * *"   # 19〜22時UTC = 翌日4〜7時JST
  workflow_dispatch:

jobs:
  poll:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Restore Google JSON
        run: |
          echo "$GOOGLE_SERVICE_ACCOUNT_JSON" | base64 -d > service_account.json
        shell: bash
        env:
          GOOGLE_SERVICE_ACCOUNT_JSON: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON }}

      - name: Run poll script
        run: |
          python poll_once.py
        env:
          DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
          GOOGLE_SHEET_NAME: ${{ secrets.GOOGLE_SHEET_NAME }}
          ALLOWED_VOICE_CHANNEL_IDS: ${{ secrets.ALLOWED_VOICE_CHANNEL_IDS }}
          GOOGLE_SERVICE_ACCOUNT_JSON: service_account.json
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
```

---

## poll\_once.py の役割（概要）

1. Discord Gatewayに一時接続
2. `ALLOWED_VOICE_CHANNEL_IDS` の在室メンバー一覧を取得
3. 今日のJST日付で `daily_presence` にUpsert（present=TRUE）
4. ユーザーごとの通算ログイン日数を計算
5. Slackへ通知：

   * 通常：

     ```
     🎤 kawashima#1234 さんがログインしました！（通算 15 日目）
     ```
   * 100日ごとの節目：

     ```
     🎉 kawashima#1234 さんがログインしました！（通算 100 日目！おめでとう！）
     ```

---

## メリット / デメリット

### メリット

* ✅ サーバー不要 → **完全無料**運用（GitHub Actions枠内）
* ✅ スプレッドシートで履歴・通算管理
* ✅ Slack通知でゲーミフィケーション（節目お祝い）

### デメリット

* ⚠️ 30分以内で入退室した人は検出漏れの可能性あり
* ⚠️ GitHub Actions の cron は数分遅延する場合あり

---

## まとめ

* **GitHub Actions** により無料で運用可能
* **Google Sheets** でログイン履歴を保持
* **Slack通知** で日次報告＋節目祝い
* 継続参加を促進するシンプルな仕組み

---

## 開発環境

### 言語・ライブラリ
* **Python 3.11+**
* 主要ライブラリ:
  - `discord.py` - Discord Bot開発
  - `gspread` - Google Sheetsアクセス
  - `slack-sdk` - Slack通知
  - `python-dotenv` - 環境変数管理

### VSCode推奨設定

#### 拡張機能
* **Python** (ms-python.python)
* **Pylance** (ms-python.vscode-pylance)
* **Python Debugger** (ms-python.debugpy)
* **GitHub Actions** (github.vscode-github-actions)
* **YAML** (redhat.vscode-yaml)

#### .vscode/settings.json
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.rulers": [88],
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

#### .vscode/launch.json
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Poll Once",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/poll_once.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    }
  ]
}
```

### 開発環境セットアップ

```bash
# 仮想環境作成
python -m venv .venv

# 仮想環境有効化（Windows）
.venv\Scripts\activate

# 仮想環境有効化（Mac/Linux）
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 開発用依存関係（オプション）
pip install black flake8 pytest
```

### .env ファイル例（ローカル開発用）
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
GOOGLE_SHEET_NAME=your_sheet_name
ALLOWED_VOICE_CHANNEL_IDS=111111111111111111,222222222222222222
SLACK_BOT_TOKEN=xoxb-your-slack-token
SLACK_CHANNEL_ID=C1234567890
```

---

## 詳細仕様書

### システム構成

#### 1. Discord Bot モジュール (`discord_client.py`)

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

#### 2. Google Sheets モジュール (`sheets_client.py`)

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

#### 3. Slack通知モジュール (`slack_notifier.py`)

**責務**: Slack通知送信

```python
class SlackNotifier:
    def __init__(self, token: str, channel_id: str)
    def send_login_notification(self, user_name: str, total_days: int)
```

**通知ロジック**:
- 通常: `🎤 {user_name} さんがログインしました！（通算 {total_days} 日目）`
- 100日刻み: `🎉` アイコンと「おめでとう！」メッセージ追加

#### 4. メインスクリプト (`poll_once.py`)

**処理フロー**:
1. 環境変数読み込み
2. Discord接続 → VCメンバー取得
3. Google Sheets更新
4. 通算日数計算
5. Slack通知送信
6. 終了

### エラーハンドリング

#### Discord接続エラー
- リトライ: 3回まで（指数バックオフ）
- 最終失敗時: エラーログ出力、処理継続（次回実行に期待）

#### Google Sheets API エラー
- Rate Limit: 60秒待機後リトライ
- 認証エラー: 即座に終了（設定ミス）

#### Slack API エラー
- 通知失敗: エラーログのみ（メイン処理は継続）

### パフォーマンス考慮事項

#### バッチ処理
- Sheets API: `batch_update` で複数行を一括更新
- Slack API: 複数ユーザーを1メッセージにまとめる

#### キャッシュ
- 通算日数: 実行中はメモリにキャッシュ（同一ユーザーの重複計算回避）

### セキュリティ

#### トークン管理
- 環境変数または GitHub Secrets で管理
- ログ出力時はマスキング
- コミットに含めない（.gitignore）

#### 権限最小化
- Discord Bot: 必要最小限のIntents
- Google Sheets: 特定シートのみ編集権限
- Slack Bot: `chat:write` のみ

### テスト戦略

#### ユニットテスト
```bash
pytest tests/
```

#### モック対象
- Discord API レスポンス
- Google Sheets API
- Slack API
- 日時（固定値でテスト）

#### CI/CD
- GitHub Actions でテスト自動実行
- Pull Request時に必須チェック

### 監視・アラート

#### ログ出力
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### メトリクス
- 実行時間
- 検出ユーザー数
- API呼び出し回数
- エラー率

### 将来の拡張性

#### 機能追加案
1. **滞在時間記録**: 入室・退室時刻を記録
2. **週次レポート**: 週間アクティビティサマリー
3. **ランキング**: 月間ログイン日数ランキング
4. **カスタムメッセージ**: ユーザーごとの通知カスタマイズ

#### スケーラビリティ
- 複数サーバー対応: guild_id ごとに処理
- 並列処理: asyncio で複数VCを同時監視
- データベース移行: Sheets → PostgreSQL（大規模化時）