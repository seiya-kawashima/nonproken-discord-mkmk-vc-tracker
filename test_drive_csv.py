from slack_notifier_attendance import VCDataAggregator
import datetime

# 集約クラスのインスタンスを作成
aggregator = VCDataAggregator(env=1, target_date=datetime.date(2025, 9, 22))

# CSVファイルを取得
csv_files = aggregator.get_csv_files_from_drive()
print(f"Google DriveのCSVファイル数: {len(csv_files)}")

for csv_file in csv_files:
    print(f"\nファイル名: {csv_file['name']}")

    # CSVファイルの内容を読み込み
    records = aggregator.read_csv_content(csv_file['id'], csv_file['name'])
    print(f"  読み込んだレコード数: {len(records)}")

    # ユーザーごとに集計
    user_counts = {}
    for record in records:
        user_name = record.get('user_name', 'Unknown')
        display_name = record.get('display_name', '')
        key = f"{user_name} ({display_name})"
        user_counts[key] = user_counts.get(key, 0) + 1

    print(f"  ユニークユーザー数: {len(user_counts)}")
    print("  ユーザー別レコード数:")
    for user, count in sorted(user_counts.items()):
        print(f"    - {user}: {count}件")