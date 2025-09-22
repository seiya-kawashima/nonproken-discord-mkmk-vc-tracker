#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日本の祝日判定スクリプト

このスクリプトは、指定された日付が日本の祝日かどうかを判定します。
GitHub Actionsや定期実行タスクで使用し、祝日の場合は処理をスキップするために使用します。
"""

import sys  # システム関連操作用
import json  # JSON処理用
from datetime import datetime, date  # 日付処理用
import argparse  # コマンドライン引数処理用

# 日本の祝日判定ライブラリ
try:
    import jpholiday  # 日本の祝日判定ライブラリ
except ImportError:
    print("jpholidayがインストールされていません。以下のコマンドでインストールしてください:")  # エラーメッセージ
    print("pip install jpholiday")  # インストールコマンド
    sys.exit(1)  # 異常終了

# タイムゾーン処理
try:
    import pytz  # タイムゾーン処理用
except ImportError:
    print("pytzがインストールされていません。以下のコマンドでインストールしてください:")  # エラーメッセージ
    print("pip install pytz")  # インストールコマンド
    sys.exit(1)  # 異常終了


def check_holiday(target_date: date = None) -> dict:
    """
    指定された日付が日本の祝日かどうかをチェック

    Args:
        target_date: チェック対象の日付（Noneの場合は今日）

    Returns:
        dict: 祝日情報を含む辞書
            - is_holiday: 祝日かどうか（bool）
            - holiday_name: 祝日名（祝日の場合のみ）
            - date: チェック対象の日付（文字列）
            - day_of_week: 曜日（月、火、水...）
    """
    # 対象日付の設定（指定がなければJSTの今日）
    if target_date is None:  # 日付が指定されていない場合
        jst = pytz.timezone('Asia/Tokyo')  # JSTタイムゾーン
        target_date = datetime.now(jst).date()  # 今日の日付（JST）

    # 祝日チェック
    is_holiday = jpholiday.is_holiday(target_date)  # 祝日かどうか判定
    holiday_name = jpholiday.is_holiday_name(target_date)  # 祝日名を取得

    # 曜日を取得（0:月曜、6:日曜）
    weekday = target_date.weekday()  # 曜日番号を取得
    weekday_names = ['月', '火', '水', '木', '金', '土', '日']  # 曜日名リスト
    day_of_week = weekday_names[weekday]  # 曜日名を取得

    # 土日判定
    is_weekend = weekday >= 5  # 土曜（5）または日曜（6）

    # 結果を辞書形式でまとめる
    result = {
        'date': target_date.strftime('%Y-%m-%d'),  # 日付（YYYY-MM-DD形式）
        'day_of_week': day_of_week,  # 曜日
        'is_holiday': is_holiday,  # 祝日かどうか
        'is_weekend': is_weekend,  # 週末かどうか
        'is_workday': not (is_holiday or is_weekend),  # 平日（祝日でも週末でもない）
        'holiday_name': holiday_name if is_holiday else None  # 祝日名（祝日の場合のみ）
    }

    return result  # 結果を返す


def main():
    """メイン処理"""
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(  # 引数パーサー作成
        description='日本の祝日判定'  # スクリプトの説明
    )
    parser.add_argument(  # 日付引数追加
        '--date',  # オプション名
        type=str,  # 文字列型
        help='チェックする日付（YYYY-MM-DD形式）。省略時は今日'  # ヘルプメッセージ
    )
    parser.add_argument(  # JSON出力オプション
        '--json',  # オプション名
        action='store_true',  # フラグとして扱う
        help='結果をJSON形式で出力'  # ヘルプメッセージ
    )
    parser.add_argument(  # GitHub Actions出力オプション
        '--github-output',  # オプション名
        action='store_true',  # フラグとして扱う
        help='GitHub Actions用の出力形式'  # ヘルプメッセージ
    )

    args = parser.parse_args()  # 引数をパース

    # 対象日付の設定
    target_date = None  # デフォルトはNone（今日）
    if args.date:  # 日付が指定された場合
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()  # 文字列を日付に変換
        except ValueError:  # 変換エラー時
            print(f"エラー: 日付形式が正しくありません: {args.date}")  # エラーメッセージ
            print("正しい形式: YYYY-MM-DD（例: 2025-01-01）")  # 正しい形式の説明
            sys.exit(1)  # 異常終了

    # 祝日チェック実行
    result = check_holiday(target_date)  # 祝日情報を取得

    # 結果の出力
    if args.json:  # JSON形式で出力
        print(json.dumps(result, ensure_ascii=False, indent=2))  # JSON出力（日本語対応）
    elif args.github_output:  # GitHub Actions形式で出力
        print(f"::set-output name=is_holiday::{str(result['is_holiday']).lower()}")  # 祝日フラグ
        print(f"::set-output name=is_workday::{str(result['is_workday']).lower()}")  # 平日フラグ
        if result['holiday_name']:  # 祝日名がある場合
            print(f"::set-output name=holiday_name::{result['holiday_name']}")  # 祝日名
    else:  # 通常の出力
        print(f"日付: {result['date']}（{result['day_of_week']}曜日）")  # 日付と曜日
        if result['is_holiday']:  # 祝日の場合
            print(f"祝日: {result['holiday_name']}")  # 祝日名を表示
        elif result['is_weekend']:  # 週末の場合
            print("週末です")  # 週末メッセージ
        else:  # 平日の場合
            print("平日です（祝日ではありません）")  # 平日メッセージ

    # 終了コードの設定（平日なら0、祝日・週末なら1）
    sys.exit(0 if result['is_workday'] else 1)  # 平日なら正常終了、それ以外は異常終了


if __name__ == "__main__":  # スクリプト直接実行時
    main()  # メイン処理を実行