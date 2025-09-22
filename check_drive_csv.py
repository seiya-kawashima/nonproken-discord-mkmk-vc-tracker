from slack_notifier_attendance import DailyAggregator
import datetime
import io
from googleapiclient.http import MediaIoBaseDownload

# 集約クラスのインスタンスを作成
aggregator = DailyAggregator(env=1, target_date=datetime.date(2025, 9, 22))

# CSVファイルを取得
csv_files = aggregator.get_csv_files_from_drive()

for csv_file in csv_files:
    print(f"ファイル名: {csv_file['name']}")

    # ファイルをダウンロード
    request = aggregator.drive_service.files().get_media(fileId=csv_file['id'])
    file_content = io.BytesIO()
    downloader = MediaIoBaseDownload(file_content, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    # CSVをパース（BOMを除去）
    file_content.seek(0)
    csv_text = file_content.read().decode('utf-8-sig')

    lines = csv_text.strip().split('\n')
    print(f"  総行数: {len(lines)}")

    # 最後の5行を表示
    print("  最後の5行:")
    for line in lines[-5:]:
        print(f"    {line}")

    # 2025/9/22のデータを全て検索
    target_records = []
    for line in lines[1:]:  # ヘッダーをスキップ
        if line.startswith("2025/9/22"):
            target_records.append(line)

    print(f"\n  2025/9/22のレコード数: {len(target_records)}")
    if target_records:
        print("  最初の5件:")
        for i, record in enumerate(target_records[:5]):
            print(f"    {i+1}. {record}")
        if len(target_records) > 5:
            print("  最後の3件:")
            for i, record in enumerate(target_records[-3:], len(target_records)-2):
                print(f"    {i}. {record}")