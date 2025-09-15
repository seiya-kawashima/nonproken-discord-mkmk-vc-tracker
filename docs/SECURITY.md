# セキュリティガイドライン

## 機密情報の取り扱い

### 🚨 絶対に守るべきルール

1. **機密情報を直接コミットしない**
   - Bot Token
   - API Key
   - Service Account JSON
   - パスワード
   - その他の認証情報

2. **公開リポジトリでの運用**
   - すべての機密情報はGitHub Secretsで管理
   - ローカルでは`.env`ファイルを使用
   - `.env`は必ず`.gitignore`に含める

## Discord Bot Token

### 必要な情報
- **Bot Token のみ** ✅
- Client ID ❌ 不要
- Client Secret ❌ 不要

### 取得方法
1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. アプリケーションを作成
3. Bot セクションでTokenを取得
4. **Reset Token**をクリックして新規生成

### セキュリティ設定
- Public Bot: OFF推奨（特定サーバーのみで使用）
- Requires OAuth2 Code Grant: OFF

## Google Service Account

### JSONファイルの取り扱い
```bash
# Base64エンコード（GitHub Secrets登録用）
base64 -i service_account.json > encoded.txt

# デコード（GitHub Actions内で使用）
echo "$GOOGLE_SERVICE_ACCOUNT_JSON" | base64 -d > service_account.json
```

### 権限の最小化
- スプレッドシートの編集権限のみ付与
- 特定のシートのみアクセス可能に設定

## Slack Bot Token

### トークンの種類
- **Bot User OAuth Token** (`xoxb-`) を使用
- User OAuth Token (`xoxp-`) は使用しない

### スコープの最小化
必要最小限のスコープのみ付与:
- `chat:write` - メッセージ送信
- `channels:read` - チャンネル情報の読み取り（必要に応じて）

## GitHub Actions での安全な運用

### 必要なGitHub Secrets

#### 本番環境用Secrets
以下のSecretsをGitHubリポジトリに設定する必要があります：

| Secret名 | 説明 | 取得方法 |
|----------|------|----------|
| `DISCORD_BOT_TOKEN` | Discord Botのトークン | Discord Developer Portalから取得 |
| `GOOGLE_SHEET_NAME` | Googleスプレッドシート名 | 作成したシートの名前 |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | サービスアカウントJSON（Base64エンコード済み） | `base64 -i service_account.json` で生成 |
| `ALLOWED_VOICE_CHANNEL_IDS` | 監視対象VCチャンネルID（カンマ区切り） | Discord開発者モードでチャンネルIDをコピー |
| `SLACK_BOT_TOKEN` | Slack Botトークン | Slack App管理画面から取得 |
| `SLACK_CHANNEL_ID` | 通知先SlackチャンネルID | Slackチャンネル情報から取得 |

#### テスト環境用Secrets
テスト環境では、すべてのSecret名に`TST_`プレフィックスを付けます：

| Secret名 | 説明 | 用途 |
|----------|------|------|
| `TST_DISCORD_BOT_TOKEN` | テスト用Discord Botトークン | テストサーバーでの動作確認 |
| `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | テスト用サービスアカウント | テストシートへのアクセス |
| `TST_ALLOWED_VOICE_CHANNEL_IDS` | テスト用VCチャンネルID | テストサーバーのVC監視 |
| `TST_SLACK_BOT_TOKEN` | テスト用Slackトークン | テスト通知の送信 |
| `TST_SLACK_CHANNEL_ID` | テスト用Slackチャンネル | テスト通知先 |

詳細な環境設定については[ENVIRONMENTS.md](ENVIRONMENTS.md)を参照してください。

### GitHub Secretsの設定手順

1. **リポジトリの Settings を開く**
2. **Security → Secrets and variables → Actions を選択**
3. **New repository secret をクリック**
4. **各Secretを追加**：
   
   例：Discord Bot Tokenの追加
   - Name: `DISCORD_BOT_TOKEN`
   - Secret: `実際のトークン値`
   
   Service Account JSONの追加（特殊）
   ```bash
   # まずBase64エンコード
   base64 -i service_account.json | tr -d '\n' > encoded.txt
   # encoded.txtの内容をコピーしてSecretに貼り付け
   ```

### Secrets の使用例
```yaml
# .github/workflows/poll.yml
env:
  DISCORD_BOT_TOKEN: ${{ secrets.DISCORD_BOT_TOKEN }}
  SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
  GOOGLE_SHEET_NAME: ${{ secrets.GOOGLE_SHEET_NAME }}
  ALLOWED_VOICE_CHANNEL_IDS: ${{ secrets.ALLOWED_VOICE_CHANNEL_IDS }}
  SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
```

### ログのマスキング
```yaml
- name: Run script
  run: |
    # 機密情報をマスク
    echo "::add-mask::${{ secrets.DISCORD_BOT_TOKEN }}"
    python discord_attendance_collector.py
```

## ローカル開発環境

### .env ファイルの管理
1. `.env.example`をコピー
```bash
cp .env.example .env
```

2. 実際の値を設定
```env
DISCORD_BOT_TOKEN=実際のトークン
```

3. 誤コミット防止
```bash
# .gitignoreに含まれていることを確認
git status --ignored
```

## トークンが漏洩した場合の対処

### 即座に実施すること
1. **トークンの無効化**
   - Discord: Developer Portalで再生成
   - Google: サービスアカウントキーを削除・再作成
   - Slack: アプリ設定でトークンを再生成

2. **影響範囲の確認**
   - アクセスログの確認
   - 不正な操作の有無を調査

3. **再発防止**
   - GitHub Secretsの更新
   - ローカル環境の`.env`更新
   - セキュリティ監査の実施

## セキュリティチェックリスト

### コミット前の確認
- [ ] `.env`ファイルが含まれていない
- [ ] `service_account.json`が含まれていない
- [ ] トークンや認証情報がハードコードされていない
- [ ] ログ出力に機密情報が含まれていない

### 定期的な確認
- [ ] 使用していないトークンの削除
- [ ] アクセス権限の見直し
- [ ] 依存パッケージのセキュリティアップデート

## 推奨ツール

### Git-secrets
```bash
# インストール
brew install git-secrets  # Mac
# または
git clone https://github.com/awslabs/git-secrets

# 設定
git secrets --install
git secrets --register-aws  # AWSパターン
git secrets --add 'xoxb-[0-9A-Za-z-]+'  # Slackトークン
```

### 環境変数の検証
```python
# discord_attendance_collector.py の冒頭で実施
import os
import sys

required_env = [
    'DISCORD_BOT_TOKEN',
    'SLACK_BOT_TOKEN',
    'GOOGLE_SERVICE_ACCOUNT_JSON'
]

for env in required_env:
    if not os.getenv(env):
        print(f"Error: {env} is not set")
        sys.exit(1)
```

## 連絡先

セキュリティ上の問題を発見した場合:
1. 公開Issueには投稿しない
2. プライベートな連絡手段で報告
3. 詳細な再現手順を含める