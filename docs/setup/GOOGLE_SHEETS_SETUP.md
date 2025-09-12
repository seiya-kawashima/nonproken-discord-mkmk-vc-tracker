# Google Sheets セットアップガイド

## 📌 このガイドについて

Google Sheetsとサービスアカウントを設定し、プログラムからアクセスできるようにする手順を説明します。
所要時間：約20分

## 📊 Google Sheetsとサービスアカウントとは？

- **Google Sheets**：Googleが提供する無料のオンライン表計算ソフト
- **サービスアカウント**：プログラムがGoogleサービスにアクセスするための専用アカウント（人間用ではない）

このプロジェクトでは、VCログイン記録をGoogle Sheetsに保存するために使用します。

## 📝 事前準備

- Googleアカウント（無料）
- ウェブブラウザ（Chrome、Firefox等）

## 🚀 セットアップ手順

### パート1：Google Sheetsの準備

#### ステップ1：新しいスプレッドシートを作成

1. [Google Sheets](https://sheets.google.com)にアクセス

2. 「**空白**」をクリックして新規スプレッドシート作成

3. スプレッドシート名を変更：
   - 本番用例：`VC_Tracker_Database`
   - テスト用例：`VC_Tracker_Test`
   
   （左上の「無題のスプレッドシート」をクリックして変更）

4. **URLをメモしておく**（後で使用）
   ```
   例：https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit
   ```

### パート2：Google Cloud Projectの設定

#### ステップ1：Google Cloud Consoleにアクセス

1. [Google Cloud Console](https://console.cloud.google.com)を開く

2. Googleアカウントでログイン

3. 利用規約に同意（初回のみ）

#### ステップ2：新しいプロジェクトを作成

1. 画面上部のプロジェクト名が表示されている部分をクリック
   - 「**プロジェクトを選択**」と表示されている場合もあります
   - 既存のプロジェクト名（例：「My First Project」）が表示されている場合もあります

2. ポップアップウィンドウが開いたら：
   - **「新しいプロジェクト」ボタンを探す**：
     - ウィンドウの右上にある場合
     - プロジェクト一覧の上部にある場合
   - 見つからない場合は、プロジェクト一覧から「**すべて**」タブを選択すると表示される場合があります

3. 「**新しいプロジェクト**」をクリック

4. プロジェクト情報を入力：
   - **プロジェクト名**：
     - 例：`VC-Tracker`
   - **場所**：「組織なし」のまま（個人アカウントの場合）

5. 「**作成**」をクリック

6. 作成完了まで約30秒待つ（通知が表示されます）

#### ステップ3：Google Sheets APIを有効化

1. 左側メニューから「**APIとサービス**」→「**ライブラリ**」を選択

2. 検索ボックスに「**Google Sheets API**」と入力

3. 「**Google Sheets API**」をクリック

4. 「**有効にする**」ボタンをクリック

5. 有効化完了まで約10秒待つ

### パート3：サービスアカウントの作成

#### ステップ1：サービスアカウントを作成

1. 左側メニューから「**IAMと管理**」→「**サービスアカウント**」を選択
   - または「**APIとサービス**」→「**認証情報**」から「**サービスアカウント**」セクションの「**サービスアカウントを管理**」をクリック

2. 上部の「**+ サービスアカウントを作成**」をクリック

3. サービスアカウント詳細を入力：
   - **サービスアカウント名**：
     - 例：`vc-tracker-service`
   - **サービスアカウントID**：自動生成される
   - **説明**（オプション）：
     - 例：`VC Tracker用のサービスアカウント`

4. 「**作成して続行**」をクリック

5. 「**このサービスアカウントにプロジェクトへのアクセスを許可**」（ロール選択）：
   - **基本的にスキップでOK**（「続行」をクリック）
   - 理由：Google Sheetsへのアクセス権限は2つの方法で設定できます：
     1. **推奨方法（このガイドで使用）**：スプレッドシート側で個別に共有設定する
     2. 代替方法：ここで「編集者」ロールを付与する（プロジェクト全体への権限となるため過剰）
   - このプロジェクトでは、必要最小限の権限にするため、スプレッドシート個別の共有設定を使用します

6. 「**ユーザーにこのサービスアカウントへのアクセスを許可**」（省略可能）：
   - **こちらもスキップ**（「完了」をクリック）
   - 理由：このサービスアカウントを他のユーザーが管理する必要がない場合は設定不要です

#### ステップ2：キーを作成してダウンロード

1. 作成したサービスアカウントの**メールアドレスをクリック**
   ```
   例：vc-tracker-service@vc-tracker-123456.iam.gserviceaccount.com
   ```

2. 「**キー**」タブを選択

3. 「**鍵を追加**」→「**新しい鍵を作成**」をクリック

4. キーのタイプ：「**JSON**」を選択

5. 「**作成**」をクリック

6. **JSONファイルが自動ダウンロードされる**
   - ファイル名例：`vc-tracker-123456-abcdef123456.json`
   - **このファイルを`service_account.json`にリネーム**

⚠️ **重要な注意事項**：
- このJSONファイルは**二度とダウンロードできません**
- 安全な場所に保管してください
- GitHubにコミットしないでください
- 他人と共有しないでください

### パート4：スプレッドシートへのアクセス権限を付与

#### ステップ1：サービスアカウントのメールアドレスをコピー

1. Google Cloud Consoleに戻る
   - 左上の三本線メニュー（ハンバーガーメニュー）をクリック
   - 「**APIとサービス**」→「**認証情報**」を選択
   - または「**IAMと管理**」→「**サービスアカウント**」からも確認可能

2. サービスアカウントの**メールアドレスをコピー**
   ```
   例：vc-tracker-service@vc-tracker-123456.iam.gserviceaccount.com
   ```

#### ステップ2：スプレッドシートを共有（重要：ここで実際の権限を設定）

1. 作成したGoogle Sheetsを開く

2. 右上の「**共有**」ボタンをクリック

3. サービスアカウントのメールアドレスを貼り付け

4. **権限を「編集者」に設定**（重要）
   - **編集者**：データの読み取り・書き込みが可能（このプロジェクトで必要）
   - 閲覧者：読み取りのみ（書き込みができないため使用不可）
   - コメント可：コメントのみ（データ書き込みができないため使用不可）

5. 「**通知を送信する**」のチェックを**外す**（重要！）
   - サービスアカウントはメールを受信できないため

6. 「**共有**」をクリック

7. 「**このユーザーに通知メールを送信しますか？**」と聞かれたら「**共有**」をクリック

## 🔐 認証情報の保管方法

### 開発環境（ローカル）

1. プロジェクトルートに`service_account.json`を配置

2. `.env`ファイルに設定：
```env
GOOGLE_SERVICE_ACCOUNT_JSON=service_account.json
GOOGLE_SHEET_NAME=VC_Tracker_Test
```

### GitHub Actions用（Base64エンコード）

**Base64エンコードとは？**
- 簡単に言うと「**ファイルを安全な文字列に変換する方法**」です
- 例えば、日本語や改行、特殊記号を含むファイルを、英数字だけの文字列に変換します
- 変換前：複雑なJSONファイル（改行や記号がたくさん）
- 変換後：`eyJ0eXBlIjoic2VydmljZV9hY2NvdW50I...`（英数字の羅列）

**なぜGitHub Actionsで必要？**
- GitHub Secretsは「1行のテキスト」しか保存できない仕様
- JSONファイルは複数行で特殊文字も含むため、そのまま保存不可
- Base64エンコードで1行の安全な文字列に変換することで保存可能に

1. **JSONファイルをBase64エンコード（文字列に変換）**：

   **Windows (PowerShell)の場合**：
   
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

   **Mac/Linuxの場合**：
   ```bash
   # ターミナルでservice_account.jsonがあるフォルダで実行
   base64 -i service_account.json | tr -d '\n' > encoded.txt
   ```

2. **エンコードされた文字列を確認**：
   - `encoded.txt`ファイルを開く
   - 長い1行の文字列（英数字の羅列）になっていることを確認
   - 例：`eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6...`

3. **encoded.txtの内容を全てコピー**

4. **GitHub Secretsに登録**：
   - GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
   - 「New repository secret」をクリック
   - Name: `TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`（テスト用）
   - Secret: コピーした文字列を貼り付け
   - 「Add secret」をクリック

## ✅ 動作確認

### このセクションについて
**このテストコードは参考例です。実際に書く必要はありません。**
- すでにプロジェクトには必要なコードが含まれています
- 設定が正しいかを確認したい場合のみ使用してください

### 動作確認の簡単な方法

**Google Sheets専用のテストスクリプトを用意しています！**

```bash
# プロジェクトフォルダで以下のコマンドを実行するだけ
python test_google_sheets.py
```

このテストスクリプトが自動的に：
- ✅ 認証ファイルの存在確認
- ✅ スプレッドシートへの接続テスト
- ✅ テストデータの書き込み
- ✅ 設定の問題があれば分かりやすくエラー表示

**参考：テストスクリプトの中身（見る必要はありません）**

```python
import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

# 認証情報を設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')
SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME')

try:
    # 認証
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く
    sheet = client.open(SHEET_NAME)
    worksheet = sheet.get_worksheet(0)
    
    # テストデータを書き込み
    worksheet.update('A1', 'テスト成功！')
    
    print(f"✅ Google Sheets接続成功: {SHEET_NAME}")
    print(f"✅ A1セルに「テスト成功！」を書き込みました")
    
except Exception as e:
    print(f"❌ エラー: {e}")
```

## 🚨 トラブルシューティング

### よくあるエラーと対処法

#### 1. 「SpreadsheetNotFound」エラー
**原因**：スプレッドシート名が間違っているか、共有されていない
**対処**：
- スプレッドシート名を確認
- サービスアカウントに共有されているか確認

#### 2. 「APIError: 403」エラー
**原因**：権限不足またはAPIが有効化されていない
**対処**：
- Google Sheets APIが有効化されているか確認
- サービスアカウントに「編集者」権限があるか確認

#### 3. 「FileNotFoundError: service_account.json」
**原因**：JSONファイルが見つからない
**対処**：
- ファイル名が正しいか確認
- ファイルパスが正しいか確認

#### 4. 「Invalid grant」エラー
**原因**：サービスアカウントキーが無効
**対処**：
- 新しいキーを作成してダウンロード
- 時刻設定が正しいか確認（時刻のずれがあるとエラーになる）

## 📊 スプレッドシート構成例

### 推奨シート構成

```
daily_presence シート:
| date_jst   | guild_id | user_id | user_name | present |
|------------|----------|---------|-----------|---------|
| 2024-01-01 | 123...   | 456...  | 田中太郎   | TRUE    |
| 2024-01-01 | 123...   | 789...  | 鈴木花子   | TRUE    |
```

## 💡 Tips

### 複数環境の管理

| 環境 | スプレッドシート名 | サービスアカウント |
|------|-------------------|-------------------|
| 本番 | VC_Tracker_Database | 本番専用アカウント |
| テスト | VC_Tracker_Test | テスト専用アカウント |
| 開発 | VC_Tracker_Dev | 開発専用アカウント |

### クォータとレート制限

Google Sheets APIには以下の制限があります：

- **読み取り**：100リクエスト/100秒/ユーザー
- **書き込み**：100リクエスト/100秒/ユーザー
- **セル数**：500万セル/スプレッドシート

### セキュリティのベストプラクティス

1. **最小権限の原則**
   - 必要なスプレッドシートのみ共有
   - 不要になったら共有を解除

2. **キーのローテーション**
   - 定期的に新しいキーを作成
   - 古いキーは削除

3. **アクセスログの確認**
   - Google Cloud Consoleで定期的に確認
   - 不審なアクセスをチェック

## ❓ よくある質問

### Q: 無料で使えますか？
A: はい、Google Sheets APIは無料枠で十分使用可能です。

### Q: 複数のスプレッドシートにアクセスできますか？
A: はい、それぞれにサービスアカウントを共有すればアクセス可能です。

### Q: スプレッドシートのオーナー権限は必要ですか？
A: いいえ、編集者権限があれば十分です。

### Q: サービスアカウントのメールアドレスを忘れました
A: Google Cloud Consoleの「認証情報」ページで確認できます。

### Q: JSONファイルを紛失しました
A: 新しいキーを作成してください。古いキーは削除することを推奨します。

## 📚 参考リンク

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [gspread Documentation](https://docs.gspread.org/)
- [Google Cloud Console](https://console.cloud.google.com)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-for-using-service-accounts)

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. エラーメッセージの全文
2. 実行したコード
3. Google Cloud Consoleの設定スクリーンショット
4. スプレッドシートの共有設定スクリーンショット
5. 試した対処法