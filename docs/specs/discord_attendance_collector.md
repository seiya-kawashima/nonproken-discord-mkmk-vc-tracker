# Discord出席収集処理（discord_attendance_collector.py）仕様書

## 📌 このドキュメントについて

このドキュメントは、**すべてのプログラムを統合して動かす司令塔（メインプログラム）**の設計書です。
各パーツ（Discord、Google Sheets、Slack）を連携させて、自動でVC参加者を記録・通知する仕組みを、初心者の方にも分かりやすく説明します。

---

## 1. 🎯 何をするプログラム？

### このプログラムの役割
想像してみてください。オーケストラの指揮者のように、**各楽器（プログラム）に指示を出して、美しい音楽（自動記録システム）を作り上げる**ようなものです。

### 具体的にできること
- ✅ Discord、Google Sheets、Slackの3つのサービスを連携
- ✅ 定期的に自動実行（30分ごと）
- ✅ エラーが起きても適切に対処
- ✅ 実行結果をログに記録

### 全体の流れ（料理のレシピのように）
1. **材料を準備**（環境設定）
2. **Discord から情報を取得**（誰がVCにいるか確認）
3. **Google Sheets に記録**（出席簿に記入）
4. **Slack に通知**（みんなにお知らせ）

---

## 2. 📥 Input（入力）

### このプログラムが受け取る情報

#### コマンドライン引数
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| **--env** | 数値 | 実行環境（0=本番, 1=テスト, 2=開発） | 1 |

#### 環境変数（環境別）
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| **DISCORD_BOT_TOKEN_{環境}** | 文字列 | Discord Botトークン | DISCORD_BOT_TOKEN_1_TST |
| **DISCORD_VOICE_CHANNEL_IDS_{環境}** | 文字列 | 監視するVCのID | DISCORD_VOICE_CHANNEL_IDS_1_TST |
| **GOOGLE_SERVICE_ACCOUNT_JSON_{環境}** | パス | Google認証ファイル | GOOGLE_SERVICE_ACCOUNT_JSON_1_TST |

#### オプションの入力
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| **GOOGLE_SERVICE_ACCOUNT_JSON** | ファイルパス | Google認証ファイルの場所 | service_account.json |
| **SLACK_BOT_TOKEN** | 文字列 | SlackのBotトークン | xoxb-123456... |
| **SLACK_CHANNEL_ID** | 文字列 | Slack通知先チャンネル | C1234567890 |

---

## 3. 📤 Output（出力）

### このプログラムが出力する情報

| 出力先 | 内容 | 形式 | 例 |
|--------|------|------|-----|
| **コンソール** | 実行ログ | テキスト | 下記参照 |
| **Google Sheets** | 出席記録 | スプレッドシート | 日付、名前、出席状態 |
| **Slack** | 通知メッセージ | チャット | ○○さんがログインしました |
| **終了コード** | 実行結果 | 数値 | 0（成功）/ 1（失敗） |

### ログ出力の例
```
INFO: Fetching VC members from Discord...
INFO: Found 5 members in VCs
INFO: Connecting to Google Sheets...
INFO: Recorded: 3 new, 2 updated
INFO: Sending Slack notifications...
INFO: Poll completed successfully
```

---

## 4. 🔧 どうやって動く？

### 動作の流れ（水が流れるように）

```
スタート
    ↓
① 設定を読み込む（パスワードなど）
    ↓
② Discordで誰がVCにいるか確認
    ↓
③ 誰かいた？
    ├─ はい → ④へ
    └─ いいえ → 終了
    ↓
④ Google Sheetsに記録
    ↓
⑤ Slackの設定ある？
    ├─ はい → ⑥へ
    └─ いいえ → 終了
    ↓
⑥ Slackに通知を送る
    ↓
終了
```

### 各ステップの詳細

#### ステップ1: 準備（環境設定）🔧
**何をする？**
- 必要な設定（トークンやパスワード）を読み込む
- 設定が正しいか確認する

**たとえば：**
- 家の鍵（トークン）があるか確認
- 住所（チャンネルID）が正しいか確認

#### ステップ2: Discord確認 👀
**何をする？**
- DiscordのVCに接続
- 誰がいるかリストアップ

**たとえば：**
- 会議室をのぞいて誰がいるか確認

#### ステップ3: Sheets記録 📝
**何をする？**
- 今日の日付で記録
- 新しい人は追加、既存の人は更新

**たとえば：**
- 出席簿に○をつける

