# config.py 仕様書

## 📌 このドキュメントについて
config.pyは、Discord VCトラッカーシステムの環境設定を一元管理するモジュールです。本番環境、テスト環境、開発環境それぞれに異なる設定を簡単に切り替えられるように設計されています。環境変数や認証情報を安全に管理し、システム全体で一貫した設定を提供します。

## 🎯 主な機能
1. **環境の切り替え** - 本番（PRD）、テスト（TST）、開発（DEV）の3つの環境を番号で管理
2. **環境変数の管理** - .envファイルから環境変数を読み込み、環境ごとに異なる変数名に対応
3. **認証情報の管理** - Discord、Google、Slackの認証情報を安全に管理
4. **フォルダ構造の定義** - Google Drive上のフォルダ階層を統一的に管理

## 📥 Input（入力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| 環境番号 | int | 実行環境の指定（0/1/2） | `2`（開発環境） |
| .envファイル | file | 環境変数を定義したファイル | `.env` |
| 環境変数 | string | OS環境変数またはBase64エンコード認証情報 | `DISCORD_BOT_TOKEN` |

## 📤 Output（出力）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| Discord設定 | dict | Botトークンとチャンネル情報 | `{'token': 'xxx', 'channel_ids': ['762140202625925151']}` |
| Google Sheets設定 | dict | スプレッドシート名と認証情報 | `{'sheet_name': 'もくもくトラッカー_2_DEV', ...}` |
| Google Drive設定 | dict | フォルダパスと環境情報 | `{'folder_path': 'discord_mokumoku_tracker', ...}` |
| Slack設定 | dict | 通知用トークンとチャンネル | `{'token': 'xoxb-xxx', 'channel_id': 'C123'}` |

## 🔧 処理の流れ

### 1. 環境の判定
```python
# コマンドライン引数から環境を判定
env = EnvConfig.get_environment_from_arg(2)  # 2 = 開発環境
# 結果: Environment.DEV
```

### 2. 環境変数名の生成
```python
# 環境に応じた変数名を生成
token_key = EnvConfig.get_env_var_name('DISCORD_BOT_TOKEN', Environment.DEV)
# 結果: 'DEV_DISCORD_BOT_TOKEN'
```

### 3. 設定の取得
```python
# Discord設定を取得
discord_config = EnvConfig.get_discord_config(Environment.DEV)
# Google Sheets設定を取得
sheets_config = EnvConfig.get_google_sheets_config(Environment.DEV)
```

## 📁 フォルダ構造
config.pyで定義されているGoogle Drive上のフォルダ構造：

```
discord_mokumoku_tracker/           # ベースフォルダ（固定）
└── [VCチャンネル名]/               # 各VCチャンネルごとのフォルダ
    ├── もくもくトラッカー_0_PRD   # 本番環境のスプレッドシート
    ├── もくもくトラッカー_1_TST   # テスト環境のスプレッドシート
    ├── もくもくトラッカー_2_DEV   # 開発環境のスプレッドシート
    └── csv/                        # CSVファイル格納フォルダ
        ├── 0_PRD.csv               # 本番環境のデータ
        ├── 1_TST.csv               # テスト環境のデータ
        └── 2_DEV.csv               # 開発環境のデータ
```

## 🔢 環境番号マッピング
| 環境 | 番号 | 環境名 | ファイル接頭辞 | 環境変数接頭辞 |
|------|------|--------|----------------|----------------|
| 本番 | 0 | PRD | `0_PRD` | なし |
| テスト | 1 | TST | `1_TST` | `TST_` |
| 開発 | 2 | DEV | `2_DEV` | `DEV_` |

## 💡 使用例

### 環境ごとの設定取得
```python
from config import EnvConfig, Environment

# 開発環境の設定を取得
env = Environment.DEV
config = EnvConfig.get_discord_config(env)
print(f"Botトークン: {config['token']}")
print(f"監視対象VCチャンネル: {config['channel_ids']}")
```

### 必須環境変数の取得
```python
# 必須の環境変数を取得（なければエラー）
token = EnvConfig.get_required('DEV_DISCORD_BOT_TOKEN', '開発環境')
```

### 全環境の設定確認
```python
# デバッグ用：全環境の設定を一括取得
all_configs = EnvConfig.get_all_configs()
for env_name, config in all_configs.items():
    print(f"{env_name}: {config}")
```

## ⚠️ 注意事項

### 環境変数の優先順位
1. 環境変数で指定された値
2. .envファイルで定義された値
3. デフォルト値（定義されている場合）

### 認証情報の取り扱い
- **JSONファイル形式**: ローカルファイルシステム上のJSONファイル
- **Base64形式**: 環境変数に直接埋め込まれたBase64エンコード文字列
- どちらか一方が必須（両方ある場合はBase64が優先）

### フォルダパスの固定化
- `discord_mokumoku_tracker`はハードコーディングされており、環境変数での上書き不可
- これにより全環境で一貫したフォルダ構造を保証

### テスト環境の特殊処理
- テスト環境では`ALLOWED_VOICE_CHANNEL_IDS`が必須
- チャンネルIDが空の場合はエラーを発生

## ❓ FAQ

**Q: 新しい環境を追加したい場合は？**
A: `Environment`クラスに新しい環境番号を追加し、`ENV_NUMBER_MAP`にマッピングを追加してください。

**Q: 環境変数が見つからないエラーが出る**
A: `.env`ファイルが存在し、正しい環境変数名で定義されているか確認してください。開発環境なら`DEV_`接頭辞が必要です。

**Q: 共有ドライブIDはどこで確認できる？**
A: Google DriveのURLから確認できます。`https://drive.google.com/drive/folders/XXX`のXXX部分がIDです。

**Q: CSVファイル名の番号は何を意味する？**
A: 環境番号です。`0_PRD.csv`は本番環境、`1_TST.csv`はテスト環境、`2_DEV.csv`は開発環境のデータです。

## 🔄 環境変数の命名規則
| 基本名 | 本番環境 | テスト環境 | 開発環境 |
|--------|----------|------------|----------|
| DISCORD_BOT_TOKEN | DISCORD_BOT_TOKEN | TST_DISCORD_BOT_TOKEN | DEV_DISCORD_BOT_TOKEN |
| GOOGLE_SHEET_NAME | GOOGLE_SHEET_NAME | TST_GOOGLE_SHEET_NAME | DEV_GOOGLE_SHEET_NAME |
| SLACK_BOT_TOKEN | SLACK_BOT_TOKEN | TST_SLACK_BOT_TOKEN | DEV_SLACK_BOT_TOKEN |

## 📝 設定項目一覧

### Discord設定
- `token`: Discord Botのアクセストークン（必須）
- `channel_ids`: 監視対象のVCチャンネルIDリスト（テスト環境では必須）

### Google Sheets設定
- `sheet_name`: スプレッドシート名（環境ごとに異なる）
- `service_account_json`: サービスアカウントJSONファイルパス
- `service_account_json_base64`: Base64エンコードされた認証情報

### Google Drive設定
- `folder_path`: ベースフォルダパス（固定値: discord_mokumoku_tracker）
- `folder_id`: 既存フォルダのID（オプション）
- `shared_drive_id`: 共有ドライブID（デフォルト: 0ANixFe4JBQskUk9PVA）
- `env_name`: 環境名（PRD/TST/DEV）
- `env_number`: 環境番号（0/1/2）

### Slack設定（オプション）
- `token`: Slack Botトークン
- `channel_id`: 通知先チャンネルID