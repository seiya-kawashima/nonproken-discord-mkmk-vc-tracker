# GitHub Wiki連携ガイド

## 📌 概要

`docs/`フォルダの内容をGitHub Wikiに連携する方法を説明します。

## 🤖 方法1: GitHub Actionsで自動同期（推奨）

### セットアップ

1. **Wikiを有効化**
   - リポジトリのSettings → Features → Wiki にチェック

2. **初回のWikiページ作成**
   - WikiタブからCreate the first pageをクリック
   - 適当な内容で保存（後で上書きされる）

3. **ワークフローを有効化**
   - `.github/workflows/sync-wiki.yml`が既に設定済み
   - `docs/`フォルダに変更があると自動でWikiに同期

### 動作

- `main`または`master`ブランチへのプッシュ時
- `docs/`フォルダ内のファイルが変更された場合
- 自動的にWikiに同期される

## 📝 方法2: 手動でコピー

### 手順

1. **Wikiをローカルにクローン**
```bash
git clone https://github.com/seiya-kawashima/nonproken-discord-mkmk-vc-tracker.wiki.git
cd nonproken-discord-mkmk-vc-tracker.wiki
```

2. **docsの内容をコピー**
```bash
cp -r ../docs/* .
```

3. **Wikiにプッシュ**
```bash
git add -A
git commit -m "Update wiki from docs"
git push
```

## 🔧 方法3: スクリプトで半自動化

### 使い方

```bash
# スクリプトを実行
bash scripts/setup-wiki.sh

# Wikiディレクトリに移動
cd wiki

# 変更をコミット・プッシュ
git add -A
git commit -m "Update wiki"
git push
```

## 📋 GitHub Wikiの制約

### ファイル名の制約

- スペースは使えない（ハイフンかアンダースコアに変換）
- 大文字小文字は区別されない
- ディレクトリ構造は維持されない（フラットになる）

### リンクの書き方

| docs/でのリンク | Wikiでのリンク |
|----------------|---------------|
| `[詳細](setup/DISCORD_BOT_SETUP.md)` | `[詳細](setup-DISCORD_BOT_SETUP)` |
| `[概要](../OVERVIEW.md)` | `[概要](OVERVIEW)` |

### サイドバーのカスタマイズ

`_Sidebar.md`ファイルを作成すると、全ページで共通のサイドバーが表示される：

```markdown
# Navigation

## Setup Guides
- [Discord Bot](setup-DISCORD_BOT_SETUP)
- [Slack Bot](setup-SLACK_BOT_SETUP)
- [Google Sheets](setup-GOOGLE_SHEETS_SETUP)

## Development
- [Environment Setup](DEVELOPMENT)
- [Security](SECURITY)
```

## 🚨 注意事項

### アクセス権限

- WikiはデフォルトでPublic（誰でも閲覧可能）
- 編集権限はコラボレーターのみ
- センシティブな情報は載せない

### 同期の競合

- Wikiを直接編集した場合、同期時に競合する可能性
- 基本的にdocs/フォルダを正として扱う
- Wiki直接編集は避ける

### 画像の扱い

- 画像は別途Wikiにアップロードが必要
- または画像URLを使用
- 相対パスは機能しない

## 🔗 関連リンク

- [GitHub Wiki Documentation](https://docs.github.com/en/communities/documenting-your-project-with-wikis)
- [Wiki vs README](https://docs.github.com/en/communities/documenting-your-project-with-wikis/about-wikis)