#### ステップ4: Slack通知 📢
**何をする？**
- 参加者の名前と日数を通知
- 100日目などは特別なメッセージ

**たとえば：**
- 社内放送でお知らせ

---

## 5. ⚙️ 必要な設定

### 設定項目一覧（必須とオプション）

#### 必須の設定（これがないと動きません）

| 設定名 | 説明 | 例 |
|--------|------|-----|
| **DISCORD_BOT_TOKEN** | DiscordのBot用パスワード | MTIzNDU2Nzg5... |
| **GOOGLE_SHEET_NAME** | 記録するスプレッドシートの名前 | VC出席記録 |
| **ALLOWED_VOICE_CHANNEL_IDS** | 監視するVCのID（複数可） | 123456789,987654321 |

#### オプションの設定（あると便利）

| 設定名 | 説明 | 例 |
|--------|------|-----|
| **GOOGLE_SERVICE_ACCOUNT_JSON** | Googleの認証ファイルの場所 | service_account.json |
| **SLACK_BOT_TOKEN** | SlackのBot用パスワード | xoxb-123456... |
| **SLACK_CHANNEL_ID** | 通知を送るチャンネル | C1234567890 |

### 設定方法

#### 方法1: .envファイル（開発用）
```
DISCORD_BOT_TOKEN=あなたのトークン
GOOGLE_SHEET_NAME=VC出席記録
ALLOWED_VOICE_CHANNEL_IDS=123456789,987654321
```

#### 方法2: GitHub Secrets（本番用）
1. GitHubのリポジトリを開く
2. Settings → Secrets → Actions
3. 「New repository secret」で追加

---

## 6. 🕐 自動実行の設定

### いつ動く？

#### 現在の設定
- **日本時間 朝4時〜7時**の間
- **30分ごと**に実行
- 例：4:00、4:30、5:00、5:30...

#### なぜこの時間？
- 朝活や早朝勉強会の参加者を記録
- サーバー負荷が少ない時間帯
- 1日の始まりを記録

### 実行時間の変更方法
GitHub Actionsの設定で変更可能：
```yaml
schedule:
  - cron: "0,30 19-22 * * *"  # UTC時間（日本時間-9時間）
```

---

## 7. ⚠️ エラーが起きたら

### よくあるエラーと対処法

#### エラー1: 設定が見つからない
```
ERROR: DISCORD_BOT_TOKEN is not set
```
**意味**: Discordのトークンが設定されていません
**対処**: 環境変数またはGitHub Secretsに設定を追加

#### エラー2: ファイルが見つからない
```
ERROR: Service account JSON file not found
```
**意味**: Googleの認証ファイルがありません
**対処**: ファイルを正しい場所に配置

#### エラー3: 接続エラー
```
ERROR: Failed to connect to Discord
```
**意味**: Discordに接続できません
**対処**: トークンが正しいか、ネットワークを確認

### エラー時の動作
1. **エラーログを出力**
2. **プログラムを停止**
3. **GitHub Actionsで失敗として記録**
4. **次回の実行時間まで待機**

---

## 8. 📊 実行結果の確認

### ログの見方

#### 正常な実行ログの例
```
2025-01-20 04:00:00 - INFO: Fetching VC members from Discord...
2025-01-20 04:00:05 - INFO: Found 5 members in VCs
2025-01-20 04:00:06 - INFO: Connecting to Google Sheets...
2025-01-20 04:00:08 - INFO: Recorded: 3 new, 2 updated
2025-01-20 04:00:09 - INFO: Sending Slack notifications...
2025-01-20 04:00:12 - INFO: Poll completed successfully
```

#### ログの読み方
| 項目 | 意味 |
|------|------|
| **時刻** | いつ実行されたか |
| **INFO** | 正常な処理 |
| **ERROR** | エラー発生 |
| **メッセージ** | 何をしているか |

### GitHub Actionsでの確認方法
1. GitHubリポジトリを開く
2. 「Actions」タブをクリック
3. 実行履歴を確認
4. 詳細を見たい実行をクリック

---

## 9. 🚀 処理速度について

### 処理時間の目安

| 処理内容 | 時間 |
|----------|------|
| Discord接続・取得 | 5〜10秒 |
| Sheets記録 | 2〜5秒 |
| Slack通知（5人分） | 5〜10秒 |
| **合計** | **15〜30秒** |

### 処理が遅い場合
- 参加者が多い（50人以上）
- ネットワークが遅い
- APIの制限に達している

---

## 10. 🧪 テストについて

### テスト方法

