# Slack Bot セットアップガイド

## 📌 このガイドについて

Slack Botを作成し、トークンを取得する手順を初心者向けに説明します。
所要時間：約15分

## 🤖 Slack Botとは？

Slack Botは、Slackワークスペース内で自動的にメッセージを送信したり、タスクを実行したりするプログラムです。
このプロジェクトでは、VCログイン通知を送信するために使用します。

## 📝 事前準備

- Slackワークスペース（管理者権限が必要）
- ウェブブラウザ（Chrome、Firefox等）
- 通知を送信したいSlackチャンネル

## 🚀 Slack App作成手順

### ステップ1：Slack API サイトにアクセス

1. [Slack API](https://api.slack.com/apps)を開く
2. Slackアカウントでログイン

### ステップ2：新しいAppを作成

1. 「**Create New App**」ボタンをクリック

2. 「**From scratch**」を選択

3. App情報を入力：
   - **App Name**：
     - 本番用例：`VC Tracker Notifier`
     - テスト用例：`VC Tracker TEST`
   - **Pick a workspace**：
     - インストール先のワークスペースを選択

4. 「**Create App**」をクリック

### ステップ3：Bot Tokenスコープを設定

1. 左側メニューから「**OAuth & Permissions**」を選択

2. 「**Scopes**」セクションまでスクロール

3. 「**Bot Token Scopes**」で「**Add an OAuth Scope**」をクリック

4. 以下のスコープを追加：
   | スコープ | 説明 |
   |---------|------|
   | `chat:write` | メッセージを送信する権限 |
   | `channels:read` | パブリックチャンネル情報を読む権限（オプション） |
   | `groups:read` | プライベートチャンネル情報を読む権限（オプション） |

### ステップ4：Appをワークスペースにインストール

1. 「**OAuth & Permissions**」ページの上部に戻る

2. 「**Install to Workspace**」ボタンをクリック

3. 権限を確認して「**許可する**」をクリック

### ステップ5：Bot Tokenを取得

1. インストール完了後、「**OAuth & Permissions**」ページに戻る

2. 「**Bot User OAuth Token**」をコピー
   ```
   例：xoxb-YOUR-BOT-TOKEN-HERE
   ```

   ⚠️ **重要な注意事項**：
   - `xoxb-`で始まることを確認（Bot Token）
   - `xoxp-`はUser Tokenなので使用しない
   - 他人に見せないでください
   - GitHubにコミットしないでください

### ステップ6：BotをChannelに追加

#### パブリックチャンネルの場合

1. Slackで通知を送信したいチャンネルを開く

2. チャンネル名をクリック → 「**インテグレーション**」タブ

3. 「**アプリを追加する**」をクリック

4. 作成したAppを検索して「**追加**」

#### プライベートチャンネルの場合

1. チャンネルで `/invite @アプリ名` を入力
   ```
   /invite @VC Tracker Notifier
   ```

### ステップ7：Channel IDを取得

#### 方法1：Slackアプリから取得（推奨）

1. 通知を送信したいチャンネルを開く

2. チャンネル名をクリック

3. 一番下までスクロールして「**チャンネルID**」を確認
   ```
   例：C1234567890
   ```

#### 方法2：ブラウザから取得

1. [Slack Web版](https://slack.com)を開く

2. 対象チャンネルを開く

3. URLから取得：
   ```
   https://app.slack.com/client/T123456/C1234567890
                                         ^^^^^^^^^^^^ これがChannel ID
   ```

## 🔐 トークンの保管方法

### 開発環境（ローカル）

`.env`ファイルに保存：
```env
SLACK_BOT_TOKEN=xoxb-あなたのトークンをここに貼り付け
SLACK_CHANNEL_ID=C1234567890
```

### テスト環境（GitHub）

GitHub Secretsに保存：
- `TEST_SLACK_BOT_TOKEN`
- `TEST_SLACK_CHANNEL_ID`

### 本番環境（GitHub）

GitHub Secretsに保存：
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`

## ✅ 動作確認

### テストメッセージ送信

```python
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

# 環境変数から取得
token = os.getenv('SLACK_BOT_TOKEN')
channel = os.getenv('SLACK_CHANNEL_ID')

client = WebClient(token=token)

try:
    # テストメッセージを送信
    response = client.chat_postMessage(
        channel=channel,
        text="✅ Slack Bot接続テスト成功！"
    )
    print(f"✅ メッセージ送信成功: {response['ts']}")
    
except SlackApiError as e:
    print(f"❌ エラー: {e.response['error']}")
```

## 🚨 トラブルシューティング

### よくあるエラーと対処法

#### 1. 「invalid_auth」エラー
**原因**：トークンが無効
**対処**：
- トークンが`xoxb-`で始まることを確認
- トークンを再生成して試す

#### 2. 「channel_not_found」エラー
**原因**：チャンネルIDが間違っているか、Botが追加されていない
**対処**：
- チャンネルIDを再確認
- BotをチャンネルにInvite

#### 3. 「not_in_channel」エラー
**原因**：Botがチャンネルのメンバーではない
**対処**：
- `/invite @アプリ名` でBotを追加

#### 4. 「missing_scope」エラー
**原因**：必要な権限がない
**対処**：
- OAuth & Permissionsで`chat:write`スコープを追加
- Appを再インストール

## 📊 メッセージフォーマット例

### シンプルなテキスト

```python
client.chat_postMessage(
    channel=channel,
    text="ユーザーがVCにログインしました"
)
```

### リッチなフォーマット（Block Kit）

```python
client.chat_postMessage(
    channel=channel,
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🎉 *VC ログイン通知*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*ユーザー:*\n田中太郎"
                },
                {
                    "type": "mrkdwn",
                    "text": "*通算日数:*\n42日目"
                }
            ]
        }
    ]
)
```

## 💡 Tips

### 複数環境の管理

| 環境 | App名の例 | チャンネルの例 |
|------|-----------|---------------|
| 本番 | VC Tracker | #vc-notifications |
| テスト | VC Tracker TEST | #test-notifications |
| 開発 | VC Tracker DEV | #dev-notifications |

### Rate Limit対策

- Slackには[Rate Limits](https://api.slack.com/docs/rate-limits)があります
- 通常：1秒に1メッセージまで
- バースト：短期間に複数送信可能

### セキュリティのベストプラクティス

1. **最小権限の原則**
   - 必要最小限のスコープのみ付与
   - 不要な権限は削除

2. **トークンのローテーション**
   - 定期的にトークンを再生成
   - 古いトークンは無効化

3. **監査ログの確認**
   - Slack管理画面で定期的に確認
   - 不審なアクティビティをチェック

## ❓ よくある質問

### Q: 無料プランでも使えますか？
A: はい、基本的な機能は無料プランで利用可能です。

### Q: 複数のチャンネルに送信できますか？
A: はい、チャンネルIDを変えて複数回送信すれば可能です。

### Q: DMも送信できますか？
A: はい、`im:write`スコープを追加すれば可能です。

### Q: メンション（@channel、@here）できますか？
A: 特別な記法（`<!channel>`、`<!here>`）を使用すれば可能です。

## 📚 参考リンク

- [Slack API Documentation](https://api.slack.com/)
- [Block Kit Builder](https://app.slack.com/block-kit-builder) - メッセージデザインツール
- [Slack SDK for Python](https://slack.dev/python-slack-sdk/)
- [Rate Limits](https://api.slack.com/docs/rate-limits)

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. エラーメッセージの全文
2. 使用しているコード
3. Slack App設定のスクリーンショット（トークンは隠す）
4. 試した対処法