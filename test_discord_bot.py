#!/usr/bin/env python3
"""Discord Bot接続テストスクリプト

使用方法:
    python test_discord_bot.py         # 本番環境のテスト
    python test_discord_bot.py --test  # テスト環境のテスト
    python test_discord_bot.py --dev   # 開発環境のテスト
"""

import discord
import asyncio
import os
import sys
import argparse
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from config import EnvConfig, Environment

async def test_discord_bot(env=Environment.PRD):
    """Discord Bot接続テスト
    
    Args:
        env: テスト対象の環境
    
    Returns:
        bool: テスト成功時True
    """
    
    env_name = EnvConfig.get_environment_name(env)
    print("=" * 70)
    print(f"Discord Bot接続テスト ({env_name})")
    print("=" * 70)
    
    # Discord設定を取得
    try:
        discord_config = EnvConfig.get_discord_config(env)
        token = discord_config['token']
        channel_ids = discord_config['channel_ids']
    except ValueError as e:
        print(f"❌ 設定エラー: {e}")
        return False
    
    print(f"✅ トークン: 設定済み")
    print(f"📍 監視対象VCチャンネル: {len(channel_ids)}個")
    for ch_id in channel_ids:
        print(f"   - {ch_id}")
    
    # Botクライアント設定
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    
    client = discord.Client(intents=intents)
    connection_success = False
    
    @client.event
    async def on_ready():
        nonlocal connection_success
        print(f"\n✅ Bot接続成功: {client.user}")
        print(f"📊 環境: {env_name}")
        print("\n接続済みサーバー:")
        
        for guild in client.guilds:
            print(f"\n  📍 {guild.name} (ID: {guild.id})")
            print(f"     メンバー数: {guild.member_count}")
            
            # VCチャンネル情報
            voice_channels = [ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)]
            print(f"     VCチャンネル数: {len(voice_channels)}")
            
            # 監視対象チャンネルの確認
            if channel_ids:  # チャンネルIDが設定されている場合
                print("     監視対象VC:")
                found_any = False
                for ch_id_str in channel_ids:
                    if ch_id_str:
                        try:
                            ch_id = int(ch_id_str)
                            channel = guild.get_channel(ch_id)
                            if channel:
                                print(f"       ✅ {channel.name} (ID: {ch_id})")
                                if hasattr(channel, 'members'):
                                    print(f"          現在のメンバー数: {len(channel.members)}")
                                    if channel.members:
                                        print("          メンバー:")
                                        for member in channel.members[:5]:  # 最初の5人まで表示
                                            print(f"            - {member.display_name}")
                                        if len(channel.members) > 5:
                                            print(f"            ... 他{len(channel.members) - 5}名")
                                found_any = True
                        except ValueError:
                            print(f"       ⚠️ 無効なチャンネルID: {ch_id_str}")

                if not found_any:
                    print("       ❌ このサーバーに監視対象VCが見つかりません")
            else:  # チャンネルIDが未設定の場合、全VCチャンネルを表示
                print("     全VCチャンネル（監視対象未設定）:")
                for vc in voice_channels[:10]:  # 最初の10個まで表示
                    print(f"       📢 {vc.name} (ID: {vc.id})")
                    if hasattr(vc, 'members') and vc.members:
                        print(f"          現在のメンバー数: {len(vc.members)}")
                if len(voice_channels) > 10:
                    print(f"       ... 他{len(voice_channels) - 10}個のVCチャンネル")
        
        connection_success = True
        await client.close()
    
    try:
        # Botを起動（タイムアウト付き）
        await asyncio.wait_for(client.start(token), timeout=10.0)
    except asyncio.TimeoutError:
        print("⏱️ タイムアウト: 接続に時間がかかりすぎています")
        return False
    except discord.LoginFailure:
        print("❌ ログイン失敗: トークンが無効です")
        print("\nトラブルシューティング:")
        print("1. トークンが正しくコピーされているか確認")
        print("2. Discord Developer Portalでトークンを再生成")
        print("3. 環境変数が正しく設定されているか確認")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    if connection_success:
        print("\n" + "=" * 70)
        print("✅ テスト成功")
        print("=" * 70)
        print("確認項目:")
        print("  ✅ Botトークンの有効性")
        print("  ✅ サーバーへの接続")
        print("  ✅ VCチャンネルへのアクセス")
        print("  ✅ メンバー情報の取得")
        return True
    else:
        print("\n❌ 接続に失敗しました")
        return False

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Discord Bot接続テスト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_discord_bot.py         # 本番環境のテスト
  python test_discord_bot.py --test  # テスト環境のテスト
  python test_discord_bot.py --dev   # 開発環境のテスト
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--test', action='store_true', help='テスト環境でテスト')
    group.add_argument('--dev', action='store_true', help='開発環境でテスト')
    
    args = parser.parse_args()
    
    # 環境を決定
    if args.test:
        env = Environment.TST
    elif args.dev:
        env = Environment.DEV
    else:
        env = Environment.PRD
    
    # .envファイルを読み込み（ローカル開発用）
    load_dotenv()
    
    # テスト実行
    success = asyncio.run(test_discord_bot(env))
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()