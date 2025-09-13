# 環境別セットアップガイド

## 📌 概要

このプロジェクトは3つの環境で動作します：
- **PRD（本番環境）**: 実際の運用で使用
- **TST（テスト環境）**: CI/CDで自動テスト実行
- **DEV（開発環境）**: ローカル開発で使用

## 🔧 環境ごとの設定

### 1. PRD（本番環境）

#### Google Sheets設定
1. **スプレッドシート作成**
   - Google Sheetsで新規スプレッドシートを作成
   - 名前を `VCトラッカー` に設定
   - URLをメモ（例: `https://docs.google.com/spreadsheets/d/本番用ID/edit`）

2. **サービスアカウント作成**
   - Google Cloud Consoleで本番用のサービスアカウントを作成
   - JSONキーをダウンロード（例: `prd_service_account.json`）
   - Base64エンコード:
     ```bash
     # Mac/Linux
     base64 -i prd_service_account.json | tr -d '\n' > prd_encoded.txt
     
     # Windows PowerShell
     [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "prd_service_account.json" -Raw))) | Out-File "prd_encoded.txt"
     ```

3. **スプレッドシート共有**
   - 作成したスプレッドシートを開く
   - 右上の「共有」ボタンをクリック
   - サービスアカウントのメールアドレスを追加（`client_email`フィールドの値）
   - 「編集者」権限を付与

#### GitHub Secrets設定（PRD用）
| Secret名 | 説明 | 値の例 |
|----------|------|--------|
| `DISCORD_BOT_TOKEN` | 本番Discord Botトークン | 本番用Botのトークン |
| `ALLOWED_VOICE_CHANNEL_IDS` | 本番VCチャンネルID | `123456789,987654321` |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | 本番用認証JSONのBase64 | `prd_encoded.txt`の内容 |
| `SLACK_BOT_TOKEN` | 本番Slack Botトークン（オプション） | 本番用Slackトークン |
| `SLACK_CHANNEL_ID` | 本番Slackチャンネル（オプション） | 本番用チャンネルID |

### 2. TST（テスト環境）

#### Google Sheets設定
1. **スプレッドシート作成**
   - Google Sheetsで新規スプレッドシートを作成
   - 名前を `VCトラッカー` に設定（PRDと同じ名前だが別ファイル）
   - URLをメモ（例: `https://docs.google.com/spreadsheets/d/テスト用ID/edit`）

2. **サービスアカウント作成**
   - Google Cloud Consoleでテスト用のサービスアカウントを作成
   - JSONキーをダウンロード（例: `tst_service_account.json`）
   - Base64エンコード:
     ```bash
     # Mac/Linux
     base64 -i tst_service_account.json | tr -d '\n' > tst_encoded.txt
     
     # Windows PowerShell
     [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "tst_service_account.json" -Raw))) | Out-File "tst_encoded.txt"
     ```

3. **スプレッドシート共有**
   - テスト用スプレッドシートを開く
   - 右上の「共有」ボタンをクリック
   - テスト用サービスアカウントのメールアドレスを追加
   - 「編集者」権限を付与

#### GitHub Secrets設定（TST用）
| Secret名 | 説明 | 値の例 |
|----------|------|--------|
| `TST_DISCORD_BOT_TOKEN` | テストDiscord Botトークン | テスト用Botのトークン |
| `TST_ALLOWED_VOICE_CHANNEL_IDS` | テストVCチャンネルID | `111111111,222222222` |
| `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | テスト用認証JSONのBase64 | `tst_encoded.txt`の内容 |
| `TST_SLACK_BOT_TOKEN` | テストSlack Botトークン（オプション） | テスト用Slackトークン |
| `TST_SLACK_CHANNEL_ID` | テストSlackチャンネル（オプション） | テスト用チャンネルID |

### 3. DEV（開発環境）

#### ローカル設定
1. **`.env`ファイル作成**
   ```env
   # Discord設定
   DISCORD_BOT_TOKEN=開発用Botトークン
   ALLOWED_VOICE_CHANNEL_IDS=開発用チャンネルID
   
   # Google Sheets設定
   GOOGLE_SERVICE_ACCOUNT_JSON=dev_service_account.json
   
   # Slack設定（オプション）
   SLACK_BOT_TOKEN=開発用Slackトークン
   SLACK_CHANNEL_ID=開発用チャンネルID
   ```

2. **開発用スプレッドシート作成**
   - 名前を `VCトラッカー` に設定
   - 開発用サービスアカウントに共有

## 📊 環境の切り替え方法

### コマンドラインでの指定
```bash
# 本番環境（PRD）
python poll_once.py --env 0

# テスト環境（TST）
python poll_once.py --env 1

# 開発環境（DEV）
python poll_once.py --env 2

# 環境指定なし（デフォルトはPRD）
python poll_once.py
```

### GitHub Actionsでの自動判定
- Pull Request時: TST環境を自動使用
- 定期実行時: PRD環境を自動使用

## 🔍 トラブルシューティング

### Q: なぜ環境ごとに別のスプレッドシートファイルが必要？
**A**: テストデータと本番データを完全に分離するためです。これにより：
- テストが本番データを破壊するリスクを排除
- 環境ごとに異なる権限管理が可能
- データの監査証跡を明確化

### Q: スプレッドシート名が全て同じなのはなぜ？
**A**: コードの簡潔性のためです。環境の違いは認証情報（サービスアカウント）で管理し、コード内では統一された名前を使用します。

### Q: TST_プレフィックスの意味は？
**A**: GitHub Secretsで環境を明確に区別するためです：
- プレフィックスなし = PRD（本番）
- TST_ = テスト環境
- ローカルの.envファイルはプレフィックス不要

## 📝 チェックリスト

### PRD環境セットアップ
- [ ] 本番用Google Sheetsスプレッドシート作成（名前: `VCトラッカー`）
- [ ] 本番用サービスアカウント作成
- [ ] スプレッドシートに本番用サービスアカウントを共有
- [ ] GitHub Secretsに本番用設定を登録（プレフィックスなし）

### TST環境セットアップ
- [ ] テスト用Google Sheetsスプレッドシート作成（名前: `VCトラッカー`）
- [ ] テスト用サービスアカウント作成
- [ ] スプレッドシートにテスト用サービスアカウントを共有
- [ ] GitHub SecretsにTST_プレフィックス付きで設定を登録

### DEV環境セットアップ
- [ ] 開発用Google Sheetsスプレッドシート作成（名前: `VCトラッカー`）
- [ ] 開発用サービスアカウント作成
- [ ] `.env`ファイル作成
- [ ] `.gitignore`に`.env`が含まれていることを確認