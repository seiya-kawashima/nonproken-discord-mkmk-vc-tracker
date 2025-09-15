# 環境別設定ガイド

## 🎯 環境構成

本プロジェクトは3つの環境で運用されます：

| 環境 | 用途 | トリガー | 使用するSecrets |
|------|------|----------|-----------------|
| **開発環境（Local）** | ローカル開発・デバッグ | 手動実行 | `.env`ファイル |
| **テスト環境（Test）** | CI/CD自動テスト | PR作成・develop push | `TST_`プレフィックス付きSecrets |
| **本番環境（Production）** | 実運用 | スケジュール・main push | プレフィックスなしSecrets |

## 📝 開発環境（ローカル）

### セットアップ手順

1. **`.env`ファイルの作成**
```bash
cp .env.example .env
```

2. **テスト用のDiscord/Slack環境を準備**
   - テスト用Discordサーバーを作成
   - テスト用Slackワークスペースを作成
   - テスト用Googleスプレッドシートを作成

3. **`.env`に開発用の値を設定**
```env
# 開発用Discord Bot（テストサーバー用）
DISCORD_BOT_TOKEN=your_test_discord_bot_token

# 開発用Googleスプレッドシート
GOOGLE_SHEET_NAME=VC_Tracker_Test

# 開発用Slack（テストワークスペース）
SLACK_BOT_TOKEN=xoxb-test-workspace-token
SLACK_CHANNEL_ID=C_TEST_CHANNEL

# テスト用VCチャンネル
ALLOWED_VOICE_CHANNEL_IDS=test_channel_id_1,test_channel_id_2
```

4. **動作確認**
```bash
python discord_attendance_collector.py
```

## 🧪 テスト環境（GitHub Actions）

### GitHub Environments設定

1. **リポジトリSettings → Environments → New environment**
2. **"test"環境を作成**
3. **Protection rules（オプション）**：
   - Required reviewers: 1人以上
   - Deployment branches: develop, feature/*

### テスト環境用Secrets設定

以下のSecretsを**test環境**に設定：

| Secret名 | 説明 | 例 |
|----------|------|-----|
| `TST_DISCORD_BOT_TOKEN` | テスト用Discord Botトークン | テストサーバー専用Bot |
| `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | テスト用サービスアカウント | テスト用シートのみアクセス可 |
| `TST_ALLOWED_VOICE_CHANNEL_IDS` | テスト用VCチャンネルID | テストサーバーのVC |
| `TST_SLACK_BOT_TOKEN` | テスト用Slackトークン | テストワークスペース用 |
| `TST_SLACK_CHANNEL_ID` | テスト用Slackチャンネル | #test-notifications |

### テスト実行方法

#### 自動実行
- Pull Request作成時
- developブランチへのpush時
- feature/*ブランチへのpush時

#### 手動実行
1. Actions → Test Environment → Run workflow
2. テストタイプを選択：
   - `all`: 全テスト実行
   - `discord_only`: Discord接続テストのみ
   - `sheets_only`: Sheets接続テストのみ
   - `slack_only`: Slack通知テストのみ

## 🚀 本番環境（Production）

### GitHub Environments設定

1. **"production"環境を作成**（オプション）
2. **Protection rules**：
   - Required reviewers: 2人以上
   - Wait timer: 5分
   - Deployment branches: main only

### 本番環境用Secrets設定

以下のSecretsを**リポジトリレベル**または**production環境**に設定：

| Secret名 | 説明 | 注意事項 |
|----------|------|----------|
| `DISCORD_BOT_TOKEN` | 本番Discord Botトークン | 本番サーバー専用 |
| `GOOGLE_SHEET_NAME` | 本番スプレッドシート名 | 実データ記録用 |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | 本番サービスアカウント | 本番シートのみアクセス |
| `ALLOWED_VOICE_CHANNEL_IDS` | 本番VCチャンネルID | 監視対象の本番VC |
| `SLACK_BOT_TOKEN` | 本番Slackトークン | 本番ワークスペース |
| `SLACK_CHANNEL_ID` | 本番Slackチャンネル | 本番通知先 |

### デプロイフロー

```mermaid
graph LR
    A[ローカル開発] --> B[feature branch]
    B --> C[Pull Request]
    C --> D[テスト環境で自動テスト]
    D --> E[develop branch]
    E --> F[統合テスト]
    F --> G[main branch]
    G --> H[本番環境デプロイ]
```

## 🔒 セキュリティ考慮事項

### 環境分離の原則

1. **完全に別のリソースを使用**
   - Discord: 別サーバー・別Bot
   - Slack: 別ワークスペース・別App
   - Google: 別スプレッドシート・別サービスアカウント

2. **権限の最小化**
   - テスト環境: テストリソースのみアクセス可
   - 本番環境: 本番リソースのみアクセス可

3. **トークンの定期更新**
   - 3ヶ月ごとにトークンを再生成
   - 古いトークンは即座に無効化

### 環境別の命名規則

```
# Discord サーバー名
本番: MKMK VC Tracker
テスト: MKMK VC Tracker [TEST]

# Googleスプレッドシート名
本番: VC_Tracker_Database
テスト: VC_Tracker_Test

# Slackチャンネル名
本番: #vc-notifications
テスト: #test-vc-notifications
```

## 📊 環境別モニタリング

### ログレベル設定

| 環境 | LOG_LEVEL | 説明 |
|------|-----------|------|
| 開発 | 1 (DEBUG) | 詳細なデバッグ情報 |
| テスト | 1 (DEBUG) | テスト実行の詳細 |
| 本番 | 2 (INFO) | 通常運用ログ |

### アラート設定

- **本番環境**: エラー時にSlack通知
- **テスト環境**: PR上にコメント
- **開発環境**: コンソール出力のみ

## 🔧 トラブルシューティング

### よくある問題

#### Q: テスト環境でDiscord接続エラー
A: テスト用BotがテストサーバーにいることとVCチャンネルIDが正しいことを確認

#### Q: Secrets not foundエラー
A: 環境名（test/production）とSecret名のプレフィックスを確認

#### Q: 本番環境で動作しない
A: テスト環境で正常動作することを確認してからデプロイ

### デバッグ方法

1. **ローカルでの確認**
```bash
# 環境変数の確認
python -c "import os; print(os.getenv('DISCORD_BOT_TOKEN')[:10] + '...')"
```

2. **GitHub Actionsでの確認**
   - workflow_dispatchでdebug_enabled=trueを指定
   - ログレベルがDEBUGになり詳細情報が出力される

## 📚 参考リンク

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Slack API](https://api.slack.com/)