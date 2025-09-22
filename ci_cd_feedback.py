#!/usr/bin/env python3
"""
CI/CDフィードバックループ自動化スクリプト
GitHub Actionsの結果を解析して、自動的にコードを修正する
"""

import subprocess  # サブプロセス実行用
import json  # JSON解析用
import re  # 正規表現用
import sys  # システム操作用
import time  # 時間操作用
from pathlib import Path  # パス操作用
from typing import List, Dict, Any  # 型ヒント用


class CICDFeedbackLoop:
    """CI/CDフィードバックループを管理するクラス"""
    
    def __init__(self, repo_path: str = "."):
        """初期化"""
        self.repo_path = Path(repo_path)  # リポジトリパス
        self.max_retries = 5  # 最大リトライ回数
        self.retry_count = 0  # 現在のリトライ回数
    
    def get_latest_run_id(self, branch: str = "feature/ci-cd-test") -> str:
        """最新のワークフロー実行IDを取得"""
        cmd = f"gh run list --branch {branch} --limit 1 --json databaseId"  # ghコマンド
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # 実行
        if result.returncode == 0:  # 成功した場合
            data = json.loads(result.stdout)  # JSON解析
            return str(data[0]["databaseId"]) if data else None  # ID返却
        return None  # 失敗時はNone
    
    def get_failed_tests(self, run_id: str) -> List[Dict[str, Any]]:
        """失敗したテストの詳細を取得"""
        cmd = f"gh run view {run_id} --log-failed"  # 失敗ログ取得コマンド
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # 実行
        
        failures = []  # 失敗リスト
        lines = result.stdout.split('\n')  # 行ごとに分割
        
        # TypeErrorパターンを検出
        type_error_pattern = r"TypeError: '(\w+)' object is not callable"  # パターン定義
        file_pattern = r"(tests/[\w/]+\.py):(\d+):"  # ファイルパターン
        
        for i, line in enumerate(lines):  # 各行を処理
            type_match = re.search(type_error_pattern, line)  # エラー検出
            if type_match:  # エラーが見つかった場合
                # 近くのファイル情報を探す
                for j in range(max(0, i-5), min(len(lines), i+5)):  # 前後5行を探索
                    file_match = re.search(file_pattern, lines[j])  # ファイル情報検出
                    if file_match:  # ファイル情報が見つかった場合
                        failures.append({
                            'error_type': 'TypeError',
                            'object_name': type_match.group(1),
                            'file': file_match.group(1),
                            'line': int(file_match.group(2)),
                            'message': line.strip()
                        })
                        break  # 内側ループを抜ける
        
        return failures  # 失敗リストを返す
    
    def analyze_error_pattern(self, failures: List[Dict[str, Any]]) -> Dict[str, Any]:
        """エラーパターンを分析して修正方法を決定"""
        if not failures:  # 失敗がない場合
            return None  # Noneを返す
        
        # VCTrackerLogger not callableエラーの場合
        if all(f['object_name'] == 'VCTrackerLogger' for f in failures):  # 全てVCTrackerLoggerエラー
            return {
                'type': 'import_error',
                'solution': 'use_class_directly',
                'details': 'VCTrackerLoggerクラスを直接使用するように修正'
            }
        
        return None  # その他のパターンはNone
    
    def apply_fix(self, solution: Dict[str, Any]) -> bool:
        """修正を適用"""
        if solution['type'] == 'import_error' and solution['solution'] == 'use_class_directly':
            # テストファイルを修正
            test_file = self.repo_path / 'tests' / 'test_logger.py'  # テストファイルパス
            
            with open(test_file, 'r', encoding='utf-8') as f:  # ファイル読み込み
                content = f.read()  # 内容取得
            
            # importを修正
            content = content.replace(
                'from logger import logger',
                'from logger import VCTrackerLogger'
            )
            
            # テストコードを修正（loggerをVCTrackerLoggerに）
            content = re.sub(
                r'test_logger = logger\((.*?)\)',
                r'test_logger = VCTrackerLogger(\1)',
                content
            )
            
            with open(test_file, 'w', encoding='utf-8') as f:  # ファイル書き込み
                f.write(content)  # 修正内容を保存
            
            return True  # 成功
        
        return False  # 失敗
    
    def commit_and_push(self, message: str) -> bool:
        """変更をコミットしてプッシュ"""
        commands = [
            "git add -A",  # 全ファイルをステージング
            f'git commit -m "{message}"',  # コミット
            "git push"  # プッシュ
        ]
        
        for cmd in commands:  # 各コマンドを実行
            result = subprocess.run(cmd, shell=True, cwd=self.repo_path)  # 実行
            if result.returncode != 0:  # 失敗した場合
                return False  # Falseを返す
        
        return True  # 成功
    
    def wait_for_workflow(self, run_id: str, timeout: int = 300) -> str:
        """ワークフローの完了を待つ"""
        start_time = time.time()  # 開始時刻
        
        while time.time() - start_time < timeout:  # タイムアウトまでループ
            cmd = f"gh run view {run_id} --json status"  # ステータス取得
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # 実行
            
            if result.returncode == 0:  # 成功した場合
                data = json.loads(result.stdout)  # JSON解析
                status = data.get('status', '')  # ステータス取得
                
                if status == 'completed':  # 完了した場合
                    cmd = f"gh run view {run_id} --json conclusion"  # 結果取得
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # 実行
                    data = json.loads(result.stdout)  # JSON解析
                    return data.get('conclusion', 'unknown')  # 結果を返す
            
            time.sleep(10)  # 10秒待機
        
        return 'timeout'  # タイムアウト
    
    def run_feedback_loop(self) -> bool:
        """フィードバックループを実行"""
        while self.retry_count < self.max_retries:  # リトライ回数以内
            self.retry_count += 1  # カウント増加
            print(f"\n=== フィードバックループ {self.retry_count}/{self.max_retries} ===")  # 状況表示
            
            # 最新の実行IDを取得
            run_id = self.get_latest_run_id()  # ID取得
            if not run_id:  # IDが取得できない場合
                print("ワークフロー実行が見つかりません")  # エラー表示
                return False  # 失敗
            
            print(f"実行ID: {run_id}")  # ID表示
            
            # ワークフローの完了を待つ
            conclusion = self.wait_for_workflow(run_id)  # 完了待ち
            print(f"結果: {conclusion}")  # 結果表示
            
            if conclusion == 'success':  # 成功した場合
                print("✅ テスト成功！")  # 成功メッセージ
                return True  # 成功を返す
            
            # 失敗したテストを取得
            failures = self.get_failed_tests(run_id)  # 失敗取得
            if not failures:  # 失敗が見つからない場合
                print("失敗情報を取得できませんでした")  # エラー表示
                return False  # 失敗
            
            print(f"失敗したテスト数: {len(failures)}")  # 失敗数表示
            
            # エラーパターンを分析
            solution = self.analyze_error_pattern(failures)  # 分析
            if not solution:  # 解決策が見つからない場合
                print("自動修正可能なパターンが見つかりません")  # エラー表示
                return False  # 失敗
            
            print(f"修正方法: {solution['details']}")  # 修正方法表示
            
            # 修正を適用
            if not self.apply_fix(solution):  # 修正失敗
                print("修正の適用に失敗しました")  # エラー表示
                return False  # 失敗
            
            print("修正を適用しました")  # 成功メッセージ
            
            # コミットしてプッシュ
            commit_msg = f"fix: CI/CDフィードバックによる自動修正 #{self.retry_count}\n\n{solution['details']}"
            if not self.commit_and_push(commit_msg):  # コミット失敗
                print("コミット/プッシュに失敗しました")  # エラー表示
                return False  # 失敗
            
            print("修正をプッシュしました")  # 成功メッセージ
            time.sleep(30)  # 30秒待機（ワークフロー開始待ち）
        
        print(f"最大リトライ回数（{self.max_retries}）に達しました")  # 終了メッセージ
        return False  # 失敗


if __name__ == "__main__":
    # フィードバックループを実行
    feedback = CICDFeedbackLoop(".")  # インスタンス作成
    success = feedback.run_feedback_loop()  # 実行
    sys.exit(0 if success else 1)  # 終了コード設定