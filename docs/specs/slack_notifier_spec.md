# Slack通知クライアント仕様書

## 1. 概要

Slack通知クライアントは、Discord VCへのログイン情報をSlackチャンネルに通知するためのモジュールです。

### 1.1 目的
- VCログインのリアルタイム通知
- 通算ログイン日数の表示
- 節目（100日ごと）のお祝い通知
- 日次サマリーの送信

### 1.2 ファイル構成
```
src/
└── slack_notifier.py  # Slack通知クライアント実装
```

## 2. クラス設計

### 2.1 SlackNotifier クラス

#### 2.1.1 責務
- Slack Web APIへの接続管理
- メッセージの送信
- 通知フォーマットの管理
- エラーハンドリング

#### 2.1.2 コンストラクタ
```python
def __init__(self, bot_token: str, channel_id: str)
```

**パラメータ:**
- `bot_token`: Slack Botトークン（xoxb-で始まる）（必須）
- `channel_id`: 通知先チャンネルID（必須）

**初期化処理:**
1. Botトークンの保存
2. チャンネルIDの保存
3. Slack WebClientインスタンスの作成

#### 2.1.3 主要メソッド

##### send_login_notification()
```python
def send_login_notification(user_name: str, total_days: int) -> bool
```

**機能:**
- 個別ユーザーのログイン通知を送信
- 通算日数に応じたメッセージ形式の切り替え

**パラメータ:**
- `user_name`: ユーザー名（例: "username#1234"）
- `total_days`: 通算ログイン日数

**メッセージフォーマット:**

通常時（100日の倍数以外）:
```
🎤 username#1234 さんがログインしました！（通算 15 日目）
```

節目（100日ごと）:
```
🎉 username#1234 さんがログインしました！（通算 100 日目！おめでとう！）
```

**処理フロー:**
1. 通算日数の確認（100の倍数かチェック）
2. メッセージフォーマットの選択
3. Slack APIでメッセージ送信
4. 送信結果の確認

**戻り値:**
- `True`: 送信成功
- `False`: 送信失敗

**エラーハンドリング:**
- SlackApiError: APIエラーをキャッチしてログ出力
- その他の例外: 予期しないエラーをキャッチ

##### send_daily_summary()
```python
def send_daily_summary(members_count: int, members_list: list) -> bool
```

**機能:**
- 日次のログインサマリーを送信
- メンバー数とリストの表示

**パラメータ:**
- `members_count`: ログインメンバー数
- `members_list`: メンバー名のリスト

**メッセージフォーマット:**

メンバーなし:
```
📊 本日のVCログイン: なし
```

メンバーあり（10名以下）:
```
📊 本日のVCログイン: 3名
user1, user2, user3
```

メンバーあり（11名以上）:
```
📊 本日のVCログイン: 15名
user1, user2, ..., user10 他5名
```

**処理フロー:**
1. メンバー数の確認
2. 表示メンバーの選択（最大10名）
3. メッセージフォーマット作成
4. Slack APIでメッセージ送信

**戻り値:**
- `True`: 送信成功
- `False`: 送信失敗

##### test_connection()
```python
def test_connection() -> bool
```

**機能:**
- Slack接続のテスト
- Bot認証の確認

**処理フロー:**
1. `auth.test` APIを呼び出し
2. 認証情報の確認
3. チーム名の取得

**戻り値:**
- `True`: 接続成功
- `False`: 接続失敗

**ログ出力:**
```
INFO: Slack connection test successful: TeamName
ERROR: Slack connection test failed: [詳細]
```

## 3. メッセージ設計

### 3.1 絵文字の使い分け
- 🎤: 通常のログイン通知
- 🎉: 節目のお祝い（100日ごと）
- 📊: 日次サマリー

### 3.2 メッセージ構成要素
1. **絵文字**: 視覚的な識別
2. **ユーザー名**: Discord名#識別子
3. **通算日数**: ゲーミフィケーション要素
4. **お祝いメッセージ**: モチベーション向上

## 4. 依存関係

### 4.1 外部ライブラリ
- `slack-sdk`: Slack公式SDK
- `slack_sdk.web`: WebClient
- `slack_sdk.errors`: エラークラス

