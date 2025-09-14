"""Google Drive上のCSVファイルを管理するクライアント"""

import csv
import io
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ロガーの設定
logger = logging.getLogger(__name__)  # このモジュール用のロガー


class DriveCSVClient:
    """Google Drive上のCSVファイルを管理するクラス"""  # クラスの説明

    SCOPES = [  # 必要なGoogle APIスコープ
        'https://www.googleapis.com/auth/drive',  # Google Drive権限
    ]

    def __init__(self, service_account_json: str, folder_name: str = "VC_Tracker_Data"):
        """初期化処理

        Args:
            service_account_json: サービスアカウントJSONファイルパス
            folder_name: Google Drive上のフォルダ名
        """  # 初期化処理の説明
        self.service_account_json = service_account_json  # JSONファイルパスを保存
        self.folder_name = folder_name  # フォルダ名を保存
        self.service = None  # Google Drive APIサービス
        self.folder_id = None  # フォルダID

    def connect(self):
        """Google Drive APIに接続"""  # メソッドの説明
        try:
            # 認証情報を作成
            creds = Credentials.from_service_account_file(  # サービスアカウントから認証情報作成
                self.service_account_json,  # JSONファイルパス
                scopes=self.SCOPES  # 必要なスコープ
            )

            # Google Drive APIサービスを構築
            self.service = build('drive', 'v3', credentials=creds)  # APIサービス作成

            # フォルダを検索または作成
            self._ensure_folder()  # フォルダの存在確認・作成

            logger.info(f"Connected to Google Drive, folder: {self.folder_name}")  # 接続成功をログ出力

        except Exception as e:  # エラー発生時
            logger.error(f"Failed to connect to Google Drive: {e}")  # エラーをログ出力
            raise  # エラーを再発生

    def _ensure_folder(self):
        """フォルダが存在しない場合は作成"""  # メソッドの説明
        # フォルダを検索
        query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"  # 検索クエリ
        results = self.service.files().list(q=query, fields="files(id, name)").execute()  # 検索実行
        items = results.get('files', [])  # 結果を取得

        if items:  # フォルダが見つかった場合
            self.folder_id = items[0]['id']  # フォルダIDを保存
            logger.info(f"Found existing folder: {self.folder_name} (ID: {self.folder_id})")  # 既存フォルダをログ出力
        else:  # フォルダが見つからない場合
            # フォルダを作成
            file_metadata = {  # フォルダのメタデータ
                'name': self.folder_name,  # フォルダ名
                'mimeType': 'application/vnd.google-apps.folder'  # フォルダのMIMEタイプ
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()  # フォルダ作成
            self.folder_id = folder.get('id')  # フォルダIDを保存
            logger.info(f"Created new folder: {self.folder_name} (ID: {self.folder_id})")  # 新規作成をログ出力

    def _get_csv_file_id(self, vc_name: str) -> str:
        """CSVファイルのIDを取得（なければNone）"""  # メソッドの説明
        # ファイル名を作成（VCチャンネル名.csv）
        filename = f"{vc_name.replace('/', '_').replace('\\', '_')}.csv"  # ファイル名作成

        # ファイルを検索
        query = f"name='{filename}' and '{self.folder_id}' in parents and trashed=false"  # 検索クエリ
        results = self.service.files().list(q=query, fields="files(id, name)").execute()  # 検索実行
        items = results.get('files', [])  # 結果を取得

        if items:  # ファイルが見つかった場合
            return items[0]['id']  # ファイルIDを返す
        return None  # 見つからない場合はNone

    def _download_csv(self, file_id: str) -> List[Dict[str, str]]:
        """CSVファイルをダウンロードして内容を返す"""  # メソッドの説明
        request = self.service.files().get_media(fileId=file_id)  # ダウンロードリクエスト作成
        file_content = io.BytesIO()  # メモリ上のファイルオブジェクト
        downloader = MediaIoBaseDownload(file_content, request)  # ダウンローダー作成

        done = False  # ダウンロード完了フラグ
        while not done:  # ダウンロードが完了するまでループ
            status, done = downloader.next_chunk()  # チャンクをダウンロード

        # CSVを読み込み
        file_content.seek(0)  # ファイルポインタを先頭に
        csv_text = file_content.read().decode('utf-8-sig')  # UTF-8でデコード（BOM対応）
        reader = csv.DictReader(io.StringIO(csv_text))  # CSV読み込み
        return list(reader)  # リストとして返す

    def _upload_csv(self, vc_name: str, data: List[Dict[str, str]], file_id: str = None):
        """CSVファイルをアップロード（新規または更新）"""  # メソッドの説明
        # ファイル名を作成
        filename = f"{vc_name.replace('/', '_').replace('\\', '_')}.csv"  # ファイル名作成

        # CSVデータを作成
        output = io.StringIO()  # メモリ上の文字列ストリーム
        if data:  # データがある場合
            fieldnames = ['datetime_jst', 'user_id', 'user_name', 'present']  # CSVのヘッダー
            writer = csv.DictWriter(output, fieldnames=fieldnames)  # CSV書き込みオブジェクト
            writer.writeheader()  # ヘッダー書き込み
            writer.writerows(data)  # データ書き込み

        # 一時ファイルに保存
        temp_filename = f"/tmp/{filename}"  # 一時ファイルパス
        with open(temp_filename, 'w', encoding='utf-8-sig') as f:  # UTF-8 BOM付きで保存
            f.write(output.getvalue())  # CSVデータを書き込み

        # メディアオブジェクトを作成
        media = MediaFileUpload(temp_filename, mimetype='text/csv')  # アップロード用メディア作成

        if file_id:  # 既存ファイルを更新
            self.service.files().update(  # ファイル更新
                fileId=file_id,
                media_body=media
            ).execute()
            logger.info(f"Updated CSV file: {filename}")  # 更新完了をログ出力
        else:  # 新規ファイルを作成
            file_metadata = {  # ファイルのメタデータ
                'name': filename,  # ファイル名
                'parents': [self.folder_id]  # 親フォルダ
            }
            self.service.files().create(  # ファイル作成
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            logger.info(f"Created new CSV file: {filename}")  # 作成完了をログ出力

        # 一時ファイルを削除
        os.remove(temp_filename)  # 一時ファイル削除

    def upsert_presence(self, members: List[Dict[str, Any]]) -> Dict[str, int]:
        """メンバーの出席情報を記録（Upsert）

        Args:
            members: メンバー情報のリスト

        Returns:
            処理結果（新規追加数、更新数）
        """  # メソッドの説明
        if not self.service:  # APIサービスが未接続の場合
            raise RuntimeError("Not connected to Google Drive")  # エラーを発生

        # JSTの今日の日付と時刻を取得
        jst = timezone(timedelta(hours=9))  # JST（UTC+9）のタイムゾーン
        now_jst = datetime.now(jst)  # 現在のJST日時
        today_jst = now_jst.strftime('%Y/%-m/%-d')  # 今日の日付（YYYY/M/D形式）
        datetime_jst = now_jst.strftime('%Y/%-m/%-d %H:%M')  # 日付と時刻（YYYY/M/D HH:MM形式）

        # VC名でグループ化
        vc_groups = {}  # VC名ごとにメンバーを分類
        for member in members:  # メンバーリストをループ
            vc_name = member.get('vc_name', 'unknown')  # VC名を取得
            if vc_name not in vc_groups:  # まだリストがない場合
                vc_groups[vc_name] = []  # 新しいリストを作成
            vc_groups[vc_name].append(member)  # メンバーを追加

        total_new_count = 0  # 全体の新規追加カウンタ
        total_update_count = 0  # 全体の更新カウンタ

        # VC名ごとにCSVファイルを作成・更新
        for vc_name, vc_members in vc_groups.items():  # VC名ごとにループ
            # 既存のCSVファイルを取得
            file_id = self._get_csv_file_id(vc_name)  # ファイルID取得

            if file_id:  # ファイルが存在する場合
                # 既存データをダウンロード
                existing_data = self._download_csv(file_id)  # CSVダウンロード
            else:  # ファイルが存在しない場合
                existing_data = []  # 空のリスト

            # 今日のデータを抽出
            today_data = {  # 今日のデータを辞書形式で保存
                row['user_id']: row  # user_idをキーとする
                for row in existing_data  # 既存データをループ
                if row.get('datetime_jst', '').startswith(today_jst)  # 今日の日付のデータを抽出

            new_count = 0  # 新規追加カウンタ
            update_count = 0  # 更新カウンタ

            # メンバーごとに処理
            for member in vc_members:  # VCメンバーリストをループ
                user_id = member['user_id']  # ユーザーID

                if user_id not in today_data:  # 今日のデータに存在しない場合
                    # 新規追加
                    new_row = {  # 新しい行データ
                        'datetime_jst': datetime_jst,  # 日付と時刻
                        'user_id': member['user_id'],  # ユーザーID
                        'user_name': member['user_name'],  # ユーザー名
                        'present': 'TRUE'  # 出席フラグ
                    }
                    existing_data.append(new_row)  # データに追加
                    new_count += 1  # カウンタ増加
                    logger.info(f"New presence in {vc_name}: {member['user_name']} on {datetime_jst}")  # 新規追加をログ出力
                else:
                    # 既にTRUEの場合は更新不要
                    if today_data[user_id].get('present') != 'TRUE':  # まだTRUEでない場合
                        # データを更新
                        for row in existing_data:  # 全データをループ
                            if row['user_id'] == user_id and row.get('datetime_jst', '').startswith(today_jst):  # 該当行を発見
                                row['present'] = 'TRUE'  # 出席フラグを更新
                                update_count += 1  # カウンタ増加
                                logger.info(f"Updated presence in {vc_name}: {member['user_name']} on {row['datetime_jst']}")  # 更新をログ出力
                                break  # ループを抜ける

            # CSVファイルをアップロード
            self._upload_csv(vc_name, existing_data, file_id)  # CSV更新

            total_new_count += new_count  # 全体のカウンタを更新
            total_update_count += update_count  # 全体のカウンタを更新

            if new_count > 0 or update_count > 0:  # 変更があった場合
                logger.info(f"Updated {vc_name}.csv: {new_count} new, {update_count} updated")  # 更新サマリをログ出力

        return {"new": total_new_count, "updated": total_update_count}  # 処理結果を返す