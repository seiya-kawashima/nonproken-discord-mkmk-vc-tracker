# 認証テスト

このディレクトリには、各サービスの認証・接続をテストするスクリプトが含まれています。

## 📁 ファイル構成

- `test_google_sheets_auth.py` - Google Sheets認証・接続テスト
- （今後追加予定）`test_discord_auth.py` - Discord Bot認証テスト
- （今後追加予定）`test_slack_auth.py` - Slack Bot認証テスト

## 🚀 使い方

### ローカルでの実行

```bash
# プロジェクトルートから実行
python tests/auth_tests/test_google_sheets_auth.py
```

### GitHub Actionsでの実行

#### 方法1: 手動実行（推奨）
1. GitHubリポジトリの「Actions」タブを開く
2. 左側のワークフロー一覧から「Authentication Tests」を選択
3. 右側の「Run workflow」ボタンをクリック
4. ブランチを選択して「Run workflow」を実行

#### 方法2: 自動実行
以下の条件で自動的に実行されます：
- Pull Request作成時（認証テスト関連ファイルの変更時）
- main/masterブランチへのpush時（認証テスト関連ファイルの変更時）

### 必要なGitHub Secrets設定

テスト環境用：
- `TEST_GOOGLE_SHEET_NAME` - テスト用スプレッドシート名
- `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` - Base64エンコードされた認証JSON

本番環境用：
- `GOOGLE_SHEET_NAME` - 本番用スプレッドシート名
- `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` - Base64エンコードされた認証JSON

このテストスクリプトは以下を確認します：
- 開発環境（.envファイル）の設定
- テスト環境（TEST_プレフィックス付き）の設定
- 本番環境（プレフィックスなし）の設定

## 📊 テスト結果

各環境のテストデータは、スプレッドシートの異なる場所に書き込まれます：
- 開発環境: A1:B3
- テスト環境: D1:E3
- 本番環境: G1:H3

## ⚠️ 注意事項

- これらのテストスクリプトは実際のサービスに接続します
- 適切な認証情報が設定されていることを確認してください
- テスト実行前に`config.py`で環境変数の設定を確認してください