# 統合テスト仕様書

## 📌 このドキュメントについて
Discord ボットの主要機能（VCメンバー取得、CSV記録、日次集計）を統合的にテストする仕様書です。認証系の接続テストと、モックデータを使用した機能テストの両方を含みます。

## 🎯 テスト目的

### 認証系テスト
1. Discord APIへの接続認証が成功すること
2. Google Drive（Sheets）への接続認証が成功すること
3. Slack APIへの接続認証が成功すること

### 機能系テスト（モックデータ使用）
1. Discord VCメンバー情報の取得と記録が正しく動作すること
2. CSVファイルへの出席データ追記（アペンド）が正確であること
3. 日次集計とSlack通知メッセージが正しく生成されること（土日祝日の連続出席計算を含む）

### エンドツーエンドテスト（E2E）
1. **discord_attendance_collector.py**の`main()`関数を直接呼び出し、全体フローをテスト
2. **daily_aggregator.py**の`main()`関数を直接呼び出し、日次集計フローをテスト
3. 実際の処理フローを通して、エラーなく完了することを確認

## 📥 Input（入力データ - MockInputData）

### 認証系テスト
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| discord_token | str | Discord Bot Token | 環境変数から取得 |
| google_credentials | JSON | Google認証情報 | サービスアカウントJSON |
| slack_webhook_url | str | Slack Webhook URL | 環境変数から取得 |

### 機能系テスト1: Discord VCメンバー取得
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_members | List[Dict] | 擬似メンバー情報（モック対象） | [{"id": "123456789", "name": "田中太郎", "display_name": "田中"}, {"id": "987654321", "name": "佐藤花子", "display_name": "佐藤"}, {"id": "456789123", "name": "鈴木一郎", "display_name": "鈴木"}] |

### 機能系テスト2: CSV記録処理
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_template_data | str | 既存のCSVテンプレート | "日付,田中,佐藤,鈴木\n2025-01-16,1,1,0\n2025-01-17,0,1,1" |
| mock_members | List[str] | テスト1で取得したメンバー名リスト | ["田中", "佐藤", "鈴木"] |

### 機能系テスト3: 日次集計とSlack通知
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_csv_data | str | 集計対象のCSVデータ（テスト2の結果） | "日付,田中,佐藤,鈴木\n2025-01-16,1,1,0\n2025-01-17,0,1,1\n2025-01-18,1,1,1" |
| target_date | str | 集計対象日（土曜日） | "2025-01-18" |

### エンドツーエンドテスト: discord_attendance_collector.py
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| env_arg | str | 環境引数 | "1" （テスト環境） |
| mock_discord_api | Mock | Discord APIのモック | VC参加者リストを返すモック |
| mock_drive_api | Mock | Google Drive APIのモック | CSV書き込みをモック |

### エンドツーエンドテスト: daily_aggregator.py
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| env_arg | str | 環境引数 | "1" （テスト環境） |
| target_date | date | 集計対象日 | "2025-01-18" |
| mock_csv_data | str | CSVデータ | 1週間分の出席データ |
| mock_slack_api | Mock | Slack APIのモック | メッセージ送信をモック |

## 📤 Output（期待値データ - ExpectedData）

### 認証系テスト
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| discord_connected | bool | Discord接続成功 | True |
| google_connected | bool | Google Drive接続成功 | True |
| slack_connected | bool | Slack接続成功 | True |

### 機能系テスト1: Discord VCメンバー取得
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| members_list | List[str] | 取得したメンバー名リスト | ["田中", "佐藤"] |
| status | bool | 取得成功/失敗 | True |

### 機能系テスト2: CSV記録処理
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| updated_csv | str | 更新後のCSVデータ | "日付,田中,佐藤\n2025-01-16,1,0\n2025-01-18,1,1" |
| is_match | bool | 期待値との一致確認 | True |

### 機能系テスト3: 日次集計とSlack通知
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| slack_message | str | 生成されたSlackメッセージ | "【本日の出席】\n田中: 累計4日, 連続3日" |
| consecutive_calc_correct | bool | 土日祝を除く連続日数計算が正確 | True |

