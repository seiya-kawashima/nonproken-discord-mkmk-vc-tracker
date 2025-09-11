# 開発環境ガイド

## 📋 目次
- [開発方針](#開発方針)
- [クロスプラットフォーム対応](#クロスプラットフォーム対応)
- [開発環境セットアップ](#開発環境セットアップ)
- [Dockerが不要な理由](#dockerが不要な理由)
- [トラブルシューティング](#トラブルシューティング)

## 開発方針

### 🤖 Claude Code によるVibe Coding

このプロジェクトは**Claude Code**を使用したVibe Codingで開発されています。

#### Vibe Codingとは
- **AIアシスタント主導**の開発スタイル
- 開発者は**設計と方針の決定**に集中
- コードの実装は**Claude Codeが全て担当**

#### 開発スタイル
```
開発者の役割:
✅ 仕様の定義と要件の明確化
✅ アーキテクチャの決定
✅ テスト方針の指示とシナリオ定義
✅ コードレビューと品質確認
❌ コードの手入力・手動実装

Claude Codeの役割:
✅ コードの実装
✅ テストの作成
✅ ドキュメントの生成
✅ リファクタリング
```

#### なぜVibe Codingなのか

| 従来の開発 | Vibe Coding |
|------------|------------|
| 開発者がコードを手入力 | Claude Codeが実装 |
| タイプミスやシンタックスエラーが発生 | 文法的に正しいコードを生成 |
| 実装に時間がかかる | 高速な実装 |
| ドキュメント作成が後回し | 実装と同時にドキュメント生成 |
| コーディング規約の統一が困難 | 一貫したコーディングスタイル |

#### 実際の開発フロー
```markdown
1. 開発者: 「Discord VCの参加者を取得して、Google Sheetsに記録する機能を作って」
2. Claude Code: 仕様書作成 → 実装 → テスト作成 → ドキュメント更新
3. 開発者: コードレビューと動作確認
4. Claude Code: フィードバックに基づく修正
```

#### 重要な原則
- **コードは一切手入力しない** - すべてClaude Codeに実装を依頼
- **自然言語で指示** - 「こういう機能が欲しい」と伝えるだけ
- **品質は妥協しない** - AIが書いたコードも厳密にレビュー
- **ドキュメント重視** - 実装と同時にドキュメントを整備

## クロスプラットフォーム対応

### ✅ 対応OS
このプロジェクトは以下のOSで完全に動作します：
- **Windows 10/11**
- **macOS 11.0以降**
- **Ubuntu 20.04以降**
- **その他のLinuxディストリビューション**

### 🎯 互換性の保証

| 機能 | Windows | macOS | Linux | 備考 |
|---|:---:|:---:|:---:|---|
| Python 3.11+ | ✅ | ✅ | ✅ | 全OS共通 |
| パッケージインストール | ✅ | ✅ | ✅ | pip使用 |
| パス処理 | ✅ | ✅ | ✅ | Pathlib使用 |
| 文字エンコーディング | ✅ | ✅ | ✅ | UTF-8統一 |
| 環境変数 | ✅ | ✅ | ✅ | python-dotenv |
| VSCode開発 | ✅ | ✅ | ✅ | 設定ファイル共通 |
| GitHub Actions | ✅ | ✅ | ✅ | Ubuntu環境で実行 |

### 🔧 実装における互換性対策

#### 1. パス処理の統一
```python
# ❌ OS依存のパス処理
log_file = "logs\\test.log"  # Windowsのみ
log_file = "logs/test.log"   # Unix系のみ

# ✅ クロスプラットフォーム対応
from pathlib import Path
log_file = Path("logs") / "test.log"  # 全OS対応
```

#### 2. 文字エンコーディング
```python
# すべてのファイルI/OでUTF-8を明示指定
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

#### 3. 改行コード
- Pythonが自動的に処理するため、特別な対策不要
- Git設定で`core.autocrlf`を適切に設定

## 開発環境セットアップ

### 🚀 全OS共通の手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/seiya-kawashima/discord-mkmk-vc-tracker.git
cd discord-mkmk-vc-tracker

# 2. Python仮想環境の作成
python -m venv .venv
# macOSで python3 コマンドの場合
python3 -m venv .venv

# 3. 仮想環境の有効化
# Windows (Command Prompt)
.venv\Scripts\activate.bat
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# 4. 依存パッケージのインストール
pip install -r requirements.txt

# 5. 開発用パッケージのインストール（オプション）
pip install -r requirements-dev.txt

# 6. 環境変数の設定
cp .env.example .env
# .envファイルを編集して実際の値を設定

# 7. 動作確認
python -c "import discord, gspread, slack_sdk; print('✅ All packages installed successfully!')"
```

### 🍎 macOS固有の注意点

#### Python のインストール
```bash
# Homebrewを使用する場合
brew install python@3.11

# または公式インストーラーから
# https://www.python.org/downloads/
```

#### SSL証明書エラーが発生した場合
```bash
# 証明書の更新
pip install --upgrade certifi
```

### 🪟 Windows固有の注意点

#### PowerShell実行ポリシー
```powershell
# スクリプト実行を許可（管理者権限で実行）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 長いパス名のサポート
```powershell
# Windows 10/11で長いパス名を有効化（管理者権限）
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### 🐧 Linux固有の注意点

#### Python開発ツールのインストール
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv

# RHEL/CentOS/Fedora
sudo yum install python3-pip python3-virtualenv
```

## Dockerが不要な理由

### 🐳 なぜDockerを使わないのか？

#### 1. **シンプルな実行環境**
- Python + 数個のライブラリのみ
- 特殊なシステム依存なし
- OS固有の設定不要

#### 2. **GitHub Actionsで十分**
```yaml
# .github/workflows/poll.yml
runs-on: ubuntu-latest
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: "3.11"
  - run: pip install -r requirements.txt
  - run: python poll_once.py
```
→ これだけで動作する簡潔さ

#### 3. **実行方式がステートレス**
- 30分ごとの定期実行
- 状態を持たない（データはGoogle Sheetsに保存）
- コンテナの永続化不要

#### 4. **オーバーヘッドの回避**

| 項目 | Dockerあり | Dockerなし |
|---|---|---|
| セットアップ時間 | 5-10分 | 1-2分 |
| 実行時間 | 3-5分 | 1-2分 |
| ディスク使用量 | 500MB+ | 50MB |
| メモリ使用量 | 200MB+ | 50MB |
| 複雑性 | 高 | 低 |

#### 5. **依存関係がシンプル**
```txt
discord.py     # Discord API
gspread        # Google Sheets
slack-sdk      # Slack API
python-dotenv  # 環境変数
pytz          # タイムゾーン
```
→ すべて`pip install`で解決

### 📊 Docker化の判断基準

#### Docker化を検討すべき場合 ❌ 現状
- 複数のデータベースを使用 → **使用していない**
- 複雑なネットワーク構成 → **不要**
- マイクロサービス構成 → **単一スクリプト**
- 特殊なOS依存ライブラリ → **なし**
- チーム開発での環境統一 → **仮想環境で十分**

#### 現在の構成で十分な理由 ✅
- **ポータビリティ**: Python仮想環境で実現
- **再現性**: requirements.txtで保証
- **隔離性**: venvで十分
- **CI/CD**: GitHub Actionsネイティブ対応

### 🎯 結論

**Dockerは不要です** - シンプルさを保つことで：
- 開発速度向上
- デバッグの容易さ
- 運用コストの削減
- 学習コストの低減

## トラブルシューティング

### 共通の問題と解決策

#### pip install でエラーが発生
```bash
# pipをアップグレード
python -m pip install --upgrade pip

# キャッシュをクリアして再インストール
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

#### import エラーが発生
```bash
# 仮想環境が有効か確認
which python  # Unix系
where python  # Windows

# 期待される出力：.venv内のpython
# 違う場合は仮想環境を再度有効化
```

#### 環境変数が読み込まれない
```python
# デバッグ用コード
import os
from dotenv import load_dotenv

load_dotenv()
print(f"Token exists: {bool(os.getenv('DISCORD_BOT_TOKEN'))}")
```

### OS別トラブルシューティング

#### macOS: `pip install discord.py` でエラー
```bash
# Xcodeコマンドラインツールをインストール
xcode-select --install
```

#### Windows: 文字化けが発生
```python
# Pythonスクリプトの先頭に追加
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

#### Linux: 権限エラー
```bash
# ログディレクトリの権限を修正
chmod 755 logs
```

## 開発のベストプラクティス

### 1. コミット前の確認
```bash
# コード整形
black src/

# 型チェック
mypy src/

# テスト実行
pytest tests/
```

### 2. 仮想環境の管理
```bash
# 依存関係の更新後
pip freeze > requirements.txt

# 定期的なアップデート
pip list --outdated
```

### 3. ログレベルの活用
```python
# 開発時
logger = VCTrackerLogger.get_logger(level=0)  # TRACE

# 本番時
logger = VCTrackerLogger.get_logger(level=2)  # INFO
```

## サポート

問題が解決しない場合：
1. [Issues](https://github.com/your-username/discord-mkmk-vc-tracker/issues)で報告
2. 以下の情報を含める：
   - OS名とバージョン
   - Pythonバージョン（`python --version`）
   - エラーメッセージ全文
   - 実行したコマンド