#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Drive CSVファイル確認ツール
Google Drive上のCSVファイルの内容を確認し、特定の日付のデータを検索・表示する
デバッグや動作確認用のユーティリティスクリプト
"""

from slack_notifier_attendance import DailyAggregator  # 日次集計クラスをインポート
import datetime  # 日付処理用
import io  # バイナリストリーム処理用
from googleapiclient.http import MediaIoBaseDownload  # Googleドライブファイルダウンロード用

# 集約クラスのインスタンスを作成
aggregator = DailyAggregator(env=1, target_date=datetime.date(2025, 9, 22))  # テスト環境で2025年9月22日のデータを確認

# CSVファイルを取得
csv_files = aggregator.get_csv_files_from_drive()  # Google DriveからCSVファイル一覧を取得

for csv_file in csv_files:  # 各CSVファイルを処理
    print(f"ファイル名: {csv_file['name']}")  # ファイル名を表示

    # ファイルをダウンロード
    request = aggregator.drive_service.files().get_media(fileId=csv_file['id'])  # ダウンロード用リクエストを作成
    file_content = io.BytesIO()  # メモリ上のバイナリストリームを作成
    downloader = MediaIoBaseDownload(file_content, request)  # ダウンローダーを作成

    done = False  # ダウンロード完了フラグ
    while not done:  # ダウンロードが完了するまでループ
        status, done = downloader.next_chunk()  # チャンク単位でダウンロード

    # CSVをパース（BOMを除去）
    file_content.seek(0)  # ファイルポインタを先頭に移動
    csv_text = file_content.read().decode('utf-8-sig')  # UTF-8でデコード（BOM付きに対応）

    lines = csv_text.strip().split('\n')  # 改行で分割してリスト化
    print(f"  総行数: {len(lines)}")  # 総行数を表示

    # 最後の5行を表示
    print("  最後の5行:")  # 見出し表示
    for line in lines[-5:]:  # 最後の5行をループ
        print(f"    {line}")  # 各行を表示

    # 2025/9/22のデータを全て検索
    target_records = []  # 該当レコードを格納するリスト
    for line in lines[1:]:  # ヘッダーをスキップしてループ
        if line.startswith("2025/9/22"):  # 対象日付で始まる行を検索
            target_records.append(line)  # リストに追加

    print(f"\n  2025/9/22のレコード数: {len(target_records)}")  # 該当レコード数を表示
    if target_records:  # レコードが存在する場合
        print("  最初の5件:")  # 見出し表示
        for i, record in enumerate(target_records[:5]):  # 最初の5件をループ
            print(f"    {i+1}. {record}")  # 番号付きで表示
        if len(target_records) > 5:  # 5件より多い場合
            print("  最後の3件:")  # 見出し表示
            for i, record in enumerate(target_records[-3:], len(target_records)-2):  # 最後の3件をループ
                print(f"    {i}. {record}")  # 番号付きで表示