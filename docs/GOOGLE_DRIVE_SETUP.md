# Google Drive CSV設定ガイド

## ⚠️ 重要：サービスアカウントの制限事項

Google Driveのサービスアカウントには**ストレージ容量がありません**。そのため、以下のいずれかの方法で設定する必要があります。

## 📋 設定方法

### 方法1：既存のGoogle Driveフォルダを共有（推奨）

1. **Google Driveでフォルダを作成**
   - Google Driveにアクセス
   - 「discord_mokumoku_tracker」というフォルダを作成

2. **サービスアカウントに共有権限を付与**
   - 作成したフォルダを右クリック → 「共有」
   - サービスアカウントのメールアドレスを入力（例：`your-service-account@your-project.iam.gserviceaccount.com`）
   - 「編集者」権限を付与

3. **フォルダIDを取得**
   - フォルダを開いてURLからIDをコピー
   - URL例：`https://drive.google.com/drive/folders/1ABC123...`
   - IDは「1ABC123...」の部分

4. **環境変数に設定**
   ```bash
   GOOGLE_DRIVE_PARENT_FOLDER_ID=1ABC123...
   ```

### 方法2：共有ドライブ（Shared Drive）を使用

Google Workspace（旧G Suite）を利用している場合は、共有ドライブを使用できます。

1. **共有ドライブを作成**
   - Google Driveで「共有ドライブ」を作成

2. **サービスアカウントを追加**
   - 共有ドライブの設定でサービスアカウントを「コンテンツ管理者」として追加

3. **共有ドライブIDを環境変数に設定**
   ```bash
   GOOGLE_SHARED_DRIVE_ID=0ABC123...
   ```

## 🔧 DriveCSVClientの修正が必要

現在のコードはサービスアカウントが直接ファイルを作成しようとしているため、上記の設定に合わせて修正が必要です。

## 📝 必要な環境変数まとめ

```bash
# サービスアカウント認証情報
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
# または
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=base64エンコードされた認証情報

# 以下のいずれか
# 方法1の場合：共有されたフォルダのID
GOOGLE_DRIVE_PARENT_FOLDER_ID=フォルダID

# 方法2の場合：共有ドライブのID
GOOGLE_SHARED_DRIVE_ID=共有ドライブID
```

## ⚠️ トラブルシューティング

### エラー：「Service Accounts do not have storage quota」
- **原因**：サービスアカウントが直接ファイルを作成しようとしている
- **解決**：上記の方法1または方法2を実施

### エラー：「Permission denied」
- **原因**：サービスアカウントに適切な権限がない
- **解決**：フォルダの共有設定で「編集者」権限を付与

## 🔗 参考リンク

- [Google Drive API - 共有ドライブについて](https://developers.google.com/drive/api/guides/about-shareddrives)
- [サービスアカウントの使用](https://developers.google.com/identity/protocols/oauth2/service-account)
- [OAuth委任について](http://support.google.com/a/answer/7281227)