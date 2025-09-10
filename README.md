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