"""Google Drive上のCSVファイルを管理するクライアント

このモジュールはDiscord VCチャンネルの参加者情報をGoogle Drive上のCSVファイルに
記録・管理するための機能を提供します。

主な機能:
- Google Drive APIを使用したCSVファイルの読み書き
- VCチャンネルごとに独立したCSVファイルで管理
- 日付と時刻付きで参加者の出席記録を保存
- 自動的なフォルダ作成とファイル管理
"""

import csv
import io
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from loguru import logger  # ログ出力用（loguru）
import sys  # システム操作用
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # 親ディレクトリをパスに追加
from config import EnvConfig  # 環境設定


class DriveCSVClient:
    """Google Drive上のCSVファイルを管理するクラス

    Google Drive APIを使用してVCチャンネルごとの参加者データを
    CSVファイルとして管理します。各VCチャンネルは独立したCSVファイルに
    保存され、参加者の出席記録が日時付きで記録されます。
    """  # クラスの説明

    SCOPES = [  # 必要なGoogle APIスコープ
        'https://www.googleapis.com/auth/drive',  # Google Drive権限
    ]

    def __init__(self, service_account_json: str, base_folder_path: str = "discord_mokumoku_tracker/csv", env_name: str = "PRD", shared_drive_id: str = None):
        """初期化処理

        Args:
            service_account_json: サービスアカウントJSONファイルパス
            base_folder_path: Google Drive上のベースフォルダパス
                             例: "discord_mokumoku_tracker/csv"
            env_name: 環境名（PRD/TST/DEV）
            shared_drive_id: 共有ドライブID（オプション）
        """  # 初期化処理の説明
        self.service_account_json = service_account_json  # JSONファイルパスを保存
        self.base_folder_path = base_folder_path  # ベースフォルダパスを保存
        self.env_name = env_name  # 環境名を保存（ファイル名に使用）
        self.shared_drive_id = shared_drive_id  # 共有ドライブIDを保存
        self.service = None  # Google Drive APIサービス
        self.vc_folder_ids = {}  # VCチャンネル名ごとのフォルダIDを保存

    def connect(self):
        """Google Drive APIに接続

        サービスアカウントの認証情報を使用してGoogle Drive APIに接続し、
        データ保存用のフォルダを準備します。フォルダが存在しない場合は
        自動的に作成されます。
        """  # メソッドの説明
        try:
            # 認証情報を作成
            creds = Credentials.from_service_account_file(  # サービスアカウントから認証情報作成
                self.service_account_json,  # JSONファイルパス
                scopes=self.SCOPES  # 必要なスコープ
            )

            # Google Drive APIサービスを構築
            self.service = build('drive', 'v3', credentials=creds)  # APIサービス作成

            # ベースフォルダの存在確認・作成
            self._ensure_base_folder()  # ベースフォルダの存在確認・作成

            # 共有ドライブ情報をログに含める
            drive_info = f"Shared Drive ID: {self.shared_drive_id}" if self.shared_drive_id else "My Drive"  # ドライブ情報
            logger.info(f"Google Driveに接続しました ({drive_info}), フォルダ: {self.base_folder_path}")  # 接続成功をログ出力

        except Exception as e:  # エラー発生時
            logger.error(f"Google Driveへの接続に失敗しました: {e}")  # エラーをログ出力
            raise  # エラーを再発生

    def _ensure_base_folder(self):
        """ベースフォルダ階層が存在しない場合は作成

        Google Drive上にベースフォルダ階層を作成します。
        例: "discord_mokumoku_tracker/csv" の場合、
        discord_mokumoku_tracker → csv の順に作成・確認します。
        """  # メソッドの説明
        # フォルダパスを分割
        folder_names = self.base_folder_path.split('/')  # スラッシュで分割
        parent_id = self.shared_drive_id if self.shared_drive_id else None  # 親フォルダID（共有ドライブIDまたはルート）

        # 各階層のフォルダを順番に作成・確認
        for i, folder_name in enumerate(folder_names):  # 各フォルダ名について
            # 現在の階層でフォルダを検索
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"  # 検索クエリ

            # 共有ドライブの場合、最初のフォルダは共有ドライブ直下、それ以降は親フォルダ指定
            if self.shared_drive_id:
                if i == 0:  # 最初のフォルダ
                    query += f" and '{self.shared_drive_id}' in parents"  # 共有ドライブ直下
                elif parent_id:  # 2番目以降のフォルダ
                    query += f" and '{parent_id}' in parents"  # 親フォルダ内で検索
            elif parent_id:  # マイドライブの場合
                query += f" and '{parent_id}' in parents"  # 親フォルダ内で検索

            list_params = {  # 検索パラメータ
                'q': query,  # 検索クエリ
                'fields': 'files(id, name)',  # 取得するフィールド
                'supportsAllDrives': True,  # 全ドライブ対応
                'includeItemsFromAllDrives': True  # 全ドライブから検索
            }

            # 共有ドライブが指定されている場合は、そのドライブ内で検索
            if self.shared_drive_id:  # 共有ドライブIDが設定されている場合
                list_params['driveId'] = self.shared_drive_id  # 共有ドライブID
                list_params['corpora'] = 'drive'  # 特定のドライブを検索
            else:  # 共有ドライブが指定されていない場合
                list_params['corpora'] = 'allDrives'  # すべてのドライブから検索
            results = self.service.files().list(**list_params).execute()  # 検索実行
            items = results.get('files', [])  # 結果を取得

            if items:  # フォルダが見つかった場合
                folder_id = items[0]['id']  # フォルダIDを取得
                logger.debug(f"Found existing folder: {folder_name} (ID: {folder_id})")  # 既存フォルダをログ出力
            else:  # フォルダが見つからない場合
                # フォルダを作成
                file_metadata = {  # フォルダのメタデータ
                    'name': folder_name,  # フォルダ名
                    'mimeType': 'application/vnd.google-apps.folder'  # フォルダのMIMEタイプ
                }

                # 親フォルダを設定（共有ドライブの最初のフォルダは共有ドライブIDを親に）
                if self.shared_drive_id and i == 0:  # 共有ドライブの最初のフォルダ
                    file_metadata['parents'] = [self.shared_drive_id]  # 共有ドライブを親に設定
                elif parent_id:  # それ以外で親フォルダがある場合
                    file_metadata['parents'] = [parent_id]  # 親フォルダを設定

                create_params = {  # 作成パラメータ
                    'body': file_metadata,  # フォルダメタデータ
                    'fields': 'id',  # 取得するフィールド
                    'supportsAllDrives': True  # 全ドライブ対応
                }
                folder = self.service.files().create(**create_params).execute()  # フォルダ作成
                folder_id = folder.get('id')  # フォルダIDを取得
                logger.info(f"Created new folder: {folder_name} (ID: {folder_id})")  # 新規作成をログ出力

            parent_id = folder_id  # 次の階層の親フォルダとして設定

        # ベースフォルダIDを保存
        self.base_folder_id = parent_id  # ベースフォルダIDを保存
        # 共有ドライブ情報を含めた完全なパス情報をログ出力
        drive_info = f"Shared Drive ID: {self.shared_drive_id}" if self.shared_drive_id else "My Drive"  # ドライブ情報
        logger.info(f"ベースフォルダの準備完了: {self.base_folder_path} (ID: {self.base_folder_id}, {drive_info})")  # 階層準備完了をログ出力

    def _ensure_vc_folder(self, vc_name: str) -> str:
        """VCチャンネル用のフォルダを作成・取得

        discord_mokumoku_tracker/csv/{VC名}/ のフォルダを作成します。
        既に存在する場合はそのIDを返します。

        Args:
            vc_name: VCチャンネル名

        Returns:
            VCチャンネルフォルダのID
        """  # メソッドの説明
        # VCチャンネル名をフォルダ名として使用（スラッシュはアンダースコアに置換）
        folder_name = vc_name.replace('/', '_').replace('\\', '_')  # フォルダ名作成

        # キャッシュから取得
        if folder_name in self.vc_folder_ids:  # 既にキャッシュにある場合
            return self.vc_folder_ids[folder_name]  # キャッシュから返す

        # フォルダを検索
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{self.base_folder_id}' in parents and trashed=false"  # 検索クエリ
        list_params = {  # 検索パラメータ
            'q': query,  # 検索クエリ
            'fields': 'files(id, name)',  # 取得するフィールド
            'supportsAllDrives': True  # 全ドライブ対応
        }

        # 共有ドライブが指定されている場合は、そのドライブ内で検索
        if self.shared_drive_id:  # 共有ドライブIDが設定されている場合
            list_params['includeItemsFromAllDrives'] = True  # 全ドライブから検索
            list_params['driveId'] = self.shared_drive_id  # 共有ドライブID
            list_params['corpora'] = 'drive'  # 特定のドライブを検索

        results = self.service.files().list(**list_params).execute()  # 検索実行
        items = results.get('files', [])  # 結果を取得

        if items:  # フォルダが見つかった場合
            folder_id = items[0]['id']  # フォルダIDを取得
            logger.debug(f"Found existing VC folder: {folder_name} (ID: {folder_id})")  # 既存フォルダをログ出力
        else:  # フォルダが見つからない場合
            # フォルダを作成
            file_metadata = {  # フォルダのメタデータ
                'name': folder_name,  # フォルダ名
                'mimeType': 'application/vnd.google-apps.folder',  # フォルダのMIMEタイプ
                'parents': [self.base_folder_id]  # 親フォルダ
            }
            create_params = {  # 作成パラメータ
                'body': file_metadata,  # フォルダメタデータ
                'fields': 'id',  # 取得するフィールド
                'supportsAllDrives': True  # 全ドライブ対応
            }
            folder = self.service.files().create(**create_params).execute()  # フォルダ作成
            folder_id = folder.get('id')  # フォルダIDを取得
            # フルパスを含めてログ出力
            full_path = f"{self.base_folder_path}/{folder_name}"  # フルパス
            logger.info(f"VC用フォルダを新規作成: {full_path} (ID: {folder_id})")  # 新規作成をログ出力

        # キャッシュに保存
        self.vc_folder_ids[folder_name] = folder_id  # キャッシュに保存
        return folder_id  # フォルダIDを返す

    def _get_csv_file_id(self, vc_name: str) -> str:
        """CSVファイルのIDを取得（なければNone）

        discord_mokumoku_tracker/csv/{VC名}/{環境}.csv のファイルを検索します。
        ファイル名は環境名.csv（例: PRD.csv, TST.csv, DEV.csv）となります。
        """  # メソッドの説明
        # VCチャンネル用のフォルダIDを取得
        vc_folder_id = self._ensure_vc_folder(vc_name)  # VCフォルダを作成・取得

        # 環境番号をconfig.pyから取得
        env_number = EnvConfig.get_env_number(self.env_name)  # 環境番号を取得

        # ファイル名を作成（番号_環境名.csv）
        filename = f"{env_number}_{self.env_name}.csv"  # ファイル名作成（例: 0_PRD.csv）

        # ファイルを検索
        query = f"name='{filename}' and '{vc_folder_id}' in parents and trashed=false"  # 検索クエリ
        list_params = {  # 検索パラメータ
            'q': query,  # 検索クエリ
            'fields': 'files(id, name)',  # 取得するフィールド
            'supportsAllDrives': True,  # 全ドライブ対応
            'includeItemsFromAllDrives': True  # 全ドライブから検索
        }

        # 共有ドライブが指定されている場合は、そのドライブ内で検索
        if self.shared_drive_id:  # 共有ドライブIDが設定されている場合
            list_params['driveId'] = self.shared_drive_id  # 共有ドライブID
            list_params['corpora'] = 'drive'  # 特定のドライブを検索

        results = self.service.files().list(**list_params).execute()  # 検索実行
        items = results.get('files', [])  # 結果を取得

        if items:  # ファイルが見つかった場合
            return items[0]['id']  # ファイルIDを返す
        return None  # 見つからない場合はNone

    def _download_csv(self, file_id: str) -> List[Dict[str, str]]:
        """CSVファイルをダウンロードして内容を返す

        Google DriveからCSVファイルをダウンロードし、パースして
        辞書形式のリストとして返します。UTF-8 BOM付きファイルにも対応し、
        メモリ上で処理するため一時ファイルは作成しません。
        """  # メソッドの説明
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
        """CSVファイルをアップロード（新規または更新）

        discord_mokumoku_tracker/csv/{VC名}/{環境}.csv にファイルを保存します。
        file_idが指定されている場合は既存ファイルを更新し、
        指定されていない場合は新規ファイルを作成します。
        CSVファイルはUTF-8 BOM付きで保存され、Excelでも正しく開けます。
        """  # メソッドの説明
        # VCチャンネル用のフォルダIDを取得
        vc_folder_id = self._ensure_vc_folder(vc_name)  # VCフォルダを作成・取得

        # 環境番号をconfig.pyから取得
        env_number = EnvConfig.get_env_number(self.env_name)  # 環境番号を取得

        # ファイル名を作成（番号_環境名.csv）
        filename = f"{env_number}_{self.env_name}.csv"  # ファイル名作成（例: 0_PRD.csv）

        # CSVデータを作成
        output = io.StringIO()  # メモリ上の文字列ストリーム
        if data:  # データがある場合
            fieldnames = ['datetime_jst', 'user_id', 'user_name']  # CSVのヘッダー（present列削除）
            writer = csv.DictWriter(output, fieldnames=fieldnames)  # CSV書き込みオブジェクト
            writer.writeheader()  # ヘッダー書き込み
            writer.writerows(data)  # データ書き込み

        # 一時ファイルに保存
        import tempfile  # 一時ファイル用
        temp_dir = tempfile.gettempdir()  # OSに応じた一時ディレクトリを取得
        temp_filename = os.path.join(temp_dir, filename)  # 一時ファイルパス
        with open(temp_filename, 'w', encoding='utf-8-sig') as f:  # UTF-8 BOM付きで保存
            f.write(output.getvalue())  # CSVデータを書き込み

        # メディアオブジェクトを作成
        media = MediaFileUpload(temp_filename, mimetype='text/csv')  # アップロード用メディア作成

        if file_id:  # 既存ファイルを更新
            update_params = {  # 更新パラメータ
                'fileId': file_id,  # ファイルID
                'media_body': media,  # メディアオブジェクト
                'supportsAllDrives': True  # 全ドライブ対応
            }
            self.service.files().update(**update_params).execute()  # ファイル更新
            # ファイルのフルパスを含めてログ出力
            full_path = f"{self.base_folder_path}/{vc_name}/{filename}"  # フルパス
            drive_info = f" (Shared Drive: {self.shared_drive_id})" if self.shared_drive_id else " (My Drive)"  # ドライブ情報
            logger.info(f"CSVファイルを更新しました: {full_path}{drive_info} (ID: {file_id})")  # 更新完了をログ出力
        else:  # 新規ファイルを作成
            file_metadata = {  # ファイルのメタデータ
                'name': filename,  # ファイル名
                'parents': [vc_folder_id]  # VCチャンネル用フォルダ
            }
            create_params = {'body': file_metadata, 'media_body': media, 'fields': 'id'}  # 作成パラメータ
            # 共有ドライブ・共有フォルダの両方に対応
            create_params['supportsAllDrives'] = True  # 全ドライブ対応
            # ファイル作成
            file = self.service.files().create(**create_params).execute()  # ファイル作成
            file_id = file.get('id')  # ファイルIDを取得
            # ファイルのフルパスを含めてログ出力
            full_path = f"{self.base_folder_path}/{vc_name}/{filename}"  # フルパス
            drive_info = f" (Shared Drive: {self.shared_drive_id})" if self.shared_drive_id else " (My Drive)"  # ドライブ情報
            logger.info(f"CSVファイルを新規作成しました: {full_path}{drive_info} (ID: {file_id})")  # 作成完了をログ出力

        # 一時ファイルを削除
        try:
            os.remove(temp_filename)  # 一時ファイル削除
        except PermissionError:
            logger.warning(f"一時ファイルを削除できませんでした（使用中）: {temp_filename}")  # ファイル使用中の警告
        except Exception as e:
            logger.warning(f"一時ファイルの削除中にエラーが発生しました: {e}")  # その他のエラー

    def upsert_presence(self, members: List[Dict[str, Any]]) -> Dict[str, int]:
        """メンバーの出席情報を記録（Upsert）

        Discord VCチャンネルの参加者情報をGoogle Drive上のCSVファイルに記録します。
        VCチャンネルごとに別々のCSVファイルで管理し、各参加者の出席記録を
        日付と時刻（YYYY/M/D HH:MM形式）付きで保存します。

        処理の流れ:
        1. メンバーリストをVCチャンネルごとにグループ化
        2. 各VCチャンネルのCSVファイルをダウンロード（または新規作成）
        3. 今日の日付のデータと照合して新規/更新を判定
        4. CSVファイルを更新してGoogle Driveにアップロード

        Args:
            members: メンバー情報のリスト（user_id, user_name, vc_nameを含む）

        Returns:
            処理結果（new: 新規追加数, updated: 更新数）
        """  # メソッドの説明
        if not self.service:  # APIサービスが未接続の場合
            raise RuntimeError("Google Driveに接続されていません")  # エラーを発生

        # JSTの今日の日付と時刻を取得
        jst = timezone(timedelta(hours=9))  # JST（UTC+9）のタイムゾーン
        now_jst = datetime.now(jst)  # 現在のJST日時
        # WindowsとLinux/macOSの両方に対応した日付フォーマット
        today_jst = f"{now_jst.year}/{now_jst.month}/{now_jst.day}"  # 今日の日付（YYYY/M/D形式）
        datetime_jst = f"{now_jst.year}/{now_jst.month}/{now_jst.day} {now_jst.strftime('%H:%M')}"  # 日付と時刻（YYYY/M/D HH:MM形式）

        # === VCチャンネルごとにメンバーをグループ化 ===
        # 同じVCチャンネルの参加者をまとめて処理するため、
        # VC名をキーとした辞書形式でグループ化します
        vc_groups = {}  # VC名ごとにメンバーを分類
        for member in members:  # メンバーリストをループ
            vc_name = member.get('vc_name', 'unknown')  # VC名を取得
            if vc_name not in vc_groups:  # まだリストがない場合
                vc_groups[vc_name] = []  # 新しいリストを作成
            vc_groups[vc_name].append(member)  # メンバーを追加

        total_new_count = 0  # 全体の新規追加カウンタ
        total_update_count = 0  # 全体の更新カウンタ

        # === 各VCチャンネルのCSVファイルを処理 ===
        # VCチャンネルごとに独立したCSVファイルで管理するため、
        # グループ化したデータを順次処理していきます
        for vc_name, vc_members in vc_groups.items():  # VC名ごとにループ
            # === 既存CSVファイルの取得または新規作成の準備 ===
            # Google Driveから該当VCチャンネルのCSVファイルを検索
            file_id = self._get_csv_file_id(vc_name)  # ファイルID取得

            if file_id:  # ファイルが存在する場合
                # 既存データをダウンロード
                existing_data = self._download_csv(file_id)  # CSVダウンロード
            else:  # ファイルが存在しない場合
                existing_data = []  # 空のリスト

            # === 今日の既存データを抽出 ===
            # 重複記録を防ぐため、既存データから今日の日付のレコードを抽出し、
            # user_idをキーとした辞書形式で保持します
            today_data = {  # 今日のデータを辞書形式で保存
                row['user_id']: row  # user_idをキーとする
                for row in existing_data  # 既存データをループ
                if row.get('datetime_jst', '').startswith(today_jst)  # 今日の日付のデータを抽出
            }  # 辞書の閉じ括弧

            new_count = 0  # 新規追加カウンタ
            update_count = 0  # 更新カウンタ

            # === 各メンバーの出席記録を処理 ===
            # VCチャンネルの参加者一人ずつについて、
            # 新規追加または既存レコードの更新を行います
            for member in vc_members:  # VCメンバーリストをループ
                user_id = member['user_id']  # ユーザーID

                if user_id not in today_data:  # 今日のデータに存在しない場合
                    # 新規追加
                    new_row = {  # 新しい行データ
                        'datetime_jst': datetime_jst,  # 日付と時刻
                        'user_id': member['user_id'],  # ユーザーID
                        'user_name': member['user_name'],  # ユーザー名
                    }
                    existing_data.append(new_row)  # データに追加
                    new_count += 1  # カウンタ増加
                    logger.info(f"{vc_name}に新規参加: {member.get('user_name', '不明')} - {datetime_jst}")  # 新規追加をログ出力
                else:
                    # 既に今日のデータがある場合はスキップ（重複を防ぐため）
                    pass  # 何もしない

            # === 更新したデータをGoogle Driveにアップロード ===
            # 新規追加・更新したデータを含む全データをCSVファイルとして
            # Google Driveにアップロードします
            self._upload_csv(vc_name, existing_data, file_id)  # CSV更新

            total_new_count += new_count  # 全体のカウンタを更新
            total_update_count += update_count  # 全体のカウンタを更新

            if new_count > 0 or update_count > 0:  # 変更があった場合
                csv_filename = f"{vc_name}.csv"  # CSVファイル名を生成
                # フルパスと共有ドライブ情報を含めて更新サマリをログ出力
                full_path = f"{self.base_folder_path}/{vc_name}/{csv_filename}"  # フルパス
                drive_info = f" (Shared Drive: {self.shared_drive_id})" if self.shared_drive_id else " (My Drive)"  # ドライブ情報
                logger.info(f"{full_path}{drive_info}を更新: 新規{new_count}件、更新{update_count}件")  # 更新サマリをログ出力

        return {"new": total_new_count, "updated": total_update_count}  # 処理結果を返す