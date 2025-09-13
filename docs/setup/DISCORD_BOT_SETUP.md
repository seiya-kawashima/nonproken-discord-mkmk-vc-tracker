# Discord Bot セットアップガイド

## 📌 このガイドについて

Discord Botを作成し、トークンを取得する手順を初心者向けに説明します。
所要時間：約10分

## 🤖 Discord Botとは？

Discord Botは、Discordサーバー内で自動的にタスクを実行するプログラムです。
このプロジェクトでは、VCチャンネルのメンバーを監視するために使用します。

## 📝 事前準備

- Discordアカウント（無料）
- Discordサーバー（テスト用・本番用）
- ウェブブラウザ（Chrome、Firefox等）

## 🚀 Bot作成手順

### ステップ1：Discord Developer Portalにアクセス

1. [Discord Developer Portal](https://discord.com/developers/applications)を開く
2. Discordアカウントでログイン

### ステップ2：新しいアプリケーションを作成

1. 右上の「**New Application**」ボタンをクリック
   
   ![New Application](https://via.placeholder.com/400x100/4C51BF/FFFFFF?text=New+Application+Button)

2. アプリケーション名を入力
   - 本番用例：`VC Tracker Bot`
   - テスト用例：`VC Tracker Bot TEST`

3. 利用規約に同意して「**Create**」をクリック

### ステップ3：Botを作成

1. 左側メニューから「**Bot**」を選択

2. 「**Reset Token**」ボタンをクリック
   - ⚠️ 初回は「Reset Token」と表示されます
   - ⚠️ 2回目以降は既存トークンが無効になります

3. 「**Yes, do it!**」をクリックして確認

4. 表示されたトークンを**安全な場所にコピー**
   ```
   例：MTE2ODU5NTQ2NjU0MzE4MTg2NA.GqPmNv.3jK5...
   ```
   
   ⚠️ **重要な注意事項**：
   - このトークンは**一度しか表示されません**
   - 他人に見せないでください（Botを乗っ取られます）
   - GitHubにコミットしないでください

### ステップ4：Botの設定

#### 基本設定

1. **Public Bot**：
   - ❌ OFF推奨（特定のサーバーのみで使用）
   - ✅ ONにすると誰でもBotを招待できる

2. **Requires OAuth2 Code Grant**：
   - ❌ OFF（不要）

3. **Message Content Intent**：
   - ❌ OFF（VCメンバー取得には不要）

#### 必要な権限（Privileged Gateway Intents）

以下の設定を確認：

| Intent | 設定 | 説明 |
|--------|------|------|
| PRESENCE INTENT | ❌ OFF | ユーザーのオンライン状態（不要） |
| SERVER MEMBERS INTENT | ✅ ON | メンバー情報の取得（必要） |
| MESSAGE CONTENT INTENT | ❌ OFF | メッセージ内容の読み取り（不要） |

### ステップ5：Botをサーバーに招待

1. 左側メニューから「**OAuth2**」→「**URL Generator**」を選択

2. **SCOPES**で以下を選択：
   - ✅ `bot`

3. **BOT PERMISSIONS**で以下を選択：
   - ✅ `View Channels`（チャンネルを見る）
   - ✅ `Connect`（VCに接続）
   - ✅ `View Server Insights`（サーバー情報を見る）

4. 生成された招待URL（Invite Link）をコピー
   ```
   https://discord.com/api/oauth2/authorize?client_id=...&permissions=...
   ```
   ※これがBot招待URLです
   ※[URLを再生成したい場合はこちら](#q-bot招待urlは一回きりですかもう一度見るには)

5. **自分がサーバー管理者の場合**：
   - URLをブラウザで開く
   - Botを追加するサーバーを選択
   - 「**認証**」をクリック
   - 権限を確認して「**はい**」をクリック

6. **自分がサーバー管理者でない場合**：
   - 生成されたURLをサーバー管理者に送る
   - 以下のメッセージテンプレートを使用：
   
   ```
   【Discord Bot招待のお願い】
   
   VC Tracker Botをサーバーに追加していただけますでしょうか。
   
   招待リンク：
   [ここに生成されたURLを貼り付け]
   
   このBotの機能：
   - VCチャンネルのメンバー情報を取得
   - 現在VCにいるユーザーを確認
   
   ※実際のデータ保存や通知は別プログラムが行います
   
   必要な権限：
   - View Channels（チャンネルを見る）
   - Connect（VCに接続）
   - View Server Insights（サーバー情報を見る）
   
   セキュリティ：
   - メッセージの読み書き権限なし
   - 最小限の権限のみ要求
   - Public Bot OFF（招待リンクを持つ人のみ追加可能）
   
   よろしくお願いします。
   ```
   
   - 管理者がリンクをクリックして承認すると、Botがサーバーに追加される

### ステップ6：VCチャンネルIDの取得

1. **Discordの開発者モードを有効化**：
   - Discord設定 → 詳細設定 → 開発者モード：ON

2. **VCチャンネルIDをコピー**：
   - VCチャンネルを右クリック
   - 「チャンネルIDをコピー」を選択
   - 例：`1168595466543181864`

## 🔐 トークンの保管方法

### 開発環境（ローカル）

`.env`ファイルに保存：
```env
DISCORD_BOT_TOKEN=あなたのトークンをここに貼り付け
```

### テスト環境（GitHub）

GitHub Secretsに`TST_DISCORD_BOT_TOKEN`として保存

### 本番環境（GitHub）

GitHub Secretsに`DISCORD_BOT_TOKEN`として保存

## ✅ 動作確認

### 1. Botがオンラインか確認

- Discordサーバーのメンバーリストを確認
- Botが「オンライン」になっていればOK

### 2. 簡単なテストコード

```python
import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Botが正常に起動しました: {client.user}')
    
    # サーバー一覧を表示
    for guild in client.guilds:
        print(f'📍 接続済みサーバー: {guild.name} (ID: {guild.id})')
    
    await client.close()

# トークンを環境変数から取得
token = os.getenv('DISCORD_BOT_TOKEN')
if token:
    client.run(token)
else:
    print('❌ エラー: DISCORD_BOT_TOKEN が設定されていません')
```

## 🚨 トラブルシューティング

### よくあるエラーと対処法

#### 1. 「Invalid Token」エラー
**原因**：トークンが間違っている
**対処**：
- トークンに余分なスペースが含まれていないか確認
- トークンを再生成して試す

#### 2. 「Missing Access」エラー
**原因**：Botに必要な権限がない
**対処**：
- Botの権限を確認
- サーバーから一度削除して再招待

#### 3. Botがオフラインのまま
**原因**：トークンが無効またはコードが実行されていない
**対処**：
- トークンを再生成
- コードのエラーを確認

#### 4. VCメンバーが取得できない
**原因**：Intentsが有効になっていない
**対処**：
- Developer PortalでSERVER MEMBERS INTENTがONか確認
- コードでintents.members = Trueが設定されているか確認

## 📚 参考リンク

- [Discord Developer Documentation](https://discord.com/developers/docs/intro)
- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Permissions Calculator](https://discordapi.com/permissions.html)

## 💡 Tips

### 複数のBotを管理する場合

| 用途 | Bot名の例 | 説明 |
|------|-----------|------|
| 本番 | VC Tracker | 実際の運用で使用 |
| テスト | VC Tracker TEST | 開発・テスト用 |
| 開発 | VC Tracker DEV | ローカル開発用 |

### セキュリティのベストプラクティス

1. **トークンの定期更新**
   - 3ヶ月ごとに新しいトークンを生成
   - 古いトークンは即座に無効化

2. **権限の最小化**
   - 必要最小限の権限のみ付与
   - 不要なIntentsは無効化

3. **環境の分離**
   - 本番用とテスト用で別のBotを使用
   - 別々のサーバーで運用

## ❓ よくある質問

### Q: Botは無料で作れますか？
A: はい、完全無料です。

### Q: 複数のサーバーで同じBotを使えますか？
A: はい、可能です。ただし、本番とテストは分けることを推奨します。

### Q: トークンを忘れてしまいました
A: Developer Portalで「Reset Token」をクリックして新しいトークンを生成してください。

### Q: Botの名前やアイコンは後から変更できますか？
A: はい、Developer Portalでいつでも変更可能です。

### Q: Bot招待URLは一回きりですか？もう一度見るには？
A: **招待URLは何度でも使用可能です。**

**URLの特徴：**
- 一回きりではなく、何度でも使える
- 同じ権限設定なら同じURLが生成される
- 複数のサーバーに同じURLで招待可能

**URLを再取得する方法：**
1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. アプリケーションを選択
3. 左側メニュー「OAuth2」→「URL Generator」
4. 同じSCOPES（bot）とPERMISSIONSを選択
5. 同じURLが表示される

**Tips：**
- URLをメモ帳などに保存しておくと便利
- 権限を変更した場合は新しいURLの生成が必要
- Client IDは変わらないので、URLの基本部分は同じ

### Q: Developer Applicationは他の人も見たり編集できますか？
A: **デフォルトでは作成者のみアクセス可能です。**

**アクセス権限について：**
- **所有者（Owner）**：完全な権限（あなた）
- **チームメンバー**：Developer Portalで招待した人のみ
- **一般ユーザー**：アクセス不可

**チームメンバーを追加する方法：**
1. Developer Portal → アプリケーション選択
2. 左側メニュー「Team」を選択
3. 「Add Team Member」をクリック
4. ユーザー名またはIDで招待

**権限レベル：**
- **Admin**：トークン再生成を含む全権限
- **Developer**：設定変更可能、トークン再生成不可
- **Read-only**：閲覧のみ

⚠️ **注意事項：**
- トークンは見た人が誰でも使える
- チームメンバーは慎重に選ぶ
- 不要になったメンバーは削除する

## 🆘 サポート

問題が解決しない場合は、以下の情報を含めてIssueを作成してください：

1. エラーメッセージの全文
2. 実行したコード
3. Discord Developer Portalの設定スクリーンショット（トークンは隠す）
4. 試した対処法