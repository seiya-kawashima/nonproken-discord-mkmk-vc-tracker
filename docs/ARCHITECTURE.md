# システムアーキテクチャ

## 📌 概要

Discord VC Trackerシステムの全体的な処理フローと、各モジュール間の連携を説明します。

## 🔄 メイン処理フロー

```mermaid
flowchart TD
    Start([開始]) --> LoadEnv[環境変数読み込み<br/>.env/GitHub Secrets]
    LoadEnv --> CheckEnv{必須環境変数<br/>チェック}
    CheckEnv -->|NG| Error1[エラー終了]
    CheckEnv -->|OK| CreateDiscord[DiscordVCPoller<br/>インスタンス作成]
    
    CreateDiscord --> GetMembers[VCメンバー取得<br/>get_vc_members]
    GetMembers --> CheckMembers{メンバー<br/>存在?}
    CheckMembers -->|なし| EndNoMembers[処理終了<br/>メンバーなし]
    CheckMembers -->|あり| CreateSheets[SheetsClient<br/>インスタンス作成]
    
    CreateSheets --> ConnectSheets[Google Sheets接続<br/>connect]
    ConnectSheets --> UpsertData[出席データ記録<br/>upsert_presence]
    UpsertData --> CheckSlack{Slack設定<br/>あり?}
    
    CheckSlack -->|なし| EndSuccess[処理成功終了]
    CheckSlack -->|あり| CreateSlack[SlackNotifier<br/>インスタンス作成]
    CreateSlack --> LoopMembers[メンバーごとに処理]
    
    LoopMembers --> GetDays[通算日数取得<br/>get_total_days]
    GetDays --> CheckNew{新規<br/>メンバー?}
    CheckNew -->|いいえ| NextMember{次の<br/>メンバー?}
    CheckNew -->|はい| SendNotif[Slack通知送信<br/>send_login_notification]
    SendNotif --> NextMember
    NextMember -->|あり| GetDays
    NextMember -->|なし| EndSuccess
```

## 🏗️ モジュール構成

```mermaid
graph TB
    subgraph "メインスクリプト"
        Main[discord_attendance_collector.py<br/>メイン処理制御]
    end
    
    subgraph "外部サービス連携"
        Discord[discord_client.py<br/>Discord API連携]
        Sheets[sheets_client.py<br/>Google Sheets API連携]
        Slack[slack_notifier.py<br/>Slack API連携]
    end
    
    subgraph "外部サービス"
        DiscordAPI[Discord API<br/>VCメンバー情報]
        SheetsAPI[Google Sheets API<br/>データ永続化]
        SlackAPI[Slack API<br/>通知]
    end
    
    Main --> Discord
    Main --> Sheets
    Main --> Slack
    
    Discord <--> DiscordAPI
    Sheets <--> SheetsAPI
    Slack <--> SlackAPI
```

## 📊 データフロー

```mermaid
sequenceDiagram
    participant Main as discord_attendance_collector.py
    participant Env as 環境変数
    participant Discord as DiscordVCPoller
    participant Sheets as SheetsClient
    participant Slack as SlackNotifier
    participant DiscordAPI as Discord API
    participant SheetsAPI as Google Sheets
    participant SlackAPI as Slack API
    
    Main->>Env: load_dotenv()
    Env-->>Main: 環境変数取得
    
    Main->>Main: 環境変数チェック
    
    Main->>Discord: new DiscordVCPoller(token, channel_ids)
    Main->>Discord: get_vc_members()
    Discord->>DiscordAPI: VCメンバー情報要求
    DiscordAPI-->>Discord: メンバーリスト
    Discord-->>Main: vc_members[]
    
    alt メンバーが存在する場合
        Main->>Sheets: new SheetsClient(json, sheet_name)
        Main->>Sheets: connect()
        Sheets->>SheetsAPI: 認証・接続
        SheetsAPI-->>Sheets: 接続成功
        
        Main->>Sheets: upsert_presence(vc_members)
        Sheets->>SheetsAPI: データ書き込み
        SheetsAPI-->>Sheets: 書き込み結果
        Sheets-->>Main: {new: X, updated: Y}
        
        opt Slack設定がある場合
            Main->>Slack: new SlackNotifier(token, channel)
            
            loop 各メンバー
                Main->>Sheets: get_total_days(user_id)
                Sheets->>SheetsAPI: 通算日数クエリ
                SheetsAPI-->>Sheets: 日数
                Sheets-->>Main: total_days
                
                opt 新規メンバーの場合
                    Main->>Slack: send_login_notification(name, days)
                    Slack->>SlackAPI: メッセージ送信
                    SlackAPI-->>Slack: 送信結果
                    Slack-->>Main: success
                end
            end
        end
    end
    
    Main->>Main: 処理完了
```

