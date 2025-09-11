# Google Sheetsクライアント仕様書

## 1. 概要

Google Sheetsクライアントは、Discord VCの出席データをGoogleスプレッドシートに記録・管理するためのモジュールです。

### 1.1 目的
- VCログイン情報の永続化
- 日次出席データの管理
- 通算ログイン日数の集計
- データのUpsert（挿入・更新）処理

### 1.2 ファイル構成
```
src/
└── sheets_client.py  # Google Sheetsクライアント実装
```

## 2. クラス設計

### 2.1 SheetsClient クラス

#### 2.1.1 責務
- Google Sheets APIへの接続管理
- 出席データの記録（Upsert）
- 通算ログイン日数の集計
- ワークシートの自動作成

#### 2.1.2 定数
```python
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
```

#### 2.1.3 コンストラクタ
```python
def __init__(self, service_account_json: str, sheet_name: str)
```

**パラメータ:**
- `service_account_json`: サービスアカウントJSONファイルパス（必須）
- `sheet_name`: スプレッドシート名（必須）

**初期化処理:**
1. 認証情報ファイルパスの保存
2. スプレッドシート名の保存
3. クライアント、シート、ワークシートの初期化（None）

#### 2.1.4 主要メソッド

##### connect()
```python
def connect()
```

**機能:**
- Google Sheetsへの接続確立
- ワークシートの取得または作成

**処理フロー:**
1. サービスアカウント認証情報の読み込み
2. gspreadクライアントの作成
3. スプレッドシートを開く
4. `daily_presence`ワークシートの取得
5. ワークシートが存在しない場合は新規作成
6. ヘッダー行の設定

**ワークシート構造:**
| 列 | カラム名 | 説明 |
|---|---|---|
| A | date_jst | 日付（YYYY-MM-DD形式） |
| B | guild_id | DiscordサーバーID |
| C | user_id | ユーザーID |
| D | user_name | ユーザー名#識別子 |
| E | present | 出席フラグ（TRUE/FALSE） |

**エラーハンドリング:**
- 認証エラー
- スプレッドシートが見つからない
- 権限不足

##### upsert_presence()
```python
def upsert_presence(members: List[Dict[str, Any]]) -> Dict[str, int]
```

**機能:**
- メンバーの出席情報をUpsert（存在しない場合は挿入、存在する場合は更新）

**パラメータ:**
```python
members = [
    {
        "guild_id": "123456789",
        "user_id": "111111111",
        "user_name": "user#1234"
    },
    ...
]
```

**処理フロー:**
1. JSTの今日の日付を取得
2. 既存データを全取得
3. 今日のデータを抽出
4. 各メンバーについて:
   - 新規の場合: 行を追加
   - 既存でFALSEの場合: TRUEに更新
   - 既存でTRUEの場合: スキップ
5. 新規データを一括追加

**戻り値:**
```python
{
    "new": 5,      # 新規追加数
    "updated": 2   # 更新数
}
```

##### get_total_days()
```python
def get_total_days(user_id: str) -> int
```

**機能:**
- 特定ユーザーの通算ログイン日数を取得

**パラメータ:**
- `user_id`: 対象ユーザーのID

**処理フロー:**
1. 全データを取得
2. 指定ユーザーIDでフィルタリング
3. `present = TRUE`のレコード数をカウント

**戻り値:**
- 通算ログイン日数（整数）

##### get_today_members()
```python
def get_today_members() -> List[Dict[str, Any]]
```

**機能:**
- 今日ログインしたメンバーのリストを取得

**処理フロー:**
1. JSTの今日の日付を取得
2. 全データを取得
3. 今日かつ`present = TRUE`のレコードを抽出

**戻り値:**
```python
[
    {
        "date_jst": "2025-09-11",
        "guild_id": "123456789",
        "user_id": "111111111",
        "user_name": "user#1234",
        "present": "TRUE"
    },
    ...
]
```

## 3. データ構造

