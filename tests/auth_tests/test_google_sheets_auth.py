"""Google Sheets接続テスト用スクリプト

このスクリプトを実行して、Google Sheetsの設定が正しくできているか確認できます。
使い方: python test_google_sheets.py

環境変数の読み込み方針:
1. 開発環境（ローカル）: .envファイルから読み込み
   - GOOGLE_SHEET_NAME
   - GOOGLE_SERVICE_ACCOUNT_JSON

2. テスト環境（GitHub Actions）: TEST_プレフィックス付き
   - TEST_GOOGLE_SHEET_NAME
   - TEST_GOOGLE_SERVICE_ACCOUNT_JSON_BASE64

3. 本番環境（GitHub Actions）: プレフィックスなし
   - GOOGLE_SHEET_NAME
   - GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
"""

import gspread  # Google Sheets操作ライブラリ
from google.oauth2.service_account import Credentials  # 認証用
import os  # 環境変数取得用
from datetime import datetime  # 現在時刻取得用
import base64  # Base64デコード用
import json  # JSON処理用
import tempfile  # 一時ファイル作成用
from config import EnvConfig  # 環境変数設定モジュール

print("=" * 70)
print("Google Sheets 接続テスト - 全環境チェック")
print("=" * 70)

# 認証情報を設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']  # スプレッドシート編集権限

def decode_base64_json(base64_string):
    """Base64エンコードされたJSONをデコードして一時ファイルに保存"""
    try:
        decoded_bytes = base64.b64decode(base64_string)
        decoded_str = decoded_bytes.decode('utf-8')
        json_data = json.loads(decoded_str)
        
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            return f.name
    except Exception as e:
        return None

