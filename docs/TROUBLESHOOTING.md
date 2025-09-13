# トラブルシューティングガイド

## 📌 概要
このドキュメントは、プロジェクトで発生する可能性のあるエラーと、その解決方法をまとめたものです。

---

## 🔴 GitHub Actions関連のエラー

### エラー: `APIError: [403]: Request had insufficient authentication scopes`

#### 症状
```
❌ Google API エラー: APIError: [403]: Request had insufficient authentication scopes.
```

#### 原因
認証情報（サービスアカウントJSON）は正しく読み込まれているが、以下のいずれかの問題が発生している：

1. **Google Sheets APIが有効化されていない**
2. **スプレッドシートが存在しない、またはサービスアカウントに共有されていない**
3. **サービスアカウントの権限が不足している**

#### 解決方法

##### 1. Google Sheets APIを有効化する

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを選択
3. 「APIとサービス」→「ライブラリ」を開く
4. 「Google Sheets API」を検索
5. 「有効にする」ボタンをクリック

##### 2. スプレッドシートを作成・共有する

**スプレッドシート名（環境別）**：
- 本番環境: `VCトラッカー`
- テスト環境: `テスト用VCトラッカー`
- 開発環境: `開発VCトラッカー`

**共有手順**：
1. Google Sheetsで対応する名前のスプレッドシートを作成
2. 右上の「共有」ボタンをクリック
3. サービスアカウントのメールアドレスを入力
   - メールアドレスはservice_account.jsonの`client_email`フィールドに記載
   - 例: `your-service-account@your-project.iam.gserviceaccount.com`
4. 「編集者」権限を選択
5. 「送信」をクリック

##### 3. サービスアカウントの権限を確認する

1. Google Cloud Consoleで「IAMと管理」→「サービスアカウント」を開く
2. 該当のサービスアカウントを選択
3. 「権限」タブで以下のロールが付与されているか確認：
   - `編集者`または`オーナー`ロール
   - または最低限`Google Sheets API`の使用権限

---

### エラー: `環境変数 TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 が設定されていません`

#### 症状
```
❗ 設定エラー: テスト環境環境用の環境変数 TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 が設定されていません
```

#### 原因
GitHub Secretsに必要な環境変数が設定されていない

#### 解決方法

1. GitHubリポジトリの「Settings」タブを開く
2. 左メニューの「Secrets and variables」→「Actions」をクリック
3. 「New repository secret」をクリック
4. 以下を設定：
   - Name: `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`
   - Value: Base64エンコードされたサービスアカウントJSON

**Base64エンコード方法**：
```bash
# Linux/Mac
base64 -i service_account.json

# Windows PowerShell
[System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("service_account.json"))
```

---

### エラー: `スプレッドシートが見つかりません`

#### 症状
```
❌ エラー: スプレッドシート 'テスト用VCトラッカー' が見つかりません
```

#### 原因
1. スプレッドシート名が間違っている
2. スプレッドシートが存在しない
3. サービスアカウントに共有されていない

#### 解決方法

1. **スプレッドシート名を確認**
   - 環境ごとに決められた名前を使用する（大文字小文字も完全一致）
   - テスト環境: `テスト用VCトラッカー`

2. **スプレッドシートを作成**
   - Google Sheetsで新規スプレッドシートを作成
   - 正確な名前を設定

3. **共有設定を確認**
   - 上記「スプレッドシートを作成・共有する」の手順を参照

---

## 🟡 ローカル開発環境のエラー

### エラー: `ModuleNotFoundError: No module named 'gspread'`

#### 症状
```python
ModuleNotFoundError: No module named 'gspread'
```

#### 原因
必要なPythonパッケージがインストールされていない

#### 解決方法
```bash
pip install -r requirements.txt
```

---

### エラー: `.env`ファイルが見つからない

#### 症状
環境変数が読み込まれない

#### 原因
`.env`ファイルが存在しない、または正しい場所にない

#### 解決方法

1. プロジェクトルートに`.env`ファイルを作成
2. 以下の形式で環境変数を設定：

```env
# 本番環境用
DISCORD_BOT_TOKEN=your_discord_token
ALLOWED_VOICE_CHANNEL_IDS=123456789,987654321
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json

# テスト環境用（オプション）
TEST_DISCORD_BOT_TOKEN=test_discord_token
TEST_ALLOWED_VOICE_CHANNEL_IDS=111111111,222222222
TEST_GOOGLE_SERVICE_ACCOUNT_JSON=test_service_account.json
```

---

## 🔵 Discord関連のエラー

### エラー: `discord.errors.LoginFailure`

#### 症状
```
discord.errors.LoginFailure: Improper token has been passed.
```

#### 原因
Discord Botトークンが無効または期限切れ

#### 解決方法

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. アプリケーションを選択
3. 「Bot」セクションで「Reset Token」をクリック
4. 新しいトークンをコピー
5. 環境変数を更新

---

## 🟢 Google Sheets関連のエラー

### エラー: `gspread.exceptions.APIError: {'code': 429}`

#### 症状
```
gspread.exceptions.APIError: {'code': 429, 'message': 'Quota exceeded'}
```

#### 原因
Google Sheets APIのレート制限に達した

#### 解決方法

1. **待機する**
   - 1分間待ってから再試行

2. **リクエスト頻度を下げる**
   - コードにsleep()を追加してリクエスト間隔を空ける

3. **クォータを増やす**
   - Google Cloud Consoleで「APIとサービス」→「割り当て」から申請

---

## 🟣 認証関連のエラー

### エラー: Base64デコードエラー

#### 症状
```
❌ Base64デコードエラー: Incorrect padding
```

#### 原因
Base64エンコードされた文字列が不正

#### 解決方法

1. **再エンコード**
   ```bash
   # 正しくエンコードされているか確認
   base64 -i service_account.json | base64 -d
   ```

2. **改行や空白を除去**
   - Base64文字列に改行や余分な空白が含まれていないか確認
   - 1行の連続した文字列として設定

3. **文字列全体をコピー**
   - 部分的なコピーではなく、全体をコピーしているか確認

---

## 💡 デバッグのヒント

### GitHub Actionsのログを詳しく見る

1. GitHubリポジトリの「Actions」タブを開く
2. 失敗したワークフローをクリック
3. ジョブ名をクリック
4. 各ステップの「>」をクリックして詳細を確認

### ローカルでテストする

```bash
# テスト環境で実行
python test_config.py 1

# 認証テストを実行
python tests/auth_tests/test_google_sheets_ci.py
```

### 環境変数を確認する

```bash
# 設定されている環境変数を確認
python -c "from config import EnvConfig, Environment; print(EnvConfig.get_all_configs())"
```

---

## 📞 サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. エラーメッセージの全文
2. 実行したコマンド
3. 環境（ローカル/GitHub Actions）
4. 試した解決方法

[Issueを作成する](https://github.com/seiya-kawashima/nonproken-discord-mkmk-vc-tracker/issues/new)