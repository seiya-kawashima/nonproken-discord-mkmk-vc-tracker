# config.py 仕様書（やさしい解説つき）

## 1. config.py とは？
`config.py` は、Discord もくもく会関連ツールで使う「設定値」をまとめて管理するためのファイルです。トークンやパスワードのような秘密情報を直接コードに書かず、`.env` ファイルに保存したものを安全に読み込む役割を持っています。さらに、本番 (PRD)・テスト (TST)・開発 (DEV) の 3 つの環境ごとに適切な設定を自動で切り替えてくれます。

> **ポイント**: 環境ごとの設定を 1 箇所にまとめることで、「本番では本番用のトークン」「テストではテスト用のトークン」を取り違えずに使えるようになります。

## 2. どうやって動いているの？
1. `dotenv.load_dotenv()` が呼ばれ、プロジェクトルートにある `.env` ファイルが読み込まれます。
2. 必要な値は環境変数として取得できるようになります。
3. `EnvConfig` クラスのメソッドを呼び出すと、環境に応じた設定値が辞書形式で返ってきます。

このように、「.env に書いてある → config.py が読み込む → コードから使える」という流れです。

### 依存ライブラリ
- `os`: 環境変数を読むため。
- `enum.IntEnum`: 環境 (PRD/TST/DEV) を数字で扱いやすくするため。
- `dotenv`: `.env` の内容を読み込むため。

## 3. 環境を表す `Environment` 列挙体
```python
class Environment(IntEnum):
    PRD = 0
    TST = 1
    DEV = 2
```
- `Environment.PRD` など定数として扱えるので、コードの可読性が上がります。
- `Environment.from_value(value)` で数値や `None` から安全に変換できます。`None` のときは本番(PRD)を選ぶようになっています。

## 4. 環境ごとの名前と番号
- `EnvConfig.ENV_NUMBER_MAP` では、環境名と番号をペアで持っています。
  - PRD → `0`
  - TST → `1`
  - DEV → `2`
- `EnvConfig.get_env_number('PRD')` のように呼ぶと該当する番号を返します。もし想定外の値が来た場合は `9` を返し、識別できない状態であることを示します。

## 5. 環境変数名の付け方
`.env` では、環境別の値を次のルールで分けています。
- 本番: そのまま (`DISCORD_BOT_TOKEN`)
- テスト: `TST_` を先頭に付ける (`TST_DISCORD_BOT_TOKEN`)
- 開発: `DEV_` を先頭に付ける (`DEV_DISCORD_BOT_TOKEN`)

`EnvConfig.get_env_var_name(base_name, env)` を使うことで、このルールに従った名前を自動で作れます。

## 6. よく使う共通メソッド
| メソッド | 何をする？ | どんなときに使う？ |
| --- | --- | --- |
| `get(key, default=None)` | `os.getenv` の薄いラッパー。値が無いときは `default` を返す。 | 必須でない値を取りたいとき。|
| `get_required(key, env_name="")` | 値が無いと `ValueError` を投げる。 | 必須のトークンなどを取得するとき。|
| `is_github_actions()` | `GITHUB_ACTIONS` が `'true'` か確認。 | CI/CD 上でだけ動作を変えたいとき。|
| `get_environment_from_arg(env_arg)` | コマンドライン引数から `Environment` を決定。 | CLI で `--env 1` のように指定したいとき。|
| `get_environment_name(env)` | 「本番環境／テスト環境／開発環境」という日本語を返す。 | ログやエラーに分かりやすく表示したいとき。|

> **初心者向けヒント**: 必須値を扱うときは必ず `get_required` を使いましょう。値が設定されていないことにすぐ気づけて、原因調査が楽になります。

## 7. 各種設定の取り方
ここからは、それぞれのサービス向け設定がどのように取得されるかを解説します。すべて辞書（`dict`）として返ってくるので、`config.get_discord_config()` のように呼び出してフィールドを参照します。

### 7.1 Discord 設定 (`get_discord_config`)
- **戻り値の例**: `{'token': 'xxxx', 'channel_ids': ['111', '222']}`
- **必須の環境変数**
  - `DISCORD_BOT_TOKEN`（テスト・開発の場合は接頭辞付き）
  - テスト環境のみ `ALLOWED_VOICE_CHANNEL_IDS` も必須（カンマ区切りで複数指定可）