### 3.1 出席レコード
```python
{
    "date_jst": str,    # 日付（YYYY-MM-DD）
    "guild_id": str,    # サーバーID
    "user_id": str,     # ユーザーID
    "user_name": str,   # ユーザー名
    "present": str      # "TRUE" or "FALSE"
}
```

### 3.2 内部状態
- `self.client`: gspreadクライアント
- `self.sheet`: スプレッドシートオブジェクト
- `self.worksheet`: ワークシートオブジェクト

## 4. 依存関係

### 4.1 外部ライブラリ
- `gspread`: Google Sheets API ラッパー
- `google-auth`: Google認証
- `google-auth-oauthlib`: OAuth2認証

### 4.2 標準ライブラリ
- `os`: ファイルパス操作
- `json`: JSON処理
- `logging`: ログ出力
- `datetime`: 日時処理
- `typing`: 型ヒント

## 5. 設定要件

### 5.1 Google Cloud設定
- **サービスアカウント:**
  - Google Cloud Consoleで作成
  - JSONキーファイルをダウンロード
  - スプレッドシートへの編集権限付与

### 5.2 環境変数
- `GOOGLE_SERVICE_ACCOUNT_JSON`: JSONファイルパス
- `GOOGLE_SHEET_NAME`: スプレッドシート名

### 5.3 権限設定
- スプレッドシートをサービスアカウントのメールアドレスに共有
- 編集者権限を付与

## 6. エラー処理

### 6.1 接続エラー
- 認証失敗: 詳細なエラーメッセージをログ出力
- スプレッドシート未検出: 名前を確認するよう促す
- 権限不足: 共有設定の確認を促す

### 6.2 データ操作エラー
- 書き込み失敗: リトライ処理
- 読み込み失敗: キャッシュから返却

### 6.3 RuntimeError
- 未接続状態でのメソッド呼び出し時に発生

## 7. ログ出力

### 7.1 ログレベル
- `INFO`: 正常処理
  - 接続成功
  - ワークシート作成
  - データ追加/更新
- `ERROR`: エラー発生
  - 接続失敗
  - API エラー

### 7.2 ログメッセージ例
```
INFO: Connected to Google Sheets: MySheet
INFO: Created daily_presence worksheet with headers
INFO: New presence: user#1234 on 2025-09-11
INFO: Added 5 new presence records
ERROR: Failed to connect to Google Sheets: [詳細]
```

## 8. パフォーマンス考慮事項

### 8.1 バッチ処理
- 複数行の追加は`append_rows()`で一括処理
- 個別更新は最小限に抑える

### 8.2 データ取得
- `get_all_records()`で全データを一度に取得
- メモリ効率を考慮（大規模データ時は分割取得）

### 8.3 API制限
- Google Sheets API: 100リクエスト/100秒
- 書き込み: 100リクエスト/100秒

## 9. セキュリティ考慮事項

### 9.1 認証情報管理
- サービスアカウントJSONは環境変数で管理
- GitHubにはBase64エンコードして保存
- ローカルではファイルとして保存

### 9.2 データアクセス制御
- 最小権限の原則
- 必要なスコープのみ要求
- 個人情報の最小化

## 10. タイムゾーン処理

### 10.1 JST対応
```python
jst = timezone(timedelta(hours=9))
today_jst = datetime.now(jst).strftime('%Y-%m-%d')
```

### 10.2 日付形式
- 統一フォーマット: `YYYY-MM-DD`
- 時刻は記録しない（日次集計のため）

## 11. 制限事項

### 11.1 スケーラビリティ
- 1シートあたり最大1000万セル
- 1シートあたり最大18,278列
- 処理速度は行数に比例して低下

### 11.2 同時アクセス
- 複数プロセスからの同時書き込みは非推奨
- ロック機構なし

## 12. 今後の拡張可能性

### 12.1 機能拡張
- 月次・年次集計機能
- データのアーカイブ機能
- 複数シートへの分散記録
- グラフ自動生成

### 12.2 性能改善
- キャッシュレイヤーの実装
- 差分更新の最適化
- バルクインサートの改善
- 非同期処理の導入