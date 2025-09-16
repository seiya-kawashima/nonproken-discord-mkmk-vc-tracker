# config.py 仕様書

## 目的と概要
- Discord もくもく会関連ツール群で共通利用する設定値を一元管理する。
- `.env` に格納した認証情報や環境別の設定値を読み込み、コードから安全かつ一貫した方法で参照できるようにする。
- 本番(PRD) / テスト(TST) / 開発(DEV)の 3 環境をサポートし、環境固有の値を自動で切り替える。

## 読み込みと依存関係
- 起動時に `dotenv.load_dotenv()` を実行し、プロジェクトルートの `.env` を環境変数へロードする。
- 外部依存: `os`, `enum.IntEnum`, `dotenv`。

## 環境定義と命名規則
### Environment 列挙体
- PRD=0, TST=1, DEV=2。
- `Environment.from_value(value)` は `None` → PRD、それ以外は `Environment(value)` を返す。

### 環境名と番号の対応
- `EnvConfig.ENV_NUMBER_MAP` で `{'PRD': '0', 'TST': '1', 'DEV': '2'}` を定義。
- `EnvConfig.get_env_number(env_name)` は一致しない場合 `'9'` を返す（CSV 等のフォールバック）。

### 環境変数プレフィックス
- `EnvConfig.get_env_var_name(base_name, env)` で環境に応じて接頭辞を付与。
  - PRD: 変換なし。
  - TST: `TST_{base_name}`。
  - DEV: `DEV_{base_name}`。

## 共通ユーティリティ
- `EnvConfig.get(key, default=None)`: `os.getenv` ラッパー。
- `EnvConfig.get_required(key, env_name="")`: 未設定時に `ValueError` を発生。`env_name` が指定されている場合はメッセージに「◯◯環境用」を付与。
- `EnvConfig.is_github_actions()`: 環境変数 `GITHUB_ACTIONS` が `'true'` の場合のみ `True`。
- `EnvConfig.get_environment_from_arg(env_arg)`: 引数が `None` のとき PRD。`0/1/2` の文字列または数値を `Environment` に変換し、不正値は `ValueError`。
- `EnvConfig.get_environment_name(env)`: PRD →「本番環境」、TST →「テスト環境」、DEV →「開発環境」。

## 設定別仕様
### Discord 設定 (`get_discord_config`)
- 返却値: `{'token': str, 'channel_ids': list[str]}`。
- 必須環境変数:
  - 全環境: `<envPrefix>DISCORD_BOT_TOKEN`。
  - TST のみ: `<envPrefix>ALLOWED_VOICE_CHANNEL_IDS`（カンマ区切り）。
- `channel_ids` はカンマ区切り文字列を分割し、空要素を除去してトリムした文字列リスト。
- TST で空リストになった場合は `ValueError`。
- PRD/DEV ではチャンネル ID が未設定でも空リストを許容。

### Google Sheets 設定 (`get_google_sheets_config`)
- 返却値: `{'sheet_name': str, 'service_account_json': str, 'service_account_json_base64': Optional[str]}`。
- デフォルトシート名:
  - PRD: `もくもくトラッカー_0_PRD`
  - TST: `もくもくトラッカー_1_TST`
  - DEV: `もくもくトラッカー_2_DEV`
- `<envPrefix>GOOGLE_SHEET_NAME` が設定されていればデフォルトを上書き。
- サービスアカウント情報は以下いずれかを必須とする。
  - `<envPrefix>GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`（優先して使用）。
  - `<envPrefix>GOOGLE_SERVICE_ACCOUNT_JSON`（ファイルパス。既定値 `service_account.json`）。
- Base64 が未設定かつファイルが存在しない場合は `ValueError` を送出。

### Google Drive 設定 (`get_google_drive_config`)
- 返却値: `{
    'folder_path': str,
    'folder_id': Optional[str],
    'shared_drive_id': Optional[str],
    'env_name': str,
    'env_number': str,
    'service_account_json': str,
    'service_account_json_base64': Optional[str]
  }`。
- フォルダ構成の基準パスは固定で `discord_mokumoku_tracker`。環境変数による上書きは不可。
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
- オプション環境変数:
  - `<envPrefix>GOOGLE_DRIVE_FOLDER_ID`: 既存フォルダの ID。
  - `<envPrefix>GOOGLE_SHARED_DRIVE_ID`: 共有ドライブ ID。未設定時は `0ANixFe4JBQskUk9PVA`。空文字の場合は `None` とみなしマイドライブ使用。
