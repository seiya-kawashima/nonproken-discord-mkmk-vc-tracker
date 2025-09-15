"""Google Drive権限テストスクリプト

このスクリプトは以下を確認します：
1. サービスアカウントの認証が成功するか
2. 共有ドライブにアクセスできるか
3. フォルダを作成できるか
4. CSVファイルを作成できるか
"""

import os  # 環境変数取得用
import sys  # システム操作用
import csv  # CSV処理用
import tempfile  # 一時ファイル用
from datetime import datetime  # 日時処理用
from loguru import logger  # ログ出力用

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import EnvConfig, Environment  # 環境設定
from google.oauth2.service_account import Credentials  # Google認証
from googleapiclient.discovery import build  # Google API
from googleapiclient.http import MediaFileUpload  # ファイルアップロード
from googleapiclient.errors import HttpError  # エラー処理

# ログ設定
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")


def test_drive_permissions(env_arg=2):
    """Google Drive権限テスト

    Args:
        env: 環境（0=PRD, 1=TST, 2=DEV）
    """
    logger.info(f"===== Google Drive権限テスト開始 =====")

    # 1. 環境設定を取得
    env = Environment.from_value(env_arg)
    env_name = EnvConfig.get_environment_name(env)
    logger.info(f"環境: {env_name}")

    try:
        drive_config = EnvConfig.get_google_drive_config(env)
    except ValueError as e:
        logger.error(f"設定エラー: {e}")
        return False

    # 設定値を表示
    logger.info(f"フォルダパス: {drive_config.get('folder_path')}")
    logger.info(f"共有ドライブID: {drive_config.get('shared_drive_id', 'なし')}")

    # 2. サービスアカウント認証
    try:
        service_account_json = drive_config['service_account_json']

        # 認証情報を作成
        creds = Credentials.from_service_account_file(
            service_account_json,
            scopes=['https://www.googleapis.com/auth/drive']
        )

        # APIサービスを構築
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ サービスアカウント認証成功")

    except Exception as e:
        logger.error(f"❌ 認証失敗: {e}")
        return False

    # 3. 共有ドライブの確認
    shared_drive_id = drive_config.get('shared_drive_id')

    if shared_drive_id:
        logger.info(f"共有ドライブID: {shared_drive_id}")

        try:
            # 共有ドライブ情報を取得
            drive_info = service.drives().get(
                driveId=shared_drive_id
            ).execute()

            logger.info(f"✅ 共有ドライブ名: {drive_info.get('name', '不明')}")

        except HttpError as e:
            if e.resp.status == 404:
                logger.error(f"❌ 共有ドライブが見つかりません: {shared_drive_id}")
            elif e.resp.status == 403:
                logger.error(f"❌ 共有ドライブへのアクセス権限がありません")
                logger.error(f"   サービスアカウントを共有ドライブのメンバーに追加してください")
            else:
                logger.error(f"❌ 共有ドライブエラー: {e}")
            return False
    else:
        logger.info("共有ドライブを使用しません（マイドライブ使用）")

    # 4. テストフォルダ作成
    test_folder_name = f"test_folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"テストフォルダ作成: {test_folder_name}")

    try:
        # フォルダメタデータ
        folder_metadata = {
            'name': test_folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # 共有ドライブ内に作成する場合は、共有ドライブIDを親として指定
        if shared_drive_id:
            folder_metadata['parents'] = [shared_drive_id]

        # 作成パラメータ
        create_params = {
            'body': folder_metadata,
            'fields': 'id, name',
            'supportsAllDrives': True
        }

        # フォルダ作成
        folder = service.files().create(**create_params).execute()
        folder_id = folder.get('id')
        logger.info(f"✅ フォルダ作成成功: {folder.get('name')} (ID: {folder_id})")

    except HttpError as e:
        logger.error(f"❌ フォルダ作成失敗: {e}")
        return False

    # 5. テストCSVファイル作成
    test_csv_name = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    logger.info(f"テストCSVファイル作成: {test_csv_name}")

    try:
        # CSVデータを作成
        csv_data = [
            ['datetime', 'user_id', 'user_name', 'status'],
            [datetime.now().isoformat(), '123456', 'test_user', 'present']
        ]

        # 一時ファイルに書き込み
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, test_csv_name)

        with open(temp_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        # ファイルメタデータ
        file_metadata = {
            'name': test_csv_name,
            'parents': [folder_id]  # 先ほど作成したフォルダ内に配置
        }

        # メディアアップロード
        media = MediaFileUpload(
            temp_file,
            mimetype='text/csv',
            resumable=True
        )

        # ファイル作成パラメータ
        create_params = {
            'body': file_metadata,
            'media_body': media,
            'fields': 'id, name',
            'supportsAllDrives': True
        }

        # ファイル作成
        file = service.files().create(**create_params).execute()
        logger.info(f"✅ CSVファイル作成成功: {file.get('name')} (ID: {file.get('id')})")

        # 一時ファイル削除
        os.remove(temp_file)

    except HttpError as e:
        if 'storageQuotaExceeded' in str(e):
            logger.error(f"❌ CSVファイル作成失敗: サービスアカウントにストレージ容量がありません")
            logger.error(f"   共有ドライブを使用するか、既存フォルダを共有してください")
        else:
            logger.error(f"❌ CSVファイル作成失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        return False

    # 6. 作成したファイルの確認
    logger.info("作成したファイルの確認...")

    try:
        # フォルダ内のファイルを検索
        query = f"'{folder_id}' in parents and trashed=false"
        list_params = {
            'q': query,
            'fields': 'files(id, name, mimeType)',
            'supportsAllDrives': True
        }

        if shared_drive_id:
            list_params['includeItemsFromAllDrives'] = True
            list_params['driveId'] = shared_drive_id
            list_params['corpora'] = 'drive'

        results = service.files().list(**list_params).execute()
        files = results.get('files', [])

        logger.info(f"フォルダ内のファイル数: {len(files)}")
        for file in files:
            logger.info(f"  - {file['name']} ({file['mimeType']})")

    except Exception as e:
        logger.error(f"ファイル確認エラー: {e}")

    # 7. クリーンアップ（テストファイルの削除）
    logger.info("テストファイルのクリーンアップ...")

    try:
        # CSVファイル削除
        if 'file' in locals() and file.get('id'):
            delete_params = {'fileId': file['id']}
            if shared_drive_id:
                delete_params['supportsAllDrives'] = True
            service.files().delete(**delete_params).execute()
            logger.info(f"  CSVファイル削除: {file['name']}")

        # フォルダ削除
        if folder_id:
            delete_params = {'fileId': folder_id}
            if shared_drive_id:
                delete_params['supportsAllDrives'] = True
            service.files().delete(**delete_params).execute()
            logger.info(f"  フォルダ削除: {test_folder_name}")

    except Exception as e:
        logger.warning(f"クリーンアップ中のエラー（無視可）: {e}")

    logger.info("===== テスト完了 =====")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Google Drive権限テスト')
    parser.add_argument(
        '--env',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='環境: 0=PRD, 1=TST, 2=DEV（デフォルト: 2）'
    )

    args = parser.parse_args()

    # テスト実行
    success = test_drive_permissions(args.env)

    # 結果表示
    if success:
        logger.info("✅ すべてのテストが成功しました！")
        logger.info("Google Drive権限は正しく設定されています。")
    else:
        logger.error("❌ テストが失敗しました。")
        logger.error("上記のエラーメッセージを確認して、権限設定を修正してください。")

    sys.exit(0 if success else 1)