#### ユニットテスト
```bash
# 個別機能のテスト
pytest tests/test_discord_client.py -v
pytest tests/test_drive_csv_client.py -v
```

#### 統合テスト
```bash
# モックデータを使用した統合テスト
pytest tests/test_integration.py -v
```

#### エンドツーエンドテスト
```python
# main()関数を直接呼び出してテスト
import discord_attendance_collector
import sys

# テスト環境で実行
sys.argv = ['discord_attendance_collector.py', '--env', '1']
exit_code = discord_attendance_collector.main()

# 結果検証
assert exit_code == 0  # 正常終了を確認
```

### テスト環境の設定
- 必ず`--env 1`（テスト環境）を使用
- モックデータでAPIをシミュレート
- 実際の外部サービスへのアクセスを避ける

## 11. 🛡️ セキュリティについて

### 安全に使うための注意点

#### パスワード（トークン）の管理
- ❌ コードに直接書かない
- ❌ 公開リポジトリにアップしない
- ✅ 環境変数で管理
- ✅ GitHub Secretsで暗号化

#### ログの安全性
- パスワードは表示しない
- 個人情報は最小限
- エラー詳細は必要な範囲のみ

---

## 12. 💡 よくある質問（FAQ）

### Q1: 手動で実行できますか？
**A:** はい、以下の方法で可能です：
- 本番環境: `python discord_attendance_collector.py --env 0`
- テスト環境: `python discord_attendance_collector.py --env 1`
- 開発環境: `python discord_attendance_collector.py --env 2`
- GitHub: Actionsページから「Run workflow」

### Q2: 実行頻度を変更できますか？
**A:** はい、GitHub Actionsの設定で変更できます。ただし、あまり頻繁にすると制限に達する可能性があります。

### Q3: 複数のDiscordサーバーに対応できますか？
**A:** 現在のバージョンでは、複数のVCチャンネルには対応していますが、サーバーは1つです。

### Q4: ログはどこに保存されますか？
**A:** GitHub Actionsの実行ログに保存されます（90日間保持）。

### Q5: エラーが起きたら通知されますか？
**A:** GitHub Actionsの設定で、失敗時にメール通知を受け取れます。

---

## 12. 🔧 メンテナンスとアップデート

### 定期的な確認事項

#### 毎週確認
- [ ] GitHub Actionsが正常に動作しているか
- [ ] エラーログがないか

#### 毎月確認
- [ ] トークンの有効期限
- [ ] API使用量
- [ ] スプレッドシートの容量

#### 毎年確認
- [ ] 依存ライブラリのアップデート
- [ ] APIの仕様変更
- [ ] セキュリティアップデート

---

## 13. 🚧 今後の改善予定

### 近い将来追加したい機能
- ⏰ 実行時間の柔軟な設定
- 📧 エラー時のメール通知
- 📊 実行統計の可視化
- 🔄 リトライ機能

### 長期的な目標
- リアルタイム監視
- 複数サーバー対応
- Web管理画面
- AIによる異常検知

---

## 14. 📚 もっと詳しく知りたい方へ

### システム構成図
```
GitHub Actions（定期実行）
        ↓
   poll_once.py（司令塔）
        ↓
    ┌───┴───┐
    ↓        ↓
Discord    Google
  Bot      Sheets
    ↓        ↓
    └───┬───┘
        ↓
     Slack
```

### 関連用語集

| 用語 | 説明 |
|------|------|
| **環境変数** | プログラムの設定を保存する場所 |
| **トークン** | サービスにアクセスするためのパスワード |
| **API** | プログラム同士が通信する仕組み |
| **非同期処理** | 複数の処理を同時に行う技術 |
| **GitHub Actions** | 自動実行サービス |
| **cron** | 定期実行のスケジュール形式 |

### 参考リンク
- [GitHub Actions Documentation](https://docs.github.com/actions) - 自動実行の設定
- [Python asyncio](https://docs.python.org/3/library/asyncio.html) - 非同期処理
- [環境変数の設定方法](https://docs.github.com/actions/security-guides/encrypted-secrets) - セキュリティ

---

## 15. 📞 サポート

問題が発生した場合は、以下の情報を準備してお問い合わせください：

1. **エラーメッセージ**の全文
2. **実行時刻**
3. **GitHub Actionsのログ**
4. **環境変数の設定状況**（トークンは除く）
5. **最後に成功した日時**

この仕様書は定期的に更新されます。最新版は常にこのファイルを参照してください。

---

*最終更新日: 2025年1月*