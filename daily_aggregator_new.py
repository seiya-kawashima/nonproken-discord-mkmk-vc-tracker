    def get_csv_files_from_drive(self) -> List[Dict[str, str]]:
        """
        Google DriveからCSVファイル一覧を取得
        configのgoogle_drive_csv_pathテンプレートに基づいてファイルを探す

        Returns:
            CSVファイル情報のリスト [{id, name, vc_name}, ...]
        """
        try:
            logger.info(f"CSVファイルの検索を開始します")  # 検索開始ログ

            # configから設定されたCSVパステンプレートを使用
            if self.google_drive_csv_path:
                logger.info(f"CSVパステンプレート: {self.google_drive_csv_path}")  # テンプレート表示

                # パステンプレートを解析 (例: discord_mokumoku_tracker/csv/{vc_name}_0_PRD.csv)
                # {vc_name}より前の部分を抽出してフォルダパスとする
                path_parts = self.google_drive_csv_path.split('{vc_name}')
                if len(path_parts) >= 2:
                    # フォルダパスとファイルパターンを取得
                    folder_path = path_parts[0].rstrip('/')  # 末尾の/を削除
                    file_pattern = path_parts[1].lstrip('_')  # 先頭の_を削除（例: 0_PRD.csv）

                    logger.info(f"フォルダパス: {folder_path}")  # フォルダパス表示
                    logger.info(f"ファイルパターン: *_{file_pattern}")  # パターン表示
                else:
                    logger.error(f"CSVパステンプレートの形式が不正です: {self.google_drive_csv_path}")
                    return []
            else:
                logger.error("CSVパステンプレートが設定されていません")
                return []

            # フォルダ階層を探索
            folder_parts = folder_path.split('/')  # パスを分割
            if not folder_parts:
                logger.warning("フォルダパスが無効です")  # 無効なパス警告
                return []

            # ルートフォルダを検索（共有ドライブ対応）
            root_folder_name = folder_parts[0]  # ルートフォルダ名
            folder_query = f"name='{root_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            folder_results = self.drive_service.files().list(
                q=folder_query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                corpora='allDrives'
            ).execute()

            folders = folder_results.get('files', [])
            if not folders:
                logger.warning(f"Google Drive上に '{root_folder_name}' フォルダが見つかりません")  # フォルダ未発見警告
                return []

            current_folder_id = folders[0]['id']  # フォルダID取得
            logger.info(f"ルートフォルダを発見: {folders[0]['name']} (ID: {current_folder_id})")  # フォルダ発見ログ

            # 残りのフォルダ階層を順に探索
            for folder_name in folder_parts[1:]:
                subfolder_query = f"'{current_folder_id}' in parents and name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
                subfolder_results = self.drive_service.files().list(
                    q=subfolder_query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                subfolders = subfolder_results.get('files', [])
                if not subfolders:
                    logger.warning(f"サブフォルダ '{folder_name}' が見つかりません")  # サブフォルダ未発見警告
                    return []

                current_folder_id = subfolders[0]['id']  # 次のフォルダID
                logger.info(f"サブフォルダを発見: {folder_name} (ID: {current_folder_id})")  # フォルダ発見ログ

            # 最終フォルダ（csvフォルダ）内のCSVファイルを検索
            target_folder_id = current_folder_id
            logger.info(f"CSVファイルを検索中...")  # 検索ログ

            # ファイルパターンに基づいて検索（例: *_0_PRD.csv）
            csv_query = f"'{target_folder_id}' in parents and name contains '_{file_pattern}'"
            csv_results = self.drive_service.files().list(
                q=csv_query,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            csv_files = csv_results.get('files', [])

            # vc_nameを抽出してファイル情報に追加
            result_files = []
            for csv_file in csv_files:
                file_name = csv_file['name']
                # ファイル名からVCチャンネル名を抽出（例: ☁もくもく広場_0_PRD.csv → ☁もくもく広場）
                if file_name.endswith(f'_{file_pattern}'):
                    vc_name = file_name.replace(f'_{file_pattern}', '')
                    result_files.append({
                        'id': csv_file['id'],
                        'name': file_name,
                        'vc_name': vc_name
                    })
                    logger.info(f"  CSVファイルを発見: {file_name} (VCチャンネル: {vc_name})")  # ファイル発見ログ

            logger.info(f"合計{len(result_files)}個のCSVファイルを発見しました")  # CSVファイル数ログ
            return result_files

        except Exception as e:
            logger.error(f"CSVファイルの取得に失敗しました: {e}")  # エラーログ
            import traceback
            logger.error(traceback.format_exc())  # スタックトレース
            return []