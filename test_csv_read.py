import csv

# CSVファイルを読み込み
csv_file = r"C:\Users\SeiyaKawashima\Downloads\☁もくもく広場_1_TST.csv"
target_date = "2025/9/22"

# 総行数と対象日のレコード数をカウント
total_lines = 0
target_records = []
unique_users = set()

with open(csv_file, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_lines += 1
        if row['datetime_jst'].startswith(target_date):
            target_records.append(row)
            unique_users.add(row['user_id'])

print(f"CSVファイル総行数（ヘッダー除く）: {total_lines}")
print(f"{target_date}のレコード数: {len(target_records)}")
print(f"{target_date}のユニークユーザー数: {len(unique_users)}")
print(f"\nユニークユーザー一覧:")
for user_id in sorted(unique_users):
    matching_records = [r for r in target_records if r['user_id'] == user_id]
    if matching_records:
        user_name = matching_records[0].get('user_name', 'Unknown')
        display_name = matching_records[0].get('display_name', '')
        print(f"  - {user_name} ({display_name}) - {len(matching_records)}件")