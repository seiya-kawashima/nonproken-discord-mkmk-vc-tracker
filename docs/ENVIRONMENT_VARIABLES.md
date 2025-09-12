# 環境変数の管理方針

## 📌 概要

このプロジェクトでは、環境ごとに異なる環境変数の管理方法を採用しています。

## 🔧 環境別の設定方法

### 1. 開発環境（ローカル）

**ファイル**: `.env`  
**場所**: プロジェクトルート  
**読み込み方法**: `python-dotenv`ライブラリで自動読み込み

```env
# Discord設定
DISCORD_BOT_TOKEN=your_discord_bot_token
ALLOWED_VOICE_CHANNEL_IDS=channel_id_1,channel_id_2

# Google Sheets設定
GOOGLE_SHEET_NAME=VC_Tracker_Dev
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json

# Slack設定（オプション）
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL_ID=your_slack_channel_id
```

### 2. テスト環境（GitHub Actions）

**設定場所**: GitHub Secrets  
**プレフィックス**: `TEST_`を付ける  
**用途**: Pull Request時の自動テスト

| 変数名 | 説明 |
|--------|------|
| `TEST_DISCORD_BOT_TOKEN` | テスト用Discord Botトークン |
| `TEST_ALLOWED_VOICE_CHANNEL_IDS` | テスト用VCチャンネルID |
| `TEST_GOOGLE_SHEET_NAME` | テスト用スプレッドシート名 |
| `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | Base64エンコードされた認証JSON |
| `TEST_SLACK_BOT_TOKEN` | テスト用Slack Botトークン |
| `TEST_SLACK_CHANNEL_ID` | テスト用Slackチャンネル |

### 3. 本番環境（GitHub Actions）

**設定場所**: GitHub Secrets  
**プレフィックス**: なし  
**用途**: 定期実行（本番運用）

| 変数名 | 説明 |
|--------|------|
| `DISCORD_BOT_TOKEN` | 本番用Discord Botトークン |
| `ALLOWED_VOICE_CHANNEL_IDS` | 本番用VCチャンネルID |
| `GOOGLE_SHEET_NAME` | 本番用スプレッドシート名 |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | Base64エンコードされた認証JSON |
| `SLACK_BOT_TOKEN` | 本番用Slack Botトークン |
| `SLACK_CHANNEL_ID` | 本番用Slackチャンネル |

## 📊 環境変数の優先順位

コード内では以下の優先順位で環境変数を読み込みます：

```python
# 例: Google Sheets名の読み込み
sheet_name = (
    os.getenv('TEST_GOOGLE_SHEET_NAME') or  # 1. テスト環境（最優先）
    os.getenv('GOOGLE_SHEET_NAME')           # 2. 本番/開発環境
)
```

## 🔐 Base64エンコードについて

GitHub ActionsではJSONファイルを直接保存できないため、Base64エンコードして保存します。

### エンコード方法

**Windows (PowerShell)**:
```powershell
# ファイルがあるフォルダで実行
cd C:\path\to\your\file
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "service_account.json" -Raw))) | Out-File "encoded.txt"
```

**Mac/Linux**:
```bash
base64 -i service_account.json | tr -d '\n' > encoded.txt
```

### デコード処理（自動）

GitHub Actions内で自動的にデコードされます：
```yaml
- name: Setup Google Service Account
  run: |
    echo "${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 }}" | base64 -d > service_account.json
```

## 🚀 環境の判定方法

コード内で現在の環境を判定する方法：

```python
# GitHub Actions環境かどうか
is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'

# テスト環境かどうか
is_test_env = bool(
    os.getenv('TEST_GOOGLE_SHEET_NAME') or 
    os.getenv('TEST_DISCORD_BOT_TOKEN')
)

# 環境名の取得
if is_test_env:
    env_name = "テスト環境"
elif is_github_actions:
    env_name = "本番環境"
else:
    env_name = "開発環境"
```

## 📝 設定チェックリスト

### 開発環境のセットアップ
- [ ] `.env`ファイルを作成
- [ ] Discord Bot トークンを設定
- [ ] Google Service Account JSONを配置
- [ ] スプレッドシート名を設定
- [ ] VCチャンネルIDを設定

### テスト環境のセットアップ
- [ ] GitHub Secretsに`TEST_DISCORD_BOT_TOKEN`を設定
- [ ] GitHub Secretsに`TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`を設定
- [ ] GitHub Secretsに`TEST_GOOGLE_SHEET_NAME`を設定
- [ ] GitHub Secretsに`TEST_ALLOWED_VOICE_CHANNEL_IDS`を設定

### 本番環境のセットアップ
- [ ] GitHub Secretsに`DISCORD_BOT_TOKEN`を設定
- [ ] GitHub Secretsに`GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`を設定
- [ ] GitHub Secretsに`GOOGLE_SHEET_NAME`を設定
- [ ] GitHub Secretsに`ALLOWED_VOICE_CHANNEL_IDS`を設定

## ⚠️ 注意事項

1. **`.env`ファイルは絶対にコミットしない**
   - `.gitignore`に含まれていることを確認

2. **トークンの取り扱い**
   - 本番用と開発用のトークンは必ず分ける
   - トークンをログに出力しない

3. **Base64エンコード**
   - GitHub Actions用の認証ファイルは必ずBase64エンコード
   - ローカルではそのままのJSONファイルを使用

## 🔍 トラブルシューティング

### 環境変数が読み込まれない
1. `.env`ファイルの配置場所を確認（プロジェクトルート）
2. `python-dotenv`がインストールされているか確認
3. GitHub Secretsの変数名を確認（大文字小文字も一致）

### Base64デコードエラー
1. エンコード時に改行が含まれていないか確認
2. 完全な文字列がコピーされているか確認
3. Windowsの場合は改行コードに注意

### 環境の判定が正しくない
1. `TEST_`プレフィックスの有無を確認
2. GitHub Actions内で実行されているか確認（`GITHUB_ACTIONS`環境変数）