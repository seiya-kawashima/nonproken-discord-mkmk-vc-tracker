# CI/CD スキップガイド

## 📌 このガイドについて

GitHub Actionsの実行をスキップしてプッシュする方法を説明します。
ドキュメント更新や設定ファイルの変更など、テストが不要な場合に使用してください。

## 🚀 方法1：コミットメッセージでスキップ（推奨）

### 基本的な使い方

```bash
# ファイルを追加
git add .

# スキップキーワードを含めてコミット
git commit -m "docs: ドキュメント更新 [skip ci]"

# プッシュ
git push
```

### 使用可能なスキップキーワード

以下のキーワードをコミットメッセージに含めると、GitHub Actionsがスキップされます：

| キーワード | 例 |
|-----------|-----|
| `[skip ci]` | `git commit -m "docs: README更新 [skip ci]"` |
| `[ci skip]` | `git commit -m "docs: README更新 [ci skip]"` |
| `[no ci]` | `git commit -m "chore: 設定ファイル更新 [no ci]"` |
| `[skip actions]` | `git commit -m "style: フォーマット修正 [skip actions]"` |
| `[actions skip]` | `git commit -m "docs: typo修正 [actions skip]"` |

### 実践例

```bash
# ドキュメントのみの更新
git add docs/
git commit -m "docs: セットアップガイド追加 [skip ci]"
git push

# 設定ファイルの更新
git add .env.example
git commit -m "chore: 環境変数テンプレート更新 [ci skip]"
git push

# READMEの更新
git add README.md
git commit -m "docs: インストール手順を更新 [no ci]"
git push
```

## 🚀 方法2：自動スキップ（設定済み）

### 現在の設定

`test.yml`に以下のパスが除外設定されているため、これらのファイルを変更してもテストは実行されません：

```yaml
paths-ignore:
  - '**.md'        # すべてのMarkdownファイル
  - 'docs/**'      # docsフォルダ内のすべてのファイル
  - '.gitignore'   # .gitignoreファイル
  - 'LICENSE'      # ライセンスファイル
```

### 自動スキップされるファイル例

以下のファイルを変更した場合、自動的にCI/CDがスキップされます：

✅ **スキップされる：**
- `README.md`
- `docs/SETUP.md`
- `docs/setup/DISCORD_BOT_SETUP.md`
- `.gitignore`
- `LICENSE`
- `CHANGELOG.md`

❌ **スキップされない：**
- `*.py`（Pythonファイル）
- `*.yml`（設定ファイル）
- `requirements.txt`
- `src/`内のファイル
- `tests/`内のファイル

## 📊 スキップ状況の確認

### GitHubでの確認方法

1. リポジトリの**Actions**タブを開く
2. コミット横のアイコンを確認：
   - ⭕ 灰色のマーク = スキップされた
   - ✅ 緑のチェック = 成功
   - ❌ 赤のX = 失敗
   - 🟡 黄色の丸 = 実行中

### コマンドラインでの確認

```bash
# 最新のワークフロー実行状況を確認
gh run list --limit 5

# 特定のコミットのワークフロー状況を確認
gh run list --commit HEAD
```

## ⚠️ 注意事項

### スキップすべきでない場合

以下の変更時は**必ずテストを実行**してください：

- 🔴 **ソースコードの変更**（`src/`内のファイル）
- 🔴 **テストコードの変更**（`tests/`内のファイル）
- 🔴 **依存関係の変更**（`requirements.txt`）
- 🔴 **ワークフローの変更**（`.github/workflows/`内のファイル）
- 🔴 **設定ファイルの変更**（`.env.example`など）

### スキップしても良い場合

- 🟢 **ドキュメントの更新**
- 🟢 **READMEの修正**
- 🟢 **typoの修正**（ドキュメント内）
- 🟢 **ライセンスファイルの更新**
- 🟢 **画像ファイルの追加**

## 🔧 トラブルシューティング

### Q: スキップキーワードを入れたのに実行される

**原因と対処法：**
1. キーワードの位置を確認（コミットメッセージ内ならどこでもOK）
2. スペルミスがないか確認
3. 対象のワークフローがpush/PRトリガーか確認（scheduleは除外不可）

### Q: ドキュメント変更なのにテストが実行される

**原因と対処法：**
1. 他のファイルも一緒に変更していないか確認
2. `git status`で変更ファイルを確認
3. 必要なら`[skip ci]`を明示的に追加

### Q: スキップしたコミットを後からテストしたい

**手動実行方法：**
1. GitHub → Actions → 対象のワークフロー
2. 「Run workflow」ボタンをクリック
3. ブランチを選択して実行

または：
```bash
# GitHub CLIを使用
gh workflow run test.yml
```

## 💡 ベストプラクティス

### コミットメッセージの書き方

```bash
# 良い例：明確な理由とスキップキーワード
git commit -m "docs: API仕様書を追加 [skip ci]"
git commit -m "chore: エディタ設定を追加（テスト不要） [ci skip]"

# 悪い例：理由が不明確
git commit -m "update [skip ci]"
git commit -m "[skip ci]"
```

### 複数コミットをまとめてプッシュ

```bash
# 複数のドキュメント変更をまとめる
git add docs/
git commit -m "docs: セットアップガイド追加 [skip ci]"

git add README.md
git commit -m "docs: README更新 [skip ci]"

git add .gitignore
git commit -m "chore: gitignore更新 [skip ci]"

# まとめてプッシュ（1回のCI実行をスキップ）
git push
```

## 📚 参考リンク

- [GitHub Actions: Skipping workflow runs](https://docs.github.com/en/actions/managing-workflow-runs/skipping-workflow-runs)
- [GitHub Actions: Workflow syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Conventional Commits](https://www.conventionalcommits.org/) - コミットメッセージの規約