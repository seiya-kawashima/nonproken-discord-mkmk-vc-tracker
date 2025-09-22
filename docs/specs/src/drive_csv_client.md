# Google Drive CSV Client 仕様書

## 📌 このドキュメントについて
このドキュメントは、Google Drive上のCSVファイルを管理するクライアントモジュールの仕様書です。
Discord VCの出席情報をCSVファイルとして保存・管理する機能を提供します。

## 🎯 身近な例え
このモジュールは「クラウド上の出席簿管理システム」のようなものです。
学校の各クラス（VCチャンネル）ごとに出席簿（CSVファイル）を作成し、
生徒（ユーザー）の出席状況を毎日記録していきます。

## 📥 Input（入力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| service_account_json | string | Google サービスアカウントのJSONファイルパス | `service_account.json` |
| folder_name | string | Google Drive上のフォルダ名 | `VC_Tracker_Data` |
| members | List[Dict] | VCメンバー情報のリスト | 下記参照 |

### membersの構造
```python
{
    'vc_name': 'general-voice',       # VCチャンネル名
    'user_id': '111111111111111111',  # DiscordユーザーID
    'user_name': 'kawashima#1234'     # ユーザー名
}
```

## 📤 Output（出力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| 処理結果 | Dict | 新規追加数と更新数 | `{"new": 5, "updated": 2}` |
| CSVファイル | file | Google Drive上に作成されるCSVファイル | `general-voice.csv` |

### CSVファイルの形式
| カラム | 説明 | 例 |
|--------|------|-----|
| date_jst | 日本時間の日付 | 2025/9/11 |
| user_id | DiscordユーザーID | 111111111111111111 |
| user_name | ユーザー名 | kawashima#1234 |
| present | 出席フラグ | TRUE |

## 🔧 処理の流れ

### 1. 初期化と接続
```
1. サービスアカウントJSONファイルを読み込み
2. Google Drive APIに接続
3. 指定フォルダが存在しない場合は自動作成
```

### 2. 出席情報の記録（upsert_presence）
```
1. 現在のJST日時を取得
2. メンバーをVCチャンネルごとにグループ化
3. 各VCチャンネルについて：
   a. 対応するCSVファイルを検索（なければ新規作成）
   b. 既存データをダウンロード
   c. 今日の日付のデータを確認
   d. 新規ユーザーは追加、既存ユーザーはスキップ
   e. 更新したCSVをアップロード
4. 処理結果を返す
```

## 💡 使用例

### 基本的な使い方
```python
# クライアントを初期化
client = DriveCSVClient(
    service_account_json='service_account.json',
    folder_name='VC_Tracker_Data'
)

# Google Driveに接続
client.connect()

# VCメンバー情報
members = [
    {
        'vc_name': 'general-voice',
        'user_id': '111111111111111111',
        'user_name': 'kawashima#1234'
    },
    {
        'vc_name': 'study-room',
        'user_id': '222222222222222222',
        'user_name': 'tanaka#5678'
    }
]

# 出席情報を記録
result = client.upsert_presence(members)
print(f"新規: {result['new']}名, 更新: {result['updated']}名")
```

### 出力されるCSVファイル例（general-voice.csv）
```csv
date_jst,user_id,user_name,present
2025/9/10,111111111111111111,kawashima#1234,TRUE
2025/9/10,333333333333333333,sato#9012,TRUE
2025/9/11,111111111111111111,kawashima#1234,TRUE
```

## ⚠️ 注意事項

### セキュリティ
- サービスアカウントのJSONファイルは絶対にGitにコミットしない
- 環境変数またはGitHub Secretsで管理する

### ファイル管理
- VCチャンネル名に`/`や`\`が含まれる場合は`_`に置換される
- CSVファイルはUTF-8 BOM付きで保存される（Excelで開く際の文字化け防止）

### エラー処理
- Google Drive APIの接続エラー時は例外を発生
- ファイルアップロード失敗時はログに記録

### パフォーマンス
- 大量のデータを扱う場合、CSVファイルのダウンロード/アップロードに時間がかかる可能性あり
- 1日あたり数百ユーザー程度であれば問題なし

## ❓ FAQ

### Q: Google Driveの容量制限は？
A: Google Driveの無料枠は15GBです。CSVファイルは非常に小さいため、数年分のデータでも問題ありません。

### Q: 複数のVCチャンネルに同じユーザーがいる場合は？
A: 各VCチャンネルごとに別々のCSVファイルで管理されるため、問題ありません。

### Q: CSVファイルを直接編集しても大丈夫？
A: 可能ですが、フォーマットを崩さないよう注意してください。特に日付形式（YYYY/M/D）は厳守してください。

### Q: Google Sheetsではなく、なぜCSVファイル？
A: CSVファイルの方がシンプルで、Sheets APIの制限を受けず、手動共有も不要なためです。

### Q: フォルダが見つからない場合は？
A: 自動的に`VC_Tracker_Data`フォルダが作成されるので、手動での作成は不要です。

## 🔄 データフロー図

```
Discord Bot
    ↓ (VCメンバー情報)
DriveCSVClient
    ↓ (認証)
Google Drive API
    ↓ (フォルダ確認/作成)
VC_Tracker_Data フォルダ
    ├── general-voice.csv
    ├── study-room.csv
    └── gaming-room.csv
```

## 📊 メトリクス

### 処理時間の目安
- 接続: 1-2秒
- CSVダウンロード: 0.5秒/ファイル
- データ処理: 0.1秒/100レコード
- CSVアップロード: 1秒/ファイル

### 容量の目安
- 1レコード: 約50バイト
- 1日100ユーザー: 約5KB
- 1年分: 約1.8MB