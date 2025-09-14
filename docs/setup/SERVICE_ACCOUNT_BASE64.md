# サービスアカウント Base64エンコード共通ガイド

## 📌 このガイドについて

サービスアカウントのJSONファイルをBase64エンコードしてGitHub Secretsに登録する共通手順です。
Google SheetsとGoogle Driveの両方のセットアップで使用します。

## 🔐 Base64エンコードとは？

**Base64エンコードとは？**
- 簡単に言うと「**ファイルを安全な文字列に変換する方法**」です
- 例えば、日本語や改行、特殊記号を含むファイルを、英数字だけの文字列に変換します
- 変換前：複雑なJSONファイル（改行や記号がたくさん）
- 変換後：`eyJ0eXBlIjoic2VydmljZV9hY2NvdW50I...`（英数字の羅列）

**なぜGitHub Actionsで必要？**
- GitHub Secretsは「1行のテキスト」しか保存できない仕様
- JSONファイルは複数行で特殊文字も含むため、そのまま保存不可
- Base64エンコードで1行の安全な文字列に変換することで保存可能に

## 📝 Base64エンコード手順

### 1. JSONファイルをBase64エンコード（文字列に変換）

#### Windows (PowerShell)の場合

最も確実な方法: Get-Contentを使用
```powershell
# まずファイルがあるフォルダに移動
cd C:\Users\ユーザー名\Downloads

# Base64エンコード（この方法が最も確実）
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "service_account.json" -Raw))) | Out-File "encoded.txt"
```

**もっと簡単な方法（Windows）**：
- オンライン変換ツール（https://www.base64encode.org/）を使用
- service_account.jsonの内容をコピーして貼り付け
- 「Encode」ボタンをクリック
- 結果をコピー

#### Mac/Linuxの場合
```bash
# ターミナルでservice_account.jsonがあるフォルダで実行
base64 -i service_account.json | tr -d '\n' > encoded.txt
```

### 2. エンコードされた文字列を確認

- `encoded.txt`ファイルを開く
- 長い1行の文字列（英数字の羅列）になっていることを確認
- 例：`eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6...`

### 3. encoded.txtの内容を全てコピー

### 4. GitHub Secretsに登録

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」をクリック
3. 設定内容：
   - **Name**: 用途に応じて以下から選択
     - `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`（本番用）
     - `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`（テスト用）
   - **Secret**: コピーした文字列を貼り付け
4. 「Add secret」をクリック

## ⚠️ 重要な注意事項

- このJSONファイルは**二度とダウンロードできません**
- 安全な場所に保管してください
- GitHubにコミットしないでください（`.gitignore`に追加済み）
- Base64エンコードされた文字列も機密情報です

## 🚨 トラブルシューティング

### Base64デコードエラー

**原因**：Base64エンコードされた文字列が不正

**対処**：
- 改行や空白を除去
- 文字列全体をコピーしているか確認
- 再度エンコードし直す

### 「Invalid grant」エラー

**原因**：サービスアカウントキーが無効

**対処**：
- 新しいキーを作成してダウンロード
- 時刻設定が正しいか確認
- プロジェクトIDが正しいか確認

## 📚 参考リンク

- [Base64エンコードとは（Wikipedia）](https://ja.wikipedia.org/wiki/Base64)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)