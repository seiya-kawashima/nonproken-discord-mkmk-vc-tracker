#!/usr/bin/env python3
"""Google Sheets Base64認証テスト

GitHub ActionsでBase64エンコードされた認証情報のテストを行います。
"""

import os
import sys
import json
import base64
import tempfile
import argparse

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import EnvConfig, Environment


def test_base64_auth(env_arg=None):
    """Base64認証のテスト"""
    
    # 環境を取得
    try:
        env = EnvConfig.get_environment_from_arg(env_arg)
    except ValueError as e:
        print(f"\n❌ エラー: {e}")
        return 1
    
    env_name = EnvConfig.get_environment_name(env)
    
    print("=" * 70)
    print(f"Google Sheets Base64認証テスト ({env_name})")
    print("=" * 70)
    
    # 指定環境の設定を取得
    try:
        config = EnvConfig.get_google_sheets_config(env)
        print("\n✅ 設定取得成功")
        print(f"  シート名: {config['sheet_name']}")
    except ValueError as e:
        print(f"\n❌ 設定エラー: {e}")
        return 1
    
    # Base64エンコードされた認証情報の処理
    base64_data = config['service_account_json_base64']
    json_file = config['service_account_json']
    
    print("\n認証情報チェック:")
    
    if base64_data:
        print("  ✅ Base64データ: 設定済み")
        
        # Base64デコードテスト
        try:
            decoded_bytes = base64.b64decode(base64_data)
            decoded_str = decoded_bytes.decode('utf-8')
            json_data = json.loads(decoded_str)
            
            print("  ✅ Base64デコード: 成功")
            print(f"  ✅ JSONパース: 成功")
            
            # 必須フィールドのチェック
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing_fields = [f for f in required_fields if f not in json_data]
            
            if missing_fields:
                print(f"  ❌ 必須フィールド不足: {missing_fields}")
                return 1
            else:
                print(f"  ✅ 必須フィールド: 全て存在")
                print(f"    - type: {json_data.get('type')}")
                print(f"    - project_id: {json_data.get('project_id')}")
                print(f"    - client_email: {json_data.get('client_email')}")
                
            # 一時ファイルに保存してテスト
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json_data, f)
                temp_file = f.name
            
            print(f"  ✅ 一時ファイル作成: {temp_file}")
            
            # Google Sheets接続テスト
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                
                SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
                creds = Credentials.from_service_account_file(temp_file, scopes=SCOPES)
                client = gspread.authorize(creds)
                
                # スプレッドシートを開く
                sheet = client.open(config['sheet_name'])
                worksheet = sheet.get_worksheet(0)
                
                print(f"\n✅ Google Sheets接続成功!")
                print(f"  スプレッドシート: {config['sheet_name']}")
                
                # テストデータ書き込み
                from datetime import datetime
                test_data = [["Base64認証テスト", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
                worksheet.update('A1:B1', test_data)
                print(f"  ✅ テストデータ書き込み成功")
                
            except Exception as e:
                print(f"\n❌ Google Sheets接続エラー: {e}")
                return 1
            finally:
                # 一時ファイル削除
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    print(f"  ✅ 一時ファイル削除完了")
                    
        except base64.binascii.Error as e:
            print(f"  ❌ Base64デコードエラー: {e}")
            return 1
        except json.JSONDecodeError as e:
            print(f"  ❌ JSONパースエラー: {e}")
            return 1
        except Exception as e:
            print(f"  ❌ 予期しないエラー: {e}")
            return 1
            
    elif os.path.exists(json_file):
        print(f"  ⚠️ Base64データなし、ファイル使用: {json_file}")
    else:
        print("  ❌ 認証情報が見つかりません")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ Base64認証テスト完了")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Base64認証テスト')
    parser.add_argument(
        '--env',
        type=int,
        choices=[0, 1, 2],
        default=1,  # デフォルトはテスト環境
        help='0=本番環境, 1=テスト環境(デフォルト), 2=開発環境'
    )
    args = parser.parse_args()
    sys.exit(test_base64_auth(args.env))