## 🔄 処理の詳細

### 1. 初期化フェーズ
- **環境変数の読み込み**: `.env`ファイルまたはGitHub Secretsから設定を取得
- **必須パラメータチェック**: 
  - `DISCORD_BOT_TOKEN`
  - `GOOGLE_SHEET_NAME`
  - `ALLOWED_VOICE_CHANNEL_IDS`
  - `service_account.json`の存在確認

### 2. データ取得フェーズ
- **Discord接続**: `DiscordVCPoller`クラスを使用してBotとして接続
- **VCメンバー取得**: 指定されたVCチャンネルIDの現在のメンバーを取得
- **データ形式**:
  ```python
  {
      'guild_id': 'サーバーID',
      'user_id': 'ユーザーID',
      'user_name': 'ユーザー名',
      'timestamp': '取得時刻'
  }
  ```

### 3. データ記録フェーズ
- **Google Sheets接続**: サービスアカウントを使用して認証
- **データ記録**: `upsert_presence()`メソッドで出席データを記録
  - 新規メンバー: 新しい行を追加
  - 既存メンバー: 該当日のデータを更新
- **シート構造**:
  ```
  | date_jst | guild_id | user_id | user_name | present |
  ```

### 4. 通知フェーズ（オプション）
- **条件**: Slack設定が存在し、新規メンバーがいる場合
- **通算日数取得**: 各メンバーの過去の出席日数を集計
- **Slack通知**: フォーマットされたメッセージを送信
  ```
  🎊 XXXさんがVCにログインしました！
  通算: Y日目
  ```

## 🔧 エラーハンドリング

```mermaid
flowchart TD
    subgraph "エラー処理パターン"
        E1[環境変数不足] --> Exit1[sys.exit 1]
        E2[Discord接続エラー] --> Log1[エラーログ出力]
        Log1 --> Exit2[sys.exit 1]
        E3[Sheets接続エラー] --> Log2[エラーログ出力]
        Log2 --> Exit3[sys.exit 1]
        E4[Slack送信エラー] --> Log3[警告ログ出力]
        Log3 --> Continue[処理継続]
    end
```

## 📝 ログ出力

各フェーズで以下のログを出力:

1. **開始ログ**: `"Fetching VC members from Discord..."`
2. **メンバー数ログ**: `"Found X members in VCs"`
3. **Sheets接続ログ**: `"Connecting to Google Sheets..."`
4. **記録結果ログ**: `"Recorded: X new, Y updated"`
5. **通知ログ**: `"Notified: Username (Day Z)"`
6. **完了ログ**: `"Poll completed successfully"`

## 🚀 実行方法

### 単体実行
```bash
python discord_attendance_collector.py
```

### GitHub Actions（定期実行）
```yaml
- cron: '*/10 7-12 * * *'  # 日本時間16-21時、10分ごと
```

## 🔍 デバッグ

ログレベルを`DEBUG`に変更することで詳細情報を取得可能:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📋 依存関係

- **discord.py**: Discord API連携
- **gspread**: Google Sheets API連携
- **google-auth**: Google認証
- **slack-sdk**: Slack API連携
- **python-dotenv**: 環境変数管理
- **pytz**: タイムゾーン処理

## 🎯 設計の特徴

1. **モジュール分離**: 各外部サービスとの連携を独立したクラスで実装
2. **エラーハンドリング**: 各フェーズで適切なエラー処理
3. **ログ出力**: 処理の追跡とデバッグを容易に
4. **環境変数管理**: 設定の外部化によるセキュリティ向上
5. **非同期処理**: Discord APIの非同期特性に対応