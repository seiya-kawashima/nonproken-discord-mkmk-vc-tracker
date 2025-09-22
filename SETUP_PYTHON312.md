# Python 3.12 環境セットアップガイド

## 🎯 なぜPython 3.12が必要か
- **discord.py** はPython 3.13で削除された`audioop`モジュールに依存しているため、Python 3.12環境が必要です
- Python 3.13を使用すると`ModuleNotFoundError: No module named 'audioop'`エラーが発生します

## 📋 事前準備

### 1. Python 3.12のインストール確認
```bash
# Windowsの場合
py -0

# 出力例：
#  -V:3.13          Python 3.13 (64-bit)
#  -V:3.12          Python 3.12 (64-bit)  ← これが必要
#  -V:3.9           Python 3.9 (64-bit)
```

Python 3.12が表示されない場合は、[Python公式サイト](https://www.python.org/downloads/)からPython 3.12.xをダウンロードしてインストールしてください。

### 2. Mac/Linuxの場合
```bash
# インストール済みPythonの確認
python3.12 --version

# インストールされていない場合（Mac）
brew install python@3.12

# インストールされていない場合（Ubuntu/Debian）
sudo apt update
sudo apt install python3.12 python3.12-venv
```

## 🚀 仮想環境のセットアップ

### 1. 仮想環境の作成

#### Windows
```powershell
# Python 3.12で仮想環境を作成
py -3.12 -m venv .venv

# 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# 実行ポリシーエラーが出る場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Mac/Linux
```bash
# Python 3.12で仮想環境を作成
python3.12 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate
```

### 2. Pythonバージョンの確認
```bash
# 仮想環境内でバージョン確認
python --version
# 出力: Python 3.12.x
```

### 3. 依存パッケージのインストール
```bash
# requirements.txtからインストール
pip install -r requirements.txt

# discord.pyが正常にインストールされたか確認
python -c "import discord; print(f'discord.py version: {discord.__version__}')"
# 出力: discord.py version: 2.3.2
```

## 🔧 VSCode設定

`.vscode/settings.json`を以下のように設定：
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

VSCodeを再起動後、ターミナルを開くと自動的に仮想環境が有効化されます。

## ⚠️ トラブルシューティング

### 問題1: discord.pyインポートエラー
```
ModuleNotFoundError: No module named 'audioop'
```
**解決策**: Python 3.12の仮想環境を使用しているか確認してください。

### 問題2: 仮想環境が有効化できない（Windows）
```
.\.venv\Scripts\Activate.ps1 : このシステムではスクリプトの実行が無効になっています
```
**解決策**: PowerShellの実行ポリシーを変更
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 問題3: pip installが失敗する
**解決策**: pipを最新版にアップデート
```bash
python -m pip install --upgrade pip
```

## 📝 日常的な使い方

### 仮想環境の有効化（毎回必要）
```bash
# Windows
.\.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate
```

### 仮想環境の無効化
```bash
deactivate
```

### パッケージの追加
```bash
# 仮想環境を有効化した状態で
pip install パッケージ名

# requirements.txtに追加
pip freeze > requirements.txt
```

## 🎉 セットアップ完了！
これでPython 3.12環境でdiscord.pyを使用する準備ができました。