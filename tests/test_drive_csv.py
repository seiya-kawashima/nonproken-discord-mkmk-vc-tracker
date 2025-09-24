#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive CSVファイルテストツール
Google Drive上のCSVファイルを読み込み、ユーザーごとのレコード数を集計する
データ整合性確認用のテストスクリプト
"""

from slack_notifier_attendance import DailyAggregator  # 日次集計クラスをインポート
import datetime  # 日付処理用

# 集約クラスのインスタンスを作成
aggregator = DailyAggregator(env=1, target_date=datetime.date(2025, 9, 22))  # テスト環境で2025年9月22日のデータを集計

# CSVファイルを取得
csv_files = aggregator.get_csv_files_from_drive()  # Google DriveからCSVファイル一覧を取得
print(f"Google DriveのCSVファイル数: {len(csv_files)}")  # ファイル数を表示

for csv_file in csv_files:  # 各CSVファイルを処理
    print(f"\nファイル名: {csv_file['name']}")  # ファイル名を表示

    # CSVファイルの内容を読み込み
    records = aggregator.read_csv_content(csv_file['id'], csv_file['name'])  # CSVデータを読み込み
    print(f"  読み込んだレコード数: {len(records)}")  # レコード数を表示

    # ユーザーごとに集計
    user_counts = {}  # ユーザー別カウントを格納する辞書
    for record in records:  # 各レコードを処理
        user_name = record.get('user_name', 'Unknown')  # ユーザー名を取得（デフォルト：Unknown）
        display_name = record.get('display_name', '')  # 表示名を取得（デフォルト：空文字）
        key = f"{user_name} ({display_name})"  # キーを作成（ユーザー名と表示名の組み合わせ）
        user_counts[key] = user_counts.get(key, 0) + 1  # カウントをインクリメント

    print(f"  ユニークユーザー数: {len(user_counts)}")  # ユニークユーザー数を表示
    print("  ユーザー別レコード数:")  # 見出し表示
    for user, count in sorted(user_counts.items()):  # ユーザー名でソートして表示
        print(f"    - {user}: {count}件")  # 各ユーザーのレコード数を表示