- サービスアカウント情報は Google Sheets と同じキーを利用し、優先順位も同様。
- `env_name` は `Environment` の列挙名（PRD/TST/DEV）、`env_number` は `ENV_NUMBER_MAP` から取得。

### Slack 設定 (`get_slack_config`)
- 返却値: `{'token': Optional[str], 'channel_id': Optional[str]}`。
- `<envPrefix>SLACK_BOT_TOKEN` と `<envPrefix>SLACK_CHANNEL_ID` を参照。設定がなければ `None`。
- Slack 連携はオプションであり、いずれの値も必須ではない。

### 全設定の収集 (`get_all_configs`)
- 各 `Environment` について Discord / Google Sheets / Slack 設定をまとめた辞書を返す。
- 個別取得で `ValueError` が発生した場合は `{'error': エラーメッセージ}` を格納。

## 公開インターフェース
- モジュールレベルで `config = EnvConfig()` を生成。利用側は `from config import config` としてクラスメソッドを呼び出せる。

## 必須・主要環境変数一覧
| 用途 | PRD | TST | DEV | 備考 |
| --- | --- | --- | --- | --- |
| Discord Bot トークン | `DISCORD_BOT_TOKEN` | `TST_DISCORD_BOT_TOKEN` | `DEV_DISCORD_BOT_TOKEN` | 全環境必須 |
| 監視対象 VC ID | 任意 (`ALLOWED_VOICE_CHANNEL_IDS`) | 必須 (`TST_ALLOWED_VOICE_CHANNEL_IDS`) | 任意 (`DEV_ALLOWED_VOICE_CHANNEL_IDS`) | カンマ区切り |
| Google シート名 | 任意 (`GOOGLE_SHEET_NAME`) | 任意 (`TST_GOOGLE_SHEET_NAME`) | 任意 (`DEV_GOOGLE_SHEET_NAME`) | 未設定時はデフォルト名 |
| サービスアカウント JSON | `GOOGLE_SERVICE_ACCOUNT_JSON` | `TST_GOOGLE_SERVICE_ACCOUNT_JSON` | `DEV_GOOGLE_SERVICE_ACCOUNT_JSON` | Base64 未設定時に参照（既定 `service_account.json`） |
| サービスアカウント Base64 | `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | `TST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | `DEV_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64` | JSON ファイルより優先 |
| Drive フォルダ ID | 任意 (`GOOGLE_DRIVE_FOLDER_ID`) | 任意 (`TST_GOOGLE_DRIVE_FOLDER_ID`) | 任意 (`DEV_GOOGLE_DRIVE_FOLDER_ID`) | 既存フォルダ利用時のみ |
| Drive 共有ドライブ ID | 任意 (`GOOGLE_SHARED_DRIVE_ID`) | 任意 (`TST_GOOGLE_SHARED_DRIVE_ID`) | 任意 (`DEV_GOOGLE_SHARED_DRIVE_ID`) | 既定 `0ANixFe4JBQskUk9PVA`、空文字でマイドライブ |
| Slack Bot トークン | 任意 (`SLACK_BOT_TOKEN`) | 任意 (`TST_SLACK_BOT_TOKEN`) | 任意 (`DEV_SLACK_BOT_TOKEN`) | Slack 連携が必要な場合のみ |
| Slack チャンネル ID | 任意 (`SLACK_CHANNEL_ID`) | 任意 (`TST_SLACK_CHANNEL_ID`) | 任意 (`DEV_SLACK_CHANNEL_ID`) | Slack 連携が必要な場合のみ |

## エラーハンドリング方針
- 必須値の欠落時は `ValueError` を発生させ、利用側が適切に対処できるようにする。
- `get_all_configs` は個別エラーを握りつぶさず、各環境ごとに `error` フィールドとして露出する。

## 利用例
```python
from config import config, Environment

env = config.get_environment_from_arg(os.getenv('APP_ENV'))
discord_conf = config.get_discord_config(env)
sheets_conf = config.get_google_sheets_config(env)
if config.is_github_actions():
    # CI 用の追加処理
    pass
```
