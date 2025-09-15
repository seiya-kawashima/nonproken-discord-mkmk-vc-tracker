"""Google Sheetsクライアント - 出席データの記録と管理"""  # モジュールの説明

import os  # ファイルパス操作用
import json  # JSON形式の処理用
from datetime import datetime, timezone, timedelta  # 日時処理用
from typing import List, Dict, Any, Optional  # 型ヒント用
import gspread  # Google Sheets API用
from google.oauth2.service_account import Credentials  # 認証用
from loguru import logger  # ログ出力用（loguru）


class SheetsClient:
    """Google Sheetsへのデータ記録を管理するクラス"""  # クラスの説明

    SCOPES = [  # 必要なGoogle APIスコープ
        'https://www.googleapis.com/auth/spreadsheets',  # スプレッドシート読み書き権限
        'https://www.googleapis.com/auth/drive',  # Google Drive権限（ファイル検索に必要）
    ]

    def __init__(self, service_account_json: str, sheet_name: str):
        """初期化処理

        Args:
            service_account_json: サービスアカウントJSONファイルパス
            sheet_name: スプレッドシート名
        """  # 初期化処理の説明
        self.service_account_json = service_account_json  # JSONファイルパスを保存
        self.sheet_name = sheet_name  # シート名を保存
        self.client = None  # Google Sheetsクライアント
        self.sheet = None  # アクティブなシート
        self.worksheet = None  # アクティブなワークシート

    def connect(self):
        """Google Sheetsに接続"""  # メソッドの説明
        try:
            # 認証情報を読み込み
            creds = Credentials.from_service_account_file(  # サービスアカウント認証
                self.service_account_json,  # JSONファイルパス
                scopes=self.SCOPES  # 必要なスコープ
            )
            
            # gspreadクライアントを作成
            self.client = gspread.authorize(creds)  # 認証済みクライアント作成
            
            # スプレッドシートを開く
            self.sheet = self.client.open(self.sheet_name)  # シート名で開く
            
            # デフォルトワークシートは作成しない（VC名ごとに作成するため）
            self.worksheet = None  # ワークシートは使用しない
            
            logger.info(f"Connected to Google Sheets: {self.sheet_name}")  # 接続成功をログ出力
            
        except Exception as e:  # エラー発生時
            logger.error(f"Failed to connect to Google Sheets: {e}")  # エラーをログ出力
            raise  # エラーを再発生

    def upsert_presence(self, members: List[Dict[str, Any]]) -> Dict[str, int]:
        """メンバーの出席情報を記録（Upsert）

        Args:
            members: メンバー情報のリスト

        Returns:
            処理結果（新規追加数、更新数）
        """  # メソッドの説明
        if not self.sheet:  # スプレッドシートが未接続の場合
            raise RuntimeError("Not connected to Google Sheets")  # エラーを発生

        # JSTの今日の日付を取得
        jst = timezone(timedelta(hours=9))  # JST（UTC+9）のタイムゾーン
        today_jst = datetime.now(jst).strftime('%Y/%-m/%-d')  # 今日の日付（YYYY/M/D形式）

        # VC名でグループ化
        vc_groups = {}  # VC名ごとにメンバーを分類
        for member in members:  # メンバーリストをループ
            vc_name = member.get('vc_name', 'unknown')  # VC名を取得
            if vc_name not in vc_groups:  # まだリストがない場合
                vc_groups[vc_name] = []  # 新しいリストを作成
            vc_groups[vc_name].append(member)  # メンバーを追加

        total_new_count = 0  # 全体の新規追加カウンタ
        total_update_count = 0  # 全体の更新カウンタ

        # VC名ごとにワークシートを作成・更新
        for vc_name, vc_members in vc_groups.items():  # VC名ごとにループ
            # ワークシート名を作成（シート名に使えない文字を置換）
            sheet_name = vc_name.replace('/', '_').replace('\\', '_')  # スラッシュとバックスラッシュを置換

            # ワークシートを取得または作成
            try:
                worksheet = self.sheet.worksheet(sheet_name)  # 既存のワークシートを取得
            except gspread.WorksheetNotFound:  # ワークシートが存在しない場合
                worksheet = self.sheet.add_worksheet(  # 新規作成
                    title=sheet_name,  # シート名
                    rows=1000,  # 初期行数
                    cols=4  # 初期列数（A-D）
                )
                # ヘッダー行を設定
                headers = ['date_jst', 'user_id', 'user_name', 'present']  # ヘッダー定義（guild_id削除）
                worksheet.update('A1:D1', [headers])  # ヘッダーを書き込み
                logger.info(f"Created worksheet: {sheet_name}")  # 作成完了をログ出力

            # 既存データを取得
            all_values = worksheet.get_all_records()  # 全レコードを取得

            # 今日のデータを抽出
            today_data = {  # 今日のデータを辞書形式で保存
                row['user_id']: row  # user_idをキーとする
                for row in all_values  # 全レコードをループ
                if row.get('date_jst') == today_jst  # 今日の日付のみ抽出
            }

            new_count = 0  # 新規追加カウンタ
            update_count = 0  # 更新カウンタ
            rows_to_append = []  # 追加する行のリスト

            for member in vc_members:  # VCメンバーリストをループ
                user_id = member['user_id']  # ユーザーID

                if user_id not in today_data:  # 今日のデータに存在しない場合
                    # 新規追加
                    row = [  # 新しい行データ
                        today_jst,  # 日付
                        member['user_id'],  # ユーザーID
                        member['user_name'],  # ユーザー名
                        'TRUE'  # 出席フラグ
                    ]
                    rows_to_append.append(row)  # 追加リストに追加
                    new_count += 1  # カウンタ増加
                    logger.info(f"New presence in {vc_name}: {member['user_name']} on {today_jst}")  # 新規追加をログ出力
                else:
                    # 既にTRUEの場合は更新不要
                        # 該当行を探して更新（本来はより効率的な方法を使うべき）
                        update_count += 1  # カウンタ増加
                        logger.info(f"Would update presence in {vc_name}: {member['user_name']} on {today_jst}")  # 更新をログ出力

            # 新規データを一括追加
            if rows_to_append:  # 追加データがある場合
                worksheet.append_rows(rows_to_append)  # 一括追加
                logger.info(f"Added {new_count} new presence records to {vc_name}")  # 追加完了をログ出力

            total_new_count += new_count  # 全体のカウンタを更新
            total_update_count += update_count  # 全体のカウンタを更新

        return {"new": total_new_count, "updated": total_update_count}  # 処理結果を返す

    def get_total_days(self, user_id: str) -> int:
        """ユーザーの通算ログイン日数を取得

        Args:
            user_id: ユーザーID

        Returns:
            通算ログイン日数
        """  # メソッドの説明
        if not self.worksheet:  # ワークシートが未接続の場合
            raise RuntimeError("Not connected to Google Sheets")  # エラーを発生

        # 全データを取得
        all_values = self.worksheet.get_all_records()  # 全レコードを取得
        
        # 指定ユーザーのTRUEレコードをカウント
        total_days = sum(  # 合計を計算
            1 for row in all_values  # 全レコードをループ
            if row.get('user_id') == user_id  # ユーザーIDが一致
            and row.get('present') == 'TRUE'  # 出席フラグがTRUE
        )
        
        return total_days  # 通算日数を返す

    def get_today_members(self) -> List[Dict[str, Any]]:
        """今日ログインしたメンバーのリストを取得

        Returns:
            今日のメンバー情報リスト
        """  # メソッドの説明
        if not self.worksheet:  # ワークシートが未接続の場合
            raise RuntimeError("Not connected to Google Sheets")  # エラーを発生

        # JSTの今日の日付を取得
        jst = timezone(timedelta(hours=9))  # JST（UTC+9）のタイムゾーン
        today_jst = datetime.now(jst).strftime('%Y/%-m/%-d')  # 今日の日付（YYYY/M/D形式）
        
        # 全データを取得
        all_values = self.worksheet.get_all_records()  # 全レコードを取得
        
        # 今日のメンバーを抽出
        today_members = [  # リスト内包表記で抽出
            row for row in all_values  # 全レコードをループ
            if row.get('date_jst') == today_jst  # 今日の日付
            and row.get('present') == 'TRUE'  # 出席フラグがTRUE
        ]
        
        return today_members  # 今日のメンバーリストを返す