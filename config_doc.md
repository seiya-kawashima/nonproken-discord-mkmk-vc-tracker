# config.py 仕様書

## 📌 このドキュメントについて
`config.py`は、Discord VCトラッカーの環境設定を管理するシンプルなモジュールです。本番・テスト・開発の3つの環境ごとに異なる設定値を切り替えて提供します。

## 🔧 主な機能
- 環境ごと（本番/テスト/開発）の設定値管理
- `.env`ファイルから環境変数を安全に読み込み
- 必要な設定値を辞書形式でまとめて返す

## 📥 Input（入力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| env | Environment | 環境の指定 | `Environment.PRD` (0), `Environment.TST` (1), `Environment.DEV` (2) |
| env_arg | int | コマンドライン引数からの環境指定 | 0=本番, 1=テスト, 2=開発 |

## 📤 Output（出力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| config | dict | すべての設定値を含む辞書 | 下記参照 |

### 設定値の内容
```python
{
    'discord_token': 'Bot のトークン',
    'channel_ids': ['123456', '789012'],  # 監視対象VCチャンネルID
    'sheet_name': 'もくもくトラッカー_0_PRD',
    'service_account_json': 'service_account.json',
    'service_account_json_base64': 'Base64エンコードされた認証情報',
    'folder_path': 'discord_mokumoku_tracker',
    'shared_drive_id': '0ANixFe4JBQskUk9PVA',
    'env_name': 'PRD',  # または TST, DEV
    'env_number': '0',   # または 1, 2
    'slack_token': 'Slack Botトークン',
    'slack_channel': 'Slackチャンネル ID'
}
```

## 🎯 使い方

### 基本的な使い方
```python
from config import get_config, get_environment_from_arg, Environment

# 方法1: 環境を直接指定
config = get_config(Environment.PRD)  # 本番環境の設定を取得
config = get_config(Environment.TST)  # テスト環境の設定を取得
config = get_config(Environment.DEV)  # 開発環境の設定を取得（デフォルト）

# 方法2: コマンドライン引数から環境を決定
import sys
env = get_environment_from_arg(int(sys.argv[1]) if len(sys.argv) > 1 else None)
config = get_config(env)

# 設定値の使用
discord_token = config['discord_token']
channel_ids = config['channel_ids']
sheet_name = config['sheet_name']
```

## 🔑 環境変数の命名規則

環境ごとに異なる値を設定するため、以下の命名規則を使用します：

| 環境 | サフィックス | 例 |
|------|------------|-----|
| 本番 (PRD) | `_0_PRD` | `DISCORD_BOT_TOKEN_0_PRD` |
| テスト (TST) | `_1_TST` | `DISCORD_BOT_TOKEN_1_TST` |
| 開発 (DEV) | `_2_DEV` | `DISCORD_BOT_TOKEN_2_DEV` |

## 📝 .env ファイルの設定項目

| 環境変数名 | 必須 | 説明 | 例 |
|-----------|------|------|-----|
| `DISCORD_BOT_TOKEN_{env}` | ✅ | Discord Botのトークン | `MTIzNDU2Nzg5...` |
| `ALLOWED_VOICE_CHANNEL_IDS_{env}` | ⚠️ | 監視対象のVCチャンネルID（カンマ区切り） | `123456789,987654321` |
| `GOOGLE_SHEET_NAME_{env}` | ❌ | スプレッドシート名（省略時はデフォルト） | `もくもくトラッカー_カスタム` |
| `GOOGLE_SERVICE_ACCOUNT_JSON_{env}` | ⚠️ | サービスアカウントのJSONファイルパス | `service_account.json` |
| `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64_{env}` | ⚠️ | Base64エンコードされた認証情報 | `eyJ0eXBlIjoi...` |
| `GOOGLE_SHARED_DRIVE_ID_{env}` | ❌ | 共有ドライブID | `0ANixFe4JBQskUk9PVA` |
| `SLACK_BOT_TOKEN_{env}` | ❌ | Slack Botトークン | `xoxb-123456...` |
| `SLACK_CHANNEL_ID_{env}` | ❌ | Slackチャンネル ID | `C1234567890` |

- ✅ 必須: 必ず設定が必要
- ⚠️ 条件付き必須: 状況により必要（認証情報はBase64かファイルパスのどちらか一方が必須）
- ❌ 任意: 設定しなくても動作する

## 🏗️ コード構造

### Environment列挙型
```python
class Environment(IntEnum):
    PRD = 0  # 本番環境
    TST = 1  # テスト環境
    DEV = 2  # 開発環境
```

### 主要な関数

#### `get_config(env: Environment) -> dict`
指定された環境のすべての設定値を取得します。

#### `get_environment_from_arg(env_arg: int) -> Environment`
コマンドライン引数から環境を決定します。
- `None` または無効な値の場合は `Environment.DEV` を返す
- 0, 1, 2 の値を対応する環境に変換

## ⚠️ エラーハンドリング

### ValueError が発生するケース
1. `get_environment_from_arg()` に無効な値が渡された場合
   - 例: `get_environment_from_arg(5)` → "無効な環境指定: 5"

2. 必須の環境変数が設定されていない場合
   - Discord トークンが未設定時にエラー

## 💡 使用例

### 例1: メインスクリプトでの使用
```python
import argparse
from config import get_config, get_environment_from_arg

# コマンドライン引数をパース
parser = argparse.ArgumentParser()
parser.add_argument('--env', type=int, choices=[0, 1, 2], default=2)
args = parser.parse_args()

# 環境を決定して設定を取得
env = get_environment_from_arg(args.env)
config = get_config(env)

# Discord Botを起動
bot_token = config['discord_token']
channel_ids = config['channel_ids']
```

### 例2: Google Sheets連携
```python
config = get_config(Environment.PRD)

# 認証情報の処理
if config['service_account_json_base64']:
    # Base64デコードして使用
    import base64
    credentials = base64.b64decode(config['service_account_json_base64'])
else:
    # ファイルパスから読み込み
    with open(config['service_account_json'], 'r') as f:
        credentials = f.read()
```

## 🔄 環境の切り替え方法

1. **コマンドライン引数で指定**
   ```bash
   python script.py --env 0  # 本番環境
   python script.py --env 1  # テスト環境
   python script.py --env 2  # 開発環境（デフォルト）
   ```

2. **コード内で直接指定**
   ```python
   config = get_config(Environment.PRD)  # 本番環境を明示的に指定
   ```

## 📁 フォルダ構造
Google Drive上では以下の構造でファイルが管理されます：
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

## ❓ FAQ

**Q: 環境変数が設定されているか確認したい**
A: `.env`ファイルの内容を確認するか、以下のコードで確認できます：
```python
import os
print(os.getenv('DISCORD_BOT_TOKEN_0_PRD'))  # None なら未設定
```

**Q: デフォルトはどの環境？**
A: 引数を指定しない場合は開発環境（DEV）がデフォルトです。

**Q: 新しい設定項目を追加したい**
A: `get_config()`関数の戻り値辞書に新しいキーを追加し、対応する環境変数を`.env`に設定してください。

## 🚀 シンプルさの理由
このモジュールは以前のバージョンから大幅に簡略化されました：
- クラスメソッドを廃止し、単純な関数に
- 350行以上のコードを48行に削減
- 複雑な継承やデコレーターを排除
- 必要最小限の機能のみを提供

これにより、理解しやすく、保守しやすいコードになっています。