## 🔧 処理の流れ

### 認証系テスト
1. 各サービスへの接続テストを実行
2. Discord: Botトークンでログイン試行
3. Google Drive: サービスアカウントで認証試行
4. Slack: WebhookURLへのテストメッセージ送信
5. 全ての接続が成功することを確認

### 機能系統合テスト
1. **Discord VCメンバー取得（モック）**
   - `on_ready`イベントをモック化
   - 固定のmock_membersデータを返すように設定
   - VCメンバー取得処理を実行

2. **CSV記録処理**
   - 既存のCSVファイルをmock_template_dataで上書き
   - `csv_client.upsert_presence()`の前でモック化
   - メンバー情報をCSVに追記（アペンド）
   - 更新後のCSVデータを期待値と比較

3. **日次集計とSlack通知**
   - 追記されたCSVデータを使用
   - daily_aggregatorの集計処理を実行
   - `post_to_slack()`メソッドの出力を取得
   - 土日祝を除く連続ログイン日数を検証
   - 累計日数の正確性を確認

## 💡 使用例

```python
# 認証系テスト
def test_authentication():
    """全サービスへの接続確認"""
    assert test_discord_connection() == True
    assert test_google_drive_connection() == True
    assert test_slack_connection() == True

# 統合テスト（モックデータ使用）
def test_integration_with_mock():
    """モックデータで全機能を統合テスト"""
    # 1. VCメンバー取得（入力データ → 期待値と比較）
    input_members = MockInputData.get_mock_members()
    members = get_vc_members_mock(input_members)
    expected_names = ExpectedData.get_member_names()
    assert members == expected_names  # ["田中", "佐藤", "鈴木"]

    # 2. CSV追記処理（入力データ → 期待値と比較）
    template_csv = MockInputData.get_template_csv()
    today_members = MockInputData.get_today_members()
    updated_csv = append_to_csv(template_csv, today_members, "2025-01-18")
    expected_csv = ExpectedData.get_csv_after_append()
    assert updated_csv == expected_csv

    # 3. Slack通知（期待値データで検証）
    expected_stats = ExpectedData.get_stats_dict()
    message = generate_slack_message(expected_stats)
    expected_message = ExpectedData.get_expected_slack_message()

    # 土曜日だが、平日の連続出席を正しく計算
    assert "連続出席: 3日" in message  # 田中: 木金土で3日連続
    assert "連続出席: 2日" in message  # 佐藤: 金土で2日連続
```

## ⚠️ 注意事項
- モックデータは本番データと同じ形式を保つこと
- 土日祝日の判定ロジックは`jpholiday`ライブラリを使用
- CSVファイルのエンコーディングはUTF-8を使用
- タイムゾーンはJST（UTC+9）で統一

## 📊 テストデータ構造

### mock_members（Discord VCメンバー）
```json
[
  {
    "id": "123456789",
    "name": "田中太郎",
    "display_name": "田中",
    "joined_at": "2025-01-18 10:00:00",
    "status": "online"
  }
]
```

### mock_template_data（CSVテンプレート）
```csv
日付,田中,佐藤,鈴木
2025-01-15,1,0,1
2025-01-16,1,1,0
2025-01-17,0,1,1
```

### expected_message（期待するSlackメッセージ）
```
📊 【2025-01-18 もくもく会 出席統計】 📊

本日の出席者: 2名
- 田中: 累計出席 3日 | 連続出席 2日 🔥
- 佐藤: 累計出席 2日 | 連続出席 1日

素晴らしい継続です！
```

## ❓ FAQ

**Q: モックデータはどこに保存する？**
A: `tests/fixtures/`ディレクトリに保存します。

**Q: 実際のAPIを呼び出してテストしたい場合は？**
A: 環境変数`USE_REAL_API=true`を設定すると実APIを使用します（CI/CDでは使用不可）。

**Q: テスト実行時間を短縮するには？**
A: `pytest -n auto`で並列実行、または特定のテストのみ実行（`pytest -k test_name`）。