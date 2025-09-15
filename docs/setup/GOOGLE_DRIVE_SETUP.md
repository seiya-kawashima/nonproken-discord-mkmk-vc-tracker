# Google Drive CSV セットアップガイド

## 📌 このガイドについて

Google Drive APIとサービスアカウントを設定し、CSVファイルでVCログを管理する手順を説明します。
所要時間：約15分

## 📊 Google DriveとCSVファイル管理とは？

- **Google Drive API**：プログラムからGoogle Driveにアクセスするためのインターフェース
- **CSVファイル**：カンマ区切りのシンプルなデータ形式（Excelでも開ける）
- **サービスアカウント**：プログラムがGoogleサービスにアクセスするための専用アカウント

このプロジェクトでは、VCログイン記録をGoogle Drive上のCSVファイルとして保存します。
**Google Sheetsの共有設定は不要**で、より簡単に運用できます。

## 📝 事前準備

- Googleアカウント（無料）
- ウェブブラウザ（Chrome、Firefox等）

## 🚀 セットアップ手順

### パート1：Google Cloud Projectの設定

#### ステップ1：Google Cloud Consoleにアクセス

1. [Google Cloud Console](https://console.cloud.google.com)を開く

2. Googleアカウントでログイン

3. 利用規約に同意（初回のみ）

#### ステップ2：新しいプロジェクトを作成

1. 画面上部のプロジェクト名が表示されている部分をクリック
   - 「**プロジェクトを選択**」と表示されている場合もあります

2. ポップアップウィンドウで「**新しいプロジェクト**」をクリック

3. プロジェクト情報を入力：
   - **プロジェクト名**：`VC-Tracker`
   - **場所**：「組織なし」のまま（個人アカウントの場合）

4. 「**作成**」をクリック

5. 作成完了まで約30秒待つ

#### ステップ3：Google Drive APIを有効化

1. 左側メニューから「**APIとサービス**」→「**ライブラリ**」を選択

2. 検索ボックスに「**Google Drive API**」と入力

3. 「**Google Drive API**」をクリック

4. 「**有効にする**」ボタンをクリック

5. 有効化完了まで約10秒待つ

⚠️ **確認方法**:
- 「**APIとサービス**」→「**有効なAPI**」でGoogle Drive APIが表示されていることを確認

### パート2：サービスアカウントの作成

#### ステップ1：サービスアカウントを作成

1. 左側メニューから「**IAMと管理**」→「**サービスアカウント**」を選択

2. 上部の「**+ サービスアカウントを作成**」をクリック

3. サービスアカウント詳細を入力：
   - **サービスアカウント名**：`vc-tracker-service`
   - **サービスアカウントID**：自動生成される
   - **説明**（オプション）：`VC Tracker用のサービスアカウント`

4. 「**作成して続行**」をクリック

5. ロール選択：**スキップでOK**（「続行」をクリック）
   - Google Drive APIは認証があれば使用可能

6. ユーザーアクセス：**スキップ**（「完了」をクリック）

#### ステップ2：キーを作成してダウンロード

1. 作成したサービスアカウントの**メールアドレスをクリック**

2. 「**キー**」タブを選択

3. 「**鍵を追加**」→「**新しい鍵を作成**」をクリック

4. キーのタイプ：「**JSON**」を選択

5. 「**作成**」をクリック

6. **JSONファイルが自動ダウンロードされる**
   - **このファイルを`service_account.json`にリネーム**

⚠️ **重要な注意事項**：
- このJSONファイルは**二度とダウンロードできません**
- 安全な場所に保管してください
- GitHubにコミットしないでください

## 🔐 認証情報の保管方法

### 開発環境（ローカル）

1. プロジェクトルートに`service_account.json`を配置

2. `.env`ファイルに設定：
```env
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
```

### GitHub Actions用（Base64エンコード）

サービスアカウントのJSONファイルをGitHub Actionsで使用するには、Base64エンコードが必要です。

📖 **詳細な手順は[サービスアカウント Base64エンコード共通ガイド](SERVICE_ACCOUNT_BASE64.md)を参照してください。**

**クイックリファレンス**:
- Secret名: `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`（本番用）

## ✅ 動作確認

### CSVファイルの自動作成

プログラムを実行すると、Google Drive上に自動的に以下が作成されます：

1. **`VC_Tracker_Data`フォルダ**
   - 初回実行時に自動作成
   - 手動での作成は不要

2. **VCチャンネルごとのCSVファイル**
   - 例：`general-voice.csv`、`study-room.csv`
   - 各VCチャンネルごとに個別のファイル

### CSVファイルの形式

```csv
datetime_jst,user_id,user_name,present
2025/9/11 10:30,111111111111111111,kawashima#1234,TRUE
2025/9/11 10:30,222222222222222222,tanaka#5678,TRUE
```

### ローカルでテストする場合

```python
from src.drive_csv_client import DriveCSVClient

# クライアントを初期化
client = DriveCSVClient('service_account.json')
client.connect()

# テストデータを書き込み
members = [{
    'vc_name': 'test-channel',
    'user_id': '123456789',
    'user_name': 'test_user'
}]
result = client.upsert_presence(members)
print(f"結果: {result}")
```

## 🚨 トラブルシューティング

### よくあるエラーと対処法

#### 1. 「Google Drive API has not been used」エラー

**原因**：Google Drive APIが有効化されていない

**対処**：
1. [Google Cloud Console](https://console.cloud.google.com)にアクセス
2. 「APIとサービス」→「ライブラリ」を選択
3. 「Google Drive API」を検索して有効化

#### 2. 「Invalid grant」エラー

**原因**：サービスアカウントキーが無効

**対処**：
- 新しいキーを作成してダウンロード
- 時刻設定が正しいか確認

#### 3. Base64デコードエラー

**原因**：Base64エンコードされた文字列が不正

**対処**：
- 改行や空白を除去
- 文字列全体をコピーしているか確認

## 💡 メリット

### Google Sheetsと比較して

1. **設定が簡単**
   - スプレッドシートの作成不要
   - 共有設定不要
   - フォルダが自動作成される

2. **制限が少ない**
   - Sheets APIのレート制限を受けない
   - セル数制限なし

3. **管理が楽**
   - VCごとに個別ファイル
   - CSVなのでExcelでも開ける
   - バックアップが簡単

## ❓ よくある質問

### Q: Google Driveの容量制限は？
A: 無料枠は15GBです。CSVファイルは非常に小さいため、数年分のデータでも問題ありません。

### Q: CSVファイルを直接編集できますか？
A: はい、Google DriveからダウンロードしてExcelで編集可能です。ただし、フォーマットは変更しないでください。

### Q: フォルダが見つからない
A: プログラム初回実行時に自動作成されます。手動作成は不要です。

### Q: 複数のVCチャンネルのデータは？
A: 各VCチャンネルごとに個別のCSVファイルが作成されます。

## 📚 参考リンク

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Google Cloud Console](https://console.cloud.google.com)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-for-using-service-accounts)

## 🔐 共有ドライブの設定（オプション）

### Google Drive共有ドライブを使用する場合

組織でGoogle Workspace（旧G Suite）を利用している場合は、共有ドライブを使用できます。

#### 共有ドライブへのサービスアカウント追加手順

##### 方法1: Google Drive Web UIから追加（推奨）

1. **Google Driveにアクセス**
   - https://drive.google.com にアクセス
   - 組織のGoogleアカウントでログイン

2. **共有ドライブを開く**
   - 左側メニューから「共有ドライブ」をクリック
   - 対象の共有ドライブを選択

3. **メンバー管理画面を開く**
   - 共有ドライブ名の右側にある「⋮」（3点メニュー）をクリック
   - 「メンバーを管理」を選択

4. **サービスアカウントを追加**
   - 「メンバーを追加」ボタンをクリック
   - サービスアカウントのメールアドレスを入力（JSONファイル内の`client_email`フィールドの値）
   - 権限レベルを選択：
     - **コンテンツ管理者**（推奨）: ファイルの作成・編集・削除が可能
     - **投稿者**: ファイルの作成・編集が可能（削除は不可）

5. **設定を保存**
   - 「送信」をクリック
   - メンバーリストにサービスアカウントが追加されたことを確認

##### 環境変数の設定

共有ドライブを使用する場合は、`.env`ファイルに共有ドライブIDを設定：

```env
# 共有ドライブID（URLから取得）
# URL例: https://drive.google.com/drive/folders/0ANixFe4JBQskUk9PVA
GOOGLE_SHARED_DRIVE_ID=0ANixFe4JBQskUk9PVA
```

### 既存のGoogle Driveフォルダを共有する場合

個人のGoogle Driveを使用する場合は、フォルダをサービスアカウントと共有します。

1. **Google Driveでフォルダを作成**
   - Google Driveにアクセス
   - 「discord_mokumoku_tracker」というフォルダを作成

2. **サービスアカウントに共有権限を付与**
   - 作成したフォルダを右クリック → 「共有」
   - サービスアカウントのメールアドレスを入力
   - 「編集者」権限を付与

3. **環境変数の設定**
   ```env
   # 共有ドライブIDは空のままにする
   GOOGLE_SHARED_DRIVE_ID=
   ```

### サービスアカウントの制限事項について

⚠️ **重要**：Google Driveのサービスアカウントには**ストレージ容量がありません**。そのため、以下のいずれかの方法で設定する必要があります：

- **共有ドライブを使用**（組織アカウントの場合）
- **既存のGoogle Driveフォルダを共有**（個人アカウントの場合）

### 共有ドライブのトラブルシューティング

#### エラー: `teamDriveMembershipRequired`
**原因**: サービスアカウントが共有ドライブのメンバーではない
**解決策**: 上記手順でサービスアカウントを追加

#### エラー: `insufficientPermissions`
**原因**: サービスアカウントの権限が不足
**解決策**: 「コンテンツ管理者」権限に変更

#### エラー: `notFound`
**原因**: 共有ドライブIDが間違っている
**解決策**: URLから正しい共有ドライブIDを確認

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. エラーメッセージの全文
2. 実行したコード
3. Google Cloud Consoleの設定スクリーンショット
4. 共有ドライブまたはフォルダの共有設定スクリーンショット（該当する場合）