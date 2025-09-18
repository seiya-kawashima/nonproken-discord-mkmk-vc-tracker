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

## 📥 Input（入力）

### テスト1: Discord VCメンバー取得
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_members | List[Dict] | 擬似メンバー情報 | [{"id": "123", "name": "田中", "joined_at": "2025-01-18 10:00:00"}] |
| channel_id | str | 対象のボイスチャンネルID | "1234567890" |

### テスト2: CSV記録処理
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_template_data | str | 既存のCSVテンプレート | "日付,田中,佐藤\n2025-01-16,1,0" |
| mock_members | List[Dict] | 記録するメンバー情報 | [{"name": "田中"}] |

### テスト3: 日次集計とSlack通知
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| mock_csv_data | str | 集計対象のCSVデータ | "日付,田中\n2025-01-16,1\n2025-01-17,1" |
| target_date | str | 集計対象日 | "2025-01-18" |

## 📤 Output（出力）

### テスト1: Discord VCメンバー取得
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| members_list | List[str] | 取得したメンバー名リスト | ["田中", "佐藤"] |
| status | bool | 取得成功/失敗 | True |

### テスト2: CSV記録処理
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| updated_csv | str | 更新後のCSVデータ | "日付,田中,佐藤\n2025-01-16,1,0\n2025-01-18,1,0" |
| is_match | bool | 期待値との一致確認 | True |

### テスト3: 日次集計とSlack通知
| 項目 | 型 | 説明 | 例 |
|------|-----|------|-----|
| slack_message | str | 生成されたSlackメッセージ | "【本日の出席】\n田中: 累計2日, 連続2日" |
| stats_correct | bool | 統計値の正確性 | True |

## 🔧 処理の流れ

### テスト1: Discord VCメンバー取得
1. Discord APIの`on_ready`イベントをモック化
2. 固定のmock_membersデータを返すように設定
3. VCメンバー取得処理を実行
4. 返されたメンバーリストを検証

### テスト2: CSV記録処理
1. 既存のCSVファイルをmock_template_dataで上書き
2. `csv_client.upsert_presence()`をモック化
3. メンバー情報をCSVに記録
4. 更新後のCSVデータを期待値と比較

### テスト3: 日次集計とSlack通知
1. テスト用CSVデータを準備
2. daily_aggregatorの集計処理を実行
3. `post_to_slack()`メソッドの出力を取得
4. 累計日数・連続ログイン日数（土日祝除く）を検証

## 💡 使用例

```python
# テスト1: VCメンバー取得
mock_members = [
    {"id": "123", "name": "田中", "joined_at": "2025-01-18 10:00:00"},
    {"id": "456", "name": "佐藤", "joined_at": "2025-01-18 10:05:00"}
]
result = test_get_vc_members(mock_members)
assert result == ["田中", "佐藤"]

# テスト2: CSV記録
template = "日付,田中,佐藤\n2025-01-16,1,0"
members = [{"name": "田中"}]
updated = test_csv_recording(template, members)
assert "2025-01-18,1,0" in updated

# テスト3: Slack通知
expected_msg = "【本日の出席】\n田中: 累計2日, 連続2日"
actual_msg = test_slack_notification()
assert expected_msg in actual_msg
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