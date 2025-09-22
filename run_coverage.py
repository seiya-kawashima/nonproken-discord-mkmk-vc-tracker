#!/usr/bin/env python
# ========================================
# カバレッジレポート生成スクリプト
# ========================================
# 概要: テストを実行してコードカバレッジを測定し、
#       見やすいレポートを生成する開発補助ツール
#
# 使い方:
#   python run_coverage.py        # 基本実行
#   python run_coverage.py --html # HTMLレポートを自動で開く
#   python run_coverage.py --ci   # CI環境用（エラー時にexit 1）
# ========================================

import subprocess  # 外部コマンドを実行するためのモジュール
import sys  # システム関連の機能を使用
import os  # OSの機能を使用（ファイル操作など）
import webbrowser  # ブラウザでHTMLを開くため
import argparse  # コマンドライン引数の処理
from pathlib import Path  # パス操作を簡潔に行うため

def run_coverage():
    """カバレッジ測定とレポート生成を実行"""

    # PYTHONPATHを設定（現在のディレクトリを追加）
    if 'PYTHONPATH' not in os.environ:  # 環境変数が設定されていない場合
        os.environ['PYTHONPATH'] = '.'  # 現在のディレクトリを追加
    elif '.' not in os.environ['PYTHONPATH']:  # 現在のディレクトリが含まれていない場合
        os.environ['PYTHONPATH'] = '.' + os.pathsep + os.environ['PYTHONPATH']  # 現在のディレクトリを追加

    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='テストカバレッジを測定してレポートを生成')  # パーサー作成
    parser.add_argument('--html', action='store_true', help='HTMLレポートを自動で開く')  # --htmlオプション
    parser.add_argument('--ci', action='store_true', help='CI環境用（失敗時にexit 1）')  # --ciオプション
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細な出力を表示')  # -vオプション
    args = parser.parse_args()  # 引数を解析

    # カバレッジデータをクリーンアップ
    print("🧹 既存のカバレッジデータをクリーンアップ中...")  # 進捗表示
    subprocess.run(['coverage', 'erase'], capture_output=True)  # 既存データを削除

    # HTMLレポートディレクトリをクリーンアップ
    htmlcov_path = Path('htmlcov')  # HTMLレポートのパス
    if htmlcov_path.exists():  # ディレクトリが存在する場合
        import shutil  # ディレクトリ削除用
        shutil.rmtree(htmlcov_path)  # ディレクトリを削除
        print("   HTMLレポートディレクトリを削除しました")  # 完了メッセージ

    # pytestコマンドの構築
    pytest_cmd = ['pytest']  # 基本コマンド

    if not args.verbose:  # 詳細出力でない場合
        pytest_cmd.append('-q')  # 静かモード

    pytest_cmd.extend([
        '--tb=short',  # トレースバックを短縮表示
    ])

    # テスト実行
    print("\n🧪 テストを実行中...")  # 進捗表示
    result = subprocess.run(pytest_cmd, capture_output=False)  # テスト実行

    if result.returncode != 0:  # テストが失敗した場合
        print("\n❌ テストが失敗しました")  # エラーメッセージ
        if args.ci:  # CI環境の場合
            sys.exit(1)  # エラーコードで終了
        return False  # 失敗を返す

    print("\n✅ すべてのテストが成功しました")  # 成功メッセージ

    # カバレッジレポートの表示
    print("\n📊 カバレッジレポート:")  # レポートヘッダー
    print("=" * 60)  # 区切り線

    # ターミナルレポート
    coverage_report = subprocess.run(
        ['coverage', 'report', '--show-missing'],  # カバーされていない行も表示
        capture_output=False  # 出力を直接表示
    )

    # カバレッジ統計の取得
    coverage_json = subprocess.run(
        ['coverage', 'json', '-o', '-'],  # JSON形式で出力
        capture_output=True,  # 出力をキャプチャ
        text=True  # テキストモードで取得
    )

    if coverage_json.returncode == 0:  # JSON取得成功
        import json  # JSON解析用
        try:
            data = json.loads(coverage_json.stdout)  # JSONをパース
            total_coverage = data['totals']['percent_covered']  # 全体のカバレッジ率

            print("\n" + "=" * 60)  # 区切り線
            print(f"📈 全体のカバレッジ: {total_coverage:.2f}%")  # カバレッジ率表示

            # カバレッジが閾値を下回る場合の警告
            if total_coverage < 70:  # 70%未満の場合
                print(f"⚠️  警告: カバレッジが70%未満です ({total_coverage:.2f}%)")  # 警告表示
                if args.ci:  # CI環境の場合
                    sys.exit(1)  # エラーコードで終了
            elif total_coverage < 80:  # 80%未満の場合
                print(f"💡 ヒント: カバレッジを80%以上に改善しましょう")  # 改善提案
            else:  # 80%以上の場合
                print(f"🎉 素晴らしい！カバレッジが{total_coverage:.2f}%です")  # 称賛メッセージ

        except json.JSONDecodeError:  # JSON解析エラー
            pass  # エラーを無視

    # HTMLレポートの生成確認
    if htmlcov_path.exists():  # HTMLレポートが生成された場合
        index_path = htmlcov_path / 'index.html'  # インデックスファイルのパス
        print(f"\n📄 HTMLレポートが生成されました: {index_path}")  # 生成完了メッセージ

        if args.html:  # --htmlオプションが指定された場合
            print("🌐 ブラウザでHTMLレポートを開いています...")  # 開く前のメッセージ
            webbrowser.open(str(index_path.absolute()))  # ブラウザで開く

    # 使用/未使用コードの可視化情報
    print("\n💡 使用/未使用コードの確認方法:")  # ヘルプ情報
    print("   1. HTMLレポート: htmlcov/index.html をブラウザで開く")  # HTMLレポート
    print("   2. 赤い行: テストでカバーされていないコード")  # 未カバー行
    print("   3. 緑の行: テストでカバーされているコード")  # カバー済み行
    print("   4. 黄色い行: 部分的にカバーされているコード（分岐など）")  # 部分カバー

    # JSON/XMLレポートの案内
    print("\n📋 その他のレポート形式:")  # その他のレポート
    print("   - coverage.xml: CI/CDツール連携用")  # XMLレポート
    print("   - coverage.json: プログラムでの解析用")  # JSONレポート

    return True  # 成功を返す

if __name__ == "__main__":  # スクリプトとして実行された場合
    # 開発環境の依存関係をインストール済みか確認
    try:
        import pytest  # pytestがインポートできるか確認
        import coverage  # coverageがインポートできるか確認
    except ImportError:  # インポートエラーの場合
        print("⚠️  必要なパッケージがインストールされていません")  # エラーメッセージ
        print("以下のコマンドを実行してください:")  # 指示
        print("  pip install -r requirements-2-dev.txt")  # インストールコマンド
        sys.exit(1)  # エラーコードで終了

    # カバレッジ測定を実行
    success = run_coverage()  # メイン処理を実行

    if not success:  # 失敗した場合
        sys.exit(1)  # エラーコードで終了