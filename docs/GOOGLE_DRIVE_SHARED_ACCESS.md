# Google Drive 共有ドライブへのサービスアカウント追加手順書

## 📌 このドキュメントについて
Discord VC TrackerがGoogle Drive共有ドライブにアクセスするために、サービスアカウントを共有ドライブのメンバーとして追加する手順を説明します。

## 🎯 必要な理由
- **エラー内容**: `The attempted action requires shared drive membership`
- **原因**: サービスアカウントが共有ドライブのメンバーではない
- **解決策**: サービスアカウントを共有ドライブに追加する

## 📋 前提条件
- Google Driveの共有ドライブへの管理者アクセス権限
- サービスアカウントのメールアドレス（JSONファイル内の`client_email`）

## 🔧 サービスアカウントのメールアドレス確認方法

### 1. サービスアカウントJSONファイルを開く
```bash
# Windowsの場合（メモ帳で開く）
notepad C:\Users\SeiyaKawashima\Downloads\service_account.json

# または、Pythonで確認
python -c "import json; print(json.load(open(r'C:\Users\SeiyaKawashima\Downloads\service_account.json'))['client_email'])"
```

### 2. `client_email`フィールドを確認
```json
{
  "type": "service_account",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  ...
}
```
この`client_email`の値をコピーしておきます。

## 📝 共有ドライブへのメンバー追加手順

### 方法1: Google Drive Web UIから追加（推奨）

1. **Google Driveにアクセス**
   - https://drive.google.com にアクセス
   - 組織のGoogleアカウントでログイン

2. **共有ドライブを開く**
   - 左側メニューから「共有ドライブ」をクリック
   - 対象の共有ドライブを選択（例：`discord_mokumoku_tracker`）

3. **メンバー管理画面を開く**
   - 共有ドライブ名の右側にある「⋮」（3点メニュー）をクリック
   - 「メンバーを管理」を選択

4. **サービスアカウントを追加**
   - 「メンバーを追加」ボタンをクリック
   - サービスアカウントのメールアドレスを入力
     ```
     例: your-service-account@your-project.iam.gserviceaccount.com
     ```
   - 権限レベルを選択：
     - **コンテンツ管理者**（推奨）: ファイルの作成・編集・削除が可能
     - **投稿者**: ファイルの作成・編集が可能（削除は不可）
     - **閲覧者**: 読み取り専用

5. **設定を保存**
   - 「送信」または「完了」をクリック
   - メンバーリストにサービスアカウントが追加されたことを確認

### 方法2: Google Drive APIから追加（上級者向け）

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 管理者権限を持つアカウントの認証情報を使用
creds = service_account.Credentials.from_service_account_file(
    'admin_service_account.json',
    scopes=['https://www.googleapis.com/auth/drive']
)

service = build('drive', 'v3', credentials=creds)

# 共有ドライブID
shared_drive_id = '0ANixFe4JBQskUk9PVA'

# サービスアカウントのメールアドレス
service_account_email = 'your-service-account@your-project.iam.gserviceaccount.com'

# 権限を追加
permission = {
    'type': 'user',
    'role': 'fileOrganizer',  # または 'writer', 'reader'
    'emailAddress': service_account_email
}

service.permissions().create(
    fileId=shared_drive_id,
    body=permission,
    supportsAllDrives=True
).execute()

print(f"サービスアカウント {service_account_email} を共有ドライブに追加しました")
```

## ✅ 動作確認

### 1. 環境変数の確認
`.env`ファイルで以下が設定されていることを確認：
```bash
# 開発環境の場合
DEV_GOOGLE_SHARED_DRIVE_ID=0ANixFe4JBQskUk9PVA
DEV_GOOGLE_SERVICE_ACCOUNT_JSON=C:\Users\SeiyaKawashima\Downloads\service_account.json
```

### 2. プログラムの実行
```bash
# 開発環境で実行
python poll_once.py --env 2
```

### 3. 成功時のログ
```
2025-09-15 20:44:10,169 - __main__ - INFO - Connecting to Google Drive...
2025-09-15 20:44:11,234 - src.drive_csv_client - INFO - Connected to Google Drive successfully
2025-09-15 20:44:11,456 - __main__ - INFO - Recording presence data to CSV...
2025-09-15 20:44:11,789 - __main__ - INFO - Recorded: 3 new, 0 updated
```

## ❗ トラブルシューティング

### エラー: `teamDriveMembershipRequired`
**原因**: サービスアカウントが共有ドライブのメンバーではない
**解決策**: 上記手順でサービスアカウントを追加

### エラー: `insufficientPermissions`
**原因**: サービスアカウントの権限が不足
**解決策**: 「コンテンツ管理者」権限に変更

### エラー: `notFound`
**原因**: 共有ドライブIDが間違っている
**解決策**:
1. Google Driveで共有ドライブを開く
2. URLから共有ドライブIDを確認
   ```
   https://drive.google.com/drive/folders/0ANixFe4JBQskUk9PVA
                                           ^^^^^^^^^^^^^^^^^^^
                                           この部分が共有ドライブID
   ```

## 🔒 セキュリティ上の注意事項

1. **最小権限の原則**
   - 必要最小限の権限のみを付与
   - 本番環境では「投稿者」権限で十分な場合が多い

2. **定期的な監査**
   - 不要になったサービスアカウントは削除
   - メンバーリストを定期的に確認

3. **サービスアカウントキーの管理**
   - JSONファイルは安全な場所に保管
   - Gitリポジトリにコミットしない
   - 定期的にキーをローテーション

## 📚 参考リンク

- [Google Drive API - 共有ドライブの管理](https://developers.google.com/drive/api/guides/manage-shareddrives)
- [サービスアカウントの作成と管理](https://cloud.google.com/iam/docs/creating-managing-service-accounts)
- [共有ドライブのベストプラクティス](https://support.google.com/a/answer/7212025)

## 💡 代替案：マイドライブを使用する

共有ドライブへのアクセス権限が取得できない場合は、マイドライブを使用することも可能です：

### 設定変更
`.env`ファイルで共有ドライブIDを空にする：
```bash
# 開発環境でマイドライブを使用
DEV_GOOGLE_SHARED_DRIVE_ID=
```

この設定により、サービスアカウントのマイドライブにファイルが保存されます。