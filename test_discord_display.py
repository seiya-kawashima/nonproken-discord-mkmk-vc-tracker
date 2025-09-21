#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Discord表示名取得のデバッグスクリプト"""

import os
os.environ['LOGLEVEL'] = 'DEBUG'  # デバッグレベルを設定

import asyncio
import discord
from config import get_config, Environment
from loguru import logger
import sys

# ログ設定
logger.remove()
logger.add(sys.stderr, level="DEBUG", format="{time:HH:mm:ss} | {level} | {message}")

async def test_discord_display_names():
    """Discord表示名取得のテスト"""
    config = get_config(Environment.DEV)  # 開発環境の設定

    discord_token = config.get('discord_token')  # Discordトークン
    if not discord_token:
        logger.error("Discordトークンが設定されていません")
        return

    # テスト用のユーザーID（kawashima_noguchiさん）
    test_user_id = "1122441529944973312"

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        logger.info(f"Discord接続: {client.user}")
        logger.info(f"ギルド数: {len(client.guilds)}")

        for guild in client.guilds:
            logger.info(f"\n=== ギルド: {guild.name} (ID: {guild.id}) ===")
            logger.info(f"メンバー数: {guild.member_count}")

            # メンバー取得を試みる
            try:
                member = guild.get_member(int(test_user_id))
                if member:
                    logger.success(f"✅ メンバー発見: {member.name}")
                    logger.info(f"  - ID: {member.id}")
                    logger.info(f"  - ユーザー名: {member.name}")
                    logger.info(f"  - ニックネーム: {member.nick}")
                    logger.info(f"  - 表示名: {member.display_name}")
                    logger.info(f"  - グローバル名: {member.global_name if hasattr(member, 'global_name') else 'N/A'}")

                    # 判定ロジックを再現
                    display = member.nick if member.nick else member.name
                    logger.info(f"  → 最終的な表示名: {display}")
                else:
                    logger.warning(f"メンバーが見つかりません: {test_user_id}")

                    # 全メンバーをリスト（最初の10人）
                    logger.debug("ギルドメンバー一覧（最初の10人）:")
                    for i, m in enumerate(list(guild.members)[:10]):
                        logger.debug(f"  {i+1}. {m.name} (ID: {m.id}, nick: {m.nick})")

            except Exception as e:
                logger.error(f"エラー: {e}")

        await client.close()

    try:
        await client.start(discord_token)
    except Exception as e:
        logger.error(f"Discord接続エラー: {e}")

if __name__ == "__main__":
    logger.info("Discord表示名取得テスト開始")
    asyncio.run(test_discord_display_names())