def test_environment(env_name, sheet_name, service_account_file, is_base64=False):
    """各環境の接続テストを実行"""
    print(f"\n{'=' * 60}")
    print(f"🔍 {env_name}のテスト")
    print(f"{'=' * 60}")
    
    # 設定値の確認
    print(f"\n📋 設定確認:")
    print(f"  - スプレッドシート名: {sheet_name if sheet_name else '❌ 未設定'}")
    print(f"  - 認証ファイル: {'Base64データ' if is_base64 else service_account_file if service_account_file else '❌ 未設定'}")
    
    if not sheet_name:
        print(f"\n⚠️ {env_name}のスプレッドシート名が設定されていません")
        return False
    
    if not service_account_file:
        print(f"\n⚠️ {env_name}の認証情報が設定されていません")
        return False
    
    # Base64デコード処理
    actual_file = service_account_file
    temp_file = None
    
    if is_base64:
        print(f"\n🔐 Base64デコード処理中...")
        temp_file = decode_base64_json(service_account_file)
        if not temp_file:
            print(f"   ❌ Base64デコードに失敗しました")
            return False
        actual_file = temp_file
        print(f"   ✅ デコード成功")
    else:
        # ファイルの存在確認
        if not os.path.exists(actual_file):
            print(f"\n❌ 認証ファイル '{actual_file}' が見つかりません")
            return False
    
    try:
        print(f"\n🔐 認証処理中...")
        
        # 認証
        creds = Credentials.from_service_account_file(
            actual_file,
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        print("   ✅ 認証成功")
        
        print(f"\n📊 スプレッドシート '{sheet_name}' に接続中...")
        
        # スプレッドシートを開く
        sheet = client.open(sheet_name)
        worksheet = sheet.get_worksheet(0)  # 最初のシートを取得
        print("   ✅ 接続成功")
        
        print(f"\n✏️ テストデータを書き込み中...")
        
        # 現在時刻を取得
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # テストデータを書き込み（環境ごとに異なる場所）
        if env_name == "開発環境":
            cell_range = 'A1:B3'
        elif env_name == "テスト環境":
            cell_range = 'D1:E3'
        else:  # 本番環境
            cell_range = 'G1:H3'
        
        test_data = [
            [f"{env_name} テスト", now],
            ["ステータス", "✅ 接続成功"],
            ["メッセージ", "設定OK"]
        ]
        
        # データを書き込み
        worksheet.update(cell_range, test_data)
        print(f"   ✅ {cell_range}に書き込み成功")
        
        print(f"\n✅ {env_name}のテスト成功！")
        
        # 一時ファイルの削除
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
        
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\n❌ スプレッドシート '{sheet_name}' が見つかりません")
        print("   📌 確認事項:")
        print("   - スプレッドシート名が正しいか確認")
        print("   - サービスアカウントに共有されているか確認")
        
    except gspread.exceptions.APIError as e:
        print(f"\n❌ Google API エラー: {e}")
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
    
    finally:
        # 一時ファイルの削除
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
    
    return False

# テスト結果を格納
results = {
    "開発環境": False,
    "テスト環境": False,
    "本番環境": False
}

# 1. 開発環境のテスト
print("\n" + "=" * 70)
print("📌 環境変数の読み込み優先順位")
print("=" * 70)
print("1. テスト環境 (TEST_プレフィックス) - GitHub Actions テスト用")
print("2. 本番環境 (プレフィックスなし) - GitHub Actions 本番用")
print("3. 開発環境 (.envファイル) - ローカル開発用")

# 開発環境のテスト（.envファイルから）
dev_config = EnvConfig.get_google_sheets_config(use_test=False)
dev_sheet = dev_config['sheet_name']
dev_account = dev_config['service_account_json']

# TEST_プレフィックスがない場合のみ開発環境をテスト
if dev_sheet and not EnvConfig.get(EnvConfig.TEST_GOOGLE_SHEET_NAME):
    results["開発環境"] = test_environment(
        "開発環境",
        dev_sheet,
        dev_account,
        is_base64=False
    )
else:
    print(f"\n{'=' * 60}")
    print(f"🔍 開発環境のテスト")
    print(f"{'=' * 60}")
    print("\n⚠️ 開発環境の設定がないか、テスト環境が優先されています")

# 2. テスト環境のテスト（TEST_プレフィックス付き）
test_config = EnvConfig.get_google_sheets_config(use_test=True)
test_sheet = test_config['sheet_name']
test_account_base64 = test_config['service_account_json_base64']
test_account_file = test_config['service_account_json']

if test_sheet:
    # Base64とファイルの両方を確認
    if test_account_base64:
        results["テスト環境"] = test_environment(
            "テスト環境",
            test_sheet,
            test_account_base64,
            is_base64=True
        )
    elif test_account_file:
        results["テスト環境"] = test_environment(
            "テスト環境",
            test_sheet,
            test_account_file,
            is_base64=False
        )
    else:
        print(f"\n{'=' * 60}")
        print(f"🔍 テスト環境のテスト")
        print(f"{'=' * 60}")
        print("\n⚠️ テスト環境の認証情報が設定されていません")
else:
    print(f"\n{'=' * 60}")
    print(f"🔍 テスト環境のテスト")
    print(f"{'=' * 60}")
    print("\n⚠️ テスト環境の設定がありません")

# 3. 本番環境のテスト（プレフィックスなし、GitHub Actions用）
# 本番環境はTEST_プレフィックスがない場合のみテスト
if not test_sheet:  # テスト環境が設定されていない場合のみ
    prod_config = EnvConfig.get_google_sheets_config(use_test=False)
    prod_sheet = prod_config['sheet_name']
    prod_account_base64 = prod_config['service_account_json_base64']
    
    if prod_sheet and prod_account_base64:
        results["本番環境"] = test_environment(
            "本番環境",
            prod_sheet,
            prod_account_base64,
            is_base64=True
        )
    elif prod_sheet and dev_account:
        # Base64がない場合は通常のファイルを試す（開発環境と同じ）
        print(f"\n{'=' * 60}")
        print(f"🔍 本番環境のテスト")
        print(f"{'=' * 60}")
        print("\n📌 注: 本番環境のBase64設定がないため、開発環境の設定を使用")
        results["本番環境"] = test_environment(
            "本番環境（開発設定で代用）",
            prod_sheet,
            dev_account,
            is_base64=False
        )
    else:
        print(f"\n{'=' * 60}")
        print(f"🔍 本番環境のテスト")
        print(f"{'=' * 60}")
        print("\n⚠️ 本番環境の設定がありません")
else:
    print(f"\n{'=' * 60}")
    print(f"🔍 本番環境のテスト")
    print(f"{'=' * 60}")
    print("\n⚠️ テスト環境が設定されているため、本番環境のテストはスキップ")

# 最終結果のサマリー
print("\n" + "=" * 70)
print("📊 テスト結果サマリー")
print("=" * 70)

for env_name, success in results.items():
    status = "✅ 成功" if success else "❌ 失敗/未設定"
    print(f"{env_name}: {status}")

# 全体の成功/失敗を判定
any_success = any(results.values())
all_success = all(results.values())

print("\n" + "=" * 70)
if all_success:
    print("🎉 すべての環境でテスト成功！")
elif any_success:
    print("⚠️ 一部の環境でテスト成功")
    print("   設定されていない環境は、必要に応じて設定してください")
else:
    print("❌ すべての環境でテスト失敗または未設定")
    print("   環境変数の設定を確認してください")

print("=" * 70)
print("\n📌 次のステップ:")
if not results["開発環境"]:
    print("   1. .envファイルに開発環境の設定を追加")
if not results["テスト環境"]:
    print("   2. TEST_プレフィックス付きの環境変数を設定（GitHub Actions用）")
if not results["本番環境"]:
    print("   3. 本番環境の環境変数を設定（GitHub Actions用）")

if any_success:
    print("   4. Google Sheetsを開いて、テストデータが書き込まれていることを確認")
    print("      - 開発環境: A1:B3")
    print("      - テスト環境: D1:E3")
    print("      - 本番環境: G1:H3")