# Discord Botクライアント仕様書

## 1. 概要

Discord Botクライアントは、指定されたボイスチャンネル（VC）に在室しているメンバー情報を取得するためのモジュールです。

### 1.1 目的
- Discord サーバーの特定VCに接続しているユーザーをリアルタイムで検出
- ユーザー情報（ギルドID、ユーザーID、ユーザー名）を収集
- 非同期処理による効率的なデータ取得

### 1.2 ファイル構成
```
src/
└── discord_client.py  # Discord Botクライアント実装
```

## 2. クラス設計

### 2.1 DiscordVCPoller クラス

#### 2.1.1 責務
- Discord Gatewayへの接続管理
- VCメンバー情報の取得
- 非同期処理の制御

#### 2.1.2 コンストラクタ
```python
def __init__(self, token: str, allowed_channel_ids: List[str])
```

**パラメータ:**
- `token`: Discord Botトークン（必須）
- `allowed_channel_ids`: 監視対象のVCチャンネルIDリスト（必須）

**初期化処理:**
1. BotトークンとチャンネルIDの保存
2. Discord Intentsの設定
   - `voice_states`: ボイスステート変更の監視
   - `guilds`: ギルド情報の取得
   - `members`: メンバー情報の取得
3. Discordクライアントインスタンスの作成
4. メンバーデータ格納用リストの初期化

#### 2.1.3 主要メソッド

##### get_vc_members()
```python
async def get_vc_members() -> List[Dict[str, Any]]
```

**機能:**
- VCに在室しているメンバー情報を非同期で取得

**処理フロー:**
1. Discord Gatewayに接続
2. `on_ready`イベントの発火を待機
3. 全ギルドのVCをスキャン
4. 監視対象チャンネルのメンバーを収集
5. 接続を終了
6. メンバー情報リストを返却

**戻り値:**
```python
[
    {
        "guild_id": "123456789012345678",
        "user_id": "111111111111111111",
        "user_name": "username#1234"
    },
    ...
]
```

**エラーハンドリング:**
- 接続エラー時は例外を再発生
- ログにエラー詳細を記録

##### コンテキストマネージャーメソッド
```python
async def __aenter__(self)
async def __aexit__(self, exc_type, exc_val, exc_tb)
```

**機能:**
- 非同期with文のサポート
- リソースの自動クリーンアップ

## 3. イベントハンドラ

### 3.1 on_ready イベント
```python
@client.event
async def on_ready()
```

**処理内容:**
1. Bot接続成功のログ出力
2. 全ギルドをイテレート
3. 各ギルドのVCチャンネルを確認
4. 監視対象チャンネルのメンバー情報を収集
5. 収集完了後、クライアント接続を終了

## 4. データ構造

### 4.1 メンバー情報
```python
{
    "guild_id": str,      # DiscordサーバーID
    "user_id": str,       # ユーザー固有ID
    "user_name": str      # ユーザー名#識別子
}
```

### 4.2 内部状態
- `self.members_data`: メンバー情報を格納するリスト
- `self.client`: Discord.pyクライアントインスタンス

## 5. 依存関係

### 5.1 外部ライブラリ
- `discord.py`: Discord API ラッパー
- `asyncio`: 非同期処理

### 5.2 標準ライブラリ
- `os`: 環境変数の取得
- `logging`: ログ出力
- `typing`: 型ヒント

## 6. 設定要件

### 6.1 Discord Bot設定
- **必要な権限:**
  - Server Members Intent
  - Voice States Intent
  - View Channels
  - Connect（VC接続確認用）

### 6.2 環境変数
- `DISCORD_BOT_TOKEN`: Botトークン（必須）
- `ALLOWED_VOICE_CHANNEL_IDS`: カンマ区切りのチャンネルID（必須）

## 7. エラー処理

### 7.1 接続エラー
- Discord APIへの接続失敗時は例外を発生
- エラー詳細をログに記録

### 7.2 権限エラー
- 必要な権限が不足している場合はログに警告を出力
- 処理は継続（取得可能な範囲で情報収集）

## 8. ログ出力

### 8.1 ログレベル
- `INFO`: 正常な処理フロー
  - Bot接続成功
  - VCチェック開始
  - メンバー発見
- `ERROR`: エラー発生時
  - 接続失敗
  - 予期しない例外

### 8.2 ログフォーマット
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 9. パフォーマンス考慮事項

### 9.1 非同期処理
- すべてのI/O操作は非同期で実行
- 複数ギルド/チャンネルの並行処理

### 9.2 接続管理
- 必要最小限の接続時間
- データ取得後は即座に接続終了

## 10. セキュリティ考慮事項

### 10.1 トークン管理
- Botトークンは環境変数から取得
- トークンをログに出力しない
- マスキング処理の実装

### 10.2 データプライバシー
- 必要最小限の情報のみ取得
- ユーザーIDは匿名化可能な形式で保存

## 11. 制限事項

### 11.1 Rate Limit
- Discord APIのレート制限に従う
- 1秒あたりのリクエスト数に制限

### 11.2 スケーラビリティ
- 大規模サーバー（1000人以上）では処理時間が増加
- 複数VCの同時監視は順次処理

## 12. 今後の拡張可能性

### 12.1 機能拡張
- リアルタイムイベント監視
- VC入退室の検知
- 音声アクティビティの追跡

### 12.2 性能改善
- キャッシュ機構の実装
- 並行処理の最適化
- WebSocket接続の永続化