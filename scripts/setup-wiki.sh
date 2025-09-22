#!/bin/bash

# GitHub Wikiをサブモジュールとして追加
echo "Setting up Wiki as submodule..."

# Wikiリポジトリをクローン
git clone https://github.com/seiya-kawashima/nonproken-discord-mkmk-vc-tracker.wiki.git wiki

# docsの内容をWikiにコピー
echo "Copying docs to wiki..."
cp -r docs/* wiki/

# Wikiのホームページを作成
cat > wiki/Home.md << 'EOF'
# VC Tracker Documentation

このWikiはリポジトリの`docs/`フォルダから自動生成されています。

## 📚 ドキュメント一覧

### 🚀 セットアップガイド
- [Discord Bot セットアップ](setup-DISCORD_BOT_SETUP)
- [Slack Bot セットアップ](setup-SLACK_BOT_SETUP)  
- [Google Sheets セットアップ](setup-GOOGLE_SHEETS_SETUP)

### 📖 開発ドキュメント
- [開発環境構築](DEVELOPMENT)
- [環境別設定](ENVIRONMENTS)
- [セキュリティガイド](SECURITY)
- [CI/CDスキップ方法](CI_CD_SKIP)

### 📊 仕様書
- [システム概要](OVERVIEW)
- [ログ設計](LOGGING)

### 📁 詳細仕様
- [poll_once.py](specs-poll_once)
- [Discord Client](specs-src-discord_client)
- [Sheets Client](specs-src-sheets_client)
- [Slack Notifier](specs-src-slack_notifier)
- [テスト仕様](specs-tests-test_spec)
EOF

# Wikiファイル名を調整（GitHub Wikiの制約対応）
cd wiki
for file in $(find . -name "*.md"); do
    # スラッシュをハイフンに変換
    newname=$(echo $file | sed 's/\//\-/g' | sed 's/^\.\-//')
    if [ "$file" != "./$newname" ]; then
        mv "$file" "$newname"
    fi
done

echo "Wiki setup complete!"
echo "Next steps:"
echo "1. cd wiki"
echo "2. git add -A"
echo "3. git commit -m 'Update wiki'"
echo "4. git push"