#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ログメッセージから絵文字を削除するスクリプト"""

import re

# ファイルを読み込み
with open('daily_aggregator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 絵文字パターンを定義（より包括的）
emoji_pattern = r'[🔍📂✅❌⚠️📖📝📈📊📁💬🔐🌐🚀🎉📄📅📍🔎ℹ️✨📋🏢📮🎨💡🔥✏️📓👉]\s*'

# logger行の絵文字を削除
content = re.sub(r'(logger\.(info|error|warning|debug)\(f?["\'])'+ emoji_pattern, r'\1', content)

# ファイルに書き戻し
with open('daily_aggregator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('絵文字を削除しました')