### 4.2 標準ライブラリ
- `logging`: ログ出力
- `typing`: 型ヒント

## 5. 設定要件

### 5.1 Slack App設定
- **必要な権限（OAuth Scopes）:**
  - `chat:write`: メッセージ送信
  - `chat:write.public`: パブリックチャンネルへの送信

### 5.2 環境変数
- `SLACK_BOT_TOKEN`: Botトークン（xoxb-）
- `SLACK_CHANNEL_ID`: チャンネルID（C1234567890形式）

### 5.3 Bot設定
1. Slack APIでAppを作成
2. OAuth & Permissionsで権限設定
3. ワークスペースにインストール
4. Botをチャンネルに招待

## 6. エラー処理

### 6.1 API エラー
- `channel_not_found`: チャンネルが見つからない
- `not_in_channel`: Botがチャンネルに参加していない
- `invalid_auth`: 認証エラー
- `rate_limited`: レート制限

### 6.2 エラーレスポンス処理
```python
try:
    response = client.chat_postMessage(...)
    if response["ok"]:
        return True
    else:
        logger.error(f"Failed: {response}")
        return False
except SlackApiError as e:
    logger.error(f"Slack API error: {e.response['error']}")
    return False
```

### 6.3 フォールバック
- 送信失敗時はFalseを返却
- 上位層でリトライ判断

## 7. ログ出力

### 7.1 ログレベル
- `INFO`: 正常処理
  - メッセージ送信成功
  - 接続テスト成功
- `ERROR`: エラー発生
  - API エラー
  - 送信失敗
  - 認証エラー

### 7.2 ログメッセージ例
```
INFO: Slack notification sent: 🎤 user#1234 さんがログインしました！（通算 10 日目）
INFO: Daily summary sent: 5 members
ERROR: Slack API error: channel_not_found
ERROR: Unexpected error sending Slack notification: [詳細]
```

## 8. パフォーマンス考慮事項

### 8.1 Rate Limit対策
- Slack API: 1秒あたり1メッセージ
- Web API: Tier 3（50+ per minute）
- バースト制限: 瞬間的な大量送信を避ける

### 8.2 非同期処理
- 現在は同期処理
- 将来的には非同期化を検討

### 8.3 バッチ処理
- 複数通知をまとめて送信
- スレッド機能の活用

## 9. セキュリティ考慮事項

### 9.1 トークン管理
- Botトークンは環境変数で管理
- ログにトークンを出力しない
- GitHub Secretsで暗号化保存

### 9.2 チャンネルアクセス
- プライベートチャンネルは明示的な招待が必要
- パブリックチャンネルは`chat:write.public`権限で送信可能

### 9.3 メッセージ内容
- 個人情報の最小化
- ユーザーIDは含めない（プライバシー保護）

## 10. 通知戦略

### 10.1 通知タイミング
- 新規ログイン時: 即座に通知
- 日次サマリー: バッチ処理後

### 10.2 通知の重複防止
- 同一ユーザーの重複通知を防ぐ
- 上位層（poll_once.py）で制御

### 10.3 通知の優先度
1. 節目のお祝い（最優先）
2. 通常のログイン通知
3. 日次サマリー

## 11. 制限事項

### 11.1 メッセージ長制限
- 1メッセージ: 最大40,000文字
- 実用上は3,000文字程度を推奨

### 11.2 ファイル添付
- 現在は未対応
- 将来的にグラフ画像の添付を検討

### 11.3 インタラクティブ機能
- ボタンやメニューは未実装
- 単方向の通知のみ

## 12. 今後の拡張可能性

### 12.1 機能拡張
- リッチメッセージ（Block Kit）対応
- スレッド返信機能
- メンション機能
- 画像・グラフの添付
- インタラクティブボタン

### 12.2 通知の高度化
- 個人別通知設定
- 通知時間のカスタマイズ
- 週次・月次レポート
- ランキング表示
- 連続ログイン日数の追跡

### 12.3 他サービス連携
- Discord連携（双方向）
- メール通知
- Webhook対応