- **処理の流れ**
  1. Bot トークンを必ず取得する。なければエラー。
  2. チャンネル ID はカンマで分割し、空白を除去してリスト化。
  3. テスト環境で ID が取得できなかったらエラーにする。
  4. 本番・開発ではチャンネル ID が空でも通過し、空リストが返る。

### 7.2 Google Sheets 設定 (`get_google_sheets_config`)
- **戻り値の例**: `{'sheet_name': 'もくもくトラッカー_0_PRD', 'service_account_json': 'service_account.json', 'service_account_json_base64': 'xxxx...'}`
- **シート名の決定**
  - 既定値は環境ごとに用意（PRD/TST/DEV）。
  - `.env` に `<envPrefix>GOOGLE_SHEET_NAME` があればそちらを優先。
- **認証情報の取得ルール**
  - Base64 形式 (`<envPrefix>GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`) が優先。
  - Base64 が無い場合は JSON ファイル (`<envPrefix>GOOGLE_SERVICE_ACCOUNT_JSON`) を探す。何も指定がなければ `service_account.json` というファイルを参照。
  - Base64 も JSON ファイルも見つからないと `ValueError`。

### 7.3 Google Drive 設定 (`get_google_drive_config`)
- **戻り値の例**:
  ```python
  {
      'folder_path': 'discord_mokumoku_tracker',
      'folder_id': '1abc...',
      'shared_drive_id': '0ANixFe4JBQskUk9PVA',
      'env_name': 'PRD',
      'env_number': '0',
      'service_account_json': 'service_account.json',
      'service_account_json_base64': None
  }
  ```
- **フォルダ構造について**
  - ベースフォルダは固定で `discord_mokumoku_tracker`。
  - フォルダ名を環境ごとに変えることはできません（運用ルールで統一）。
  - 参考構造:
    ```
    discord_mokumoku_tracker/
      └── [VCチャンネル名]/
          ├── もくもくトラッカー_0_PRD.spreadsheet
          ├── もくもくトラッカー_1_TST.spreadsheet
          ├── もくもくトラッカー_2_DEV.spreadsheet
          └── csv/
              ├── 0_PRD.csv
              ├── 1_TST.csv
              └── 2_DEV.csv
    ```
- **オプションで設定できるもの**
  - `<envPrefix>GOOGLE_DRIVE_FOLDER_ID`: 既存フォルダ ID（指定しない場合は新規作成を想定）。
  - `<envPrefix>GOOGLE_SHARED_DRIVE_ID`: 共有ドライブ ID。省略した場合は `0ANixFe4JBQskUk9PVA` が使われ、空文字を設定すると `None` (マイドライブ) として扱う。
- 認証情報に関するルールは Google Sheets と同じです。

### 7.4 Slack 設定 (`get_slack_config`)
- **戻り値の例**: `{'token': None, 'channel_id': None}`
- Slack 通知はオプション機能なので、値が無ければ `None` のままで問題ありません。
- `.env` で設定する場合は `<envPrefix>SLACK_BOT_TOKEN` と `<envPrefix>SLACK_CHANNEL_ID` を用意します。

### 7.5 まとめて取得 (`get_all_configs`)
- すべての環境について Discord / Google Sheets / Slack 設定をまとめた辞書を返します。
- どれかで `ValueError` が発生した場合は、該当環境に `{'error': 'メッセージ'}` を入れて返します。これで「どの環境の設定が欠けているか」を一覧で確認できます。

## 8. `.env` に書くべき項目一覧
| 用途 | PRD | TST | DEV | 必須か？ | 補足 |
| --- | --- | --- | --- | --- | --- |
| Discord Bot トークン | `DISCORD_BOT_TOKEN` | `TST_DISCORD_BOT_TOKEN` | `DEV_DISCORD_BOT_TOKEN` | ✔ | Bot を動かすのに必須 |
| 監視対象 VC ID | `ALLOWED_VOICE_CHANNEL_IDS` | `TST_ALLOWED_VOICE_CHANNEL_IDS` | `DEV_ALLOWED_VOICE_CHANNEL_IDS` | TST では ✔ | カンマ区切り。PRD/DEV は任意 |
| Google シート名 | `GOOGLE_SHEET_NAME` | `TST_GOOGLE_SHEET_NAME` | `DEV_GOOGLE_SHEET_NAME` | 任意 | 未設定ならデフォルト名 |
| サービスアカウント JSON | `GOOGLE_SERVICE_ACCOUNT_JSON` | `TST_GOOGLE_SERVICE_ACCOUNT_JSON` | `DEV_GOOGLE_SERVICE_ACCOUNT_JSON` | Base64 が無い場合のみ ✔ | ファイルパス。既定は `service_account.json` |
| サービスアカウント Base64 | `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | `DEV_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | ✔ (どちらか) | JSON を Base64 化した文字列 |
| Drive フォルダ ID | `GOOGLE_DRIVE_FOLDER_ID` | `TST_GOOGLE_DRIVE_FOLDER_ID` | `DEV_GOOGLE_DRIVE_FOLDER_ID` | 任意 | 既存フォルダを使いたいときだけ |
| Drive 共有ドライブ ID | `GOOGLE_SHARED_DRIVE_ID` | `TST_GOOGLE_SHARED_DRIVE_ID` | `DEV_GOOGLE_SHARED_DRIVE_ID` | 任意 | 既定は共有ドライブ ID。空文字でマイドライブ |
| Slack Bot トークン | `SLACK_BOT_TOKEN` | `TST_SLACK_BOT_TOKEN` | `DEV_SLACK_BOT_TOKEN` | 任意 | Slack 連携が必要なとき |
| Slack チャンネル ID | `SLACK_CHANNEL_ID` | `TST_SLACK_CHANNEL_ID` | `DEV_SLACK_CHANNEL_ID` | 任意 | Slack 連携が必要なとき |

> **コツ**: まずは PRD の列に必要な値をすべて入れ、テスト・開発用が必要になったらそのときに TST/DEV 用の項目を追加すると迷いにくいです。

## 9. エラーが出たときの考え方
- `get_required` や `get_google_sheets_config` などで `ValueError` が発生した場合は、メッセージをよく読むと「どの環境のどの変数が無いか」を教えてくれます。
- `get_all_configs` を使えば、全部の環境の設定を一気にチェックできます。開発初期に設定漏れを見つけるのに便利です。

## 10. 使い方の例
```python
from config import config, Environment
import os

# 例1: 実行時引数や環境変数から環境を決める
env = config.get_environment_from_arg(os.getenv('APP_ENV'))
print(config.get_environment_name(env))  # => "本番環境" など

# 例2: Discord Bot を動かすときに設定を読む
discord_conf = config.get_discord_config(env)
TOKEN = discord_conf['token']
CHANNEL_IDS = discord_conf['channel_ids']

# 例3: Google Sheets へ接続するための情報を取得
sheets_conf = config.get_google_sheets_config(env)
if sheets_conf['service_account_json_base64']:
    # Base64 データから認証情報を復元して使う
    pass
else:
    # ファイルパスを指定してライブラリに渡す
    pass

# 例4: CI/CD だけ特別な処理をしたいとき
if config.is_github_actions():
    print("GitHub Actions 上で実行されています")
```

## 11. これから拡張したいときは？
- 新しい設定値を追加したい場合は、まず `.env` と `.env.example` に項目を追加し、`EnvConfig` に取得用メソッドを書くと分かりやすく整理できます。
- 既存の命名規則（PRD は接頭辞なし、TST/DEV は接頭辞あり）を守ると、環境を切り替えてもミスが減ります。
- エラー処理は `ValueError` を投げる形に統一しているので、追加メソッドでも同じ方針にすると全体が揃います。

---
初心者の方は、まずは `.env` を整備し、`get_all_configs()` を呼び出して値が正しく取得できるかをチェックするところから始めるのがおすすめです。分からない値があれば、エラーメッセージとこの仕様書を照らし合わせて確認してみてください。
