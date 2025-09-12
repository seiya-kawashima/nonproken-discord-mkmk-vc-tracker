# GitHub Secrets設定ガイド

## 📌 概要
GitHub ActionsでCI/CDテストを実行するために必要なSecretsの設定方法を説明します。

## 🔑 必要なSecrets

### 必須設定

| Secret名 | 説明 | 例 |
|----------|------|-----|
| `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | サービスアカウントJSONのBase64エンコード | 下記参照 |

**重要**: スプレッドシート名は環境ごとに固定値を使用します：
- テスト環境: `テスト用VCトラッカー`
- 本番環境: `VCトラッカー`
- 開発環境: `開発VCトラッカー`

### オプション設定

| Secret名 | 説明 | 例 |
|----------|------|-----|
| `DISCORD_BOT_TOKEN` | Discord Botトークン | `MTIzNDU2Nzg5...` |
| `ALLOWED_VOICE_CHANNEL_IDS` | VCチャンネルID（カンマ区切り） | `1234567890,0987654321` |
| `SLACK_BOT_TOKEN` | Slack Botトークン | `xoxb-...` |
| `SLACK_CHANNEL_ID` | SlackチャンネルID | `C1234567890` |

## 📝 設定手順

### 1. GitHubリポジトリのSettings画面を開く

1. リポジトリページで「Settings」タブをクリック
2. 左側メニューの「Secrets and variables」→「Actions」をクリック

### 2. 新しいSecretを追加

1. 「New repository secret」ボタンをクリック
2. 以下の情報を入力：
   - **Name**: Secret名（例：`TEST_GOOGLE_SHEET_NAME`）
   - **Value**: 設定値

### 3. TEST_GOOGLE_SHEET_NAMEの設定

```
Name: TEST_GOOGLE_SHEET_NAME
Value: あなたのテスト用スプレッドシート名
```

**注意**: この名前は実際にGoogle Sheetsで作成したスプレッドシートの名前と完全に一致する必要があります。

### 4. TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64の設定

#### Base64エンコード方法

**Linux/Mac:**
```bash
base64 -i service_account.json
```

**Windows (PowerShell):**
```powershell
[System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("service_account.json"))
```

**Windows (Git Bash):**
```bash
base64 service_account.json
```

#### 設定方法

1. 上記コマンドで取得したBase64文字列をコピー
2. GitHub Secretsに以下を設定：
```
Name: TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
Value: [Base64エンコードされた文字列全体]
```

## ✅ 設定確認方法

### 1. GitHub Actionsで手動実行

1. リポジトリの「Actions」タブを開く
2. 「Test Base64 Authentication」ワークフローを選択
3. 「Run workflow」ボタンをクリック
4. 実行結果を確認

### 2. 設定チェックリスト

- [ ] `TEST_GOOGLE_SHEET_NAME`が設定されている
- [ ] スプレッドシート名が実際のシート名と一致している
- [ ] `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`が設定されている
- [ ] Base64エンコードが正しく行われている
- [ ] サービスアカウントにスプレッドシートの編集権限がある

## 🔧 トラブルシューティング

### エラー: 環境変数 TEST_GOOGLE_SHEET_NAME が設定されていません

**原因**: GitHub Secretsに`TEST_GOOGLE_SHEET_NAME`が設定されていない

**解決方法**:
1. GitHub Secretsに`TEST_GOOGLE_SHEET_NAME`を追加
2. 値にテスト用スプレッドシート名を入力

### エラー: スプレッドシートが見つかりません

**原因**: 
- スプレッドシート名が間違っている
- サービスアカウントに共有されていない

**解決方法**:
1. Google Sheetsでスプレッドシート名を確認
2. スプレッドシートの共有設定でサービスアカウントのメールアドレスを追加
3. 編集権限を付与

### エラー: Base64デコードエラー

**原因**: Base64エンコードが正しくない

**解決方法**:
1. service_account.jsonファイルを再度Base64エンコード
2. 改行や余分な文字が含まれていないか確認
3. GitHub Secretsに再設定

## 📚 関連ドキュメント

- [Google Sheets設定ガイド](./setup/GOOGLE_SHEETS_SETUP.md)
- [環境変数設定ガイド](./ENV_SETUP.md)
- [CI/CDガイド](./CI_CD.md)