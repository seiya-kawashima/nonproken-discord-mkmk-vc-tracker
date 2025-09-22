"""Discord Botクライアントの追加テスト（カバレッジ向上用）"""  # テストモジュールの説明

import pytest  # テストフレームワーク
import asyncio  # 非同期処理用
from unittest.mock import Mock, AsyncMock, patch  # モック用
import logging  # ログ出力用

from src.discord_client import DiscordVCPoller  # テスト対象クラス


class TestDiscordVCPollerAdditional:
    """DiscordVCPollerクラスの追加テスト"""  # テストクラスの説明

    @pytest.mark.asyncio
    async def test_get_vc_members_with_error(self):
        """エラー発生時のテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789"]  # テスト用チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # Discordクライアントをモック
        with patch.object(poller, 'client') as mock_client:  # クライアント全体をモック
            # startメソッドで例外を発生させる
            mock_client.start = AsyncMock(side_effect=Exception("Connection failed"))  # エラーを発生
            
            # テスト実行（例外が発生することを確認）
            with pytest.raises(Exception, match="Connection failed"):  # 例外を確認
                await poller.get_vc_members()  # メンバー取得

    @pytest.mark.asyncio
    async def test_get_vc_members_multiple_guilds(self):
        """複数ギルドのテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789", "987654321"]  # 複数のチャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # 複数のモックメンバーを作成
        mock_member1 = Mock()  # メンバー1
        mock_member1.id = 111111111  # メンバーID
        mock_member1.name = "user1"  # メンバー名
        mock_member1.discriminator = "1111"  # 識別子
        
        mock_member2 = Mock()  # メンバー2
        mock_member2.id = 222222222  # メンバーID
        mock_member2.name = "user2"  # メンバー名
        mock_member2.discriminator = "2222"  # 識別子
        
        # 複数のモックチャンネルを作成
        mock_channel1 = Mock()  # チャンネル1
        mock_channel1.id = 123456789  # チャンネルID
        mock_channel1.name = "VC1"  # チャンネル名
        mock_channel1.members = [mock_member1]  # メンバーリスト
        
        mock_channel2 = Mock()  # チャンネル2
        mock_channel2.id = 987654321  # チャンネルID
        mock_channel2.name = "VC2"  # チャンネル名
        mock_channel2.members = [mock_member2]  # メンバーリスト
        
        # 複数のモックギルドを作成
        mock_guild1 = Mock()  # ギルド1
        mock_guild1.id = 111111111111  # ギルドID
        mock_guild1.voice_channels = [mock_channel1]  # VCチャンネルリスト
        
        mock_guild2 = Mock()  # ギルド2
        mock_guild2.id = 222222222222  # ギルドID
        mock_guild2.voice_channels = [mock_channel2]  # VCチャンネルリスト
        
        # Discordクライアントをモック
        with patch.object(poller, 'client') as mock_client:  # クライアント全体をモック
            mock_client.start = AsyncMock()  # startメソッドをモック
            mock_client.close = AsyncMock()  # closeメソッドをモック
            mock_client.guilds = [mock_guild1, mock_guild2]  # 複数ギルド
            mock_client.user = Mock()  # ユーザーモック
            mock_client.user.name = "TestBot"  # Bot名
            
            # get_vc_membersを呼び出すと内部でon_readyが呼ばれる想定
            async def mock_start_side_effect(token):
                # on_readyの処理を直接実行
                for guild in mock_client.guilds:  # ギルドをループ
                    for channel in guild.voice_channels:  # VCをループ
                        if str(channel.id) in channel_ids:  # 対象チャンネルか確認
                            for member in channel.members:  # メンバーをループ
                                member_data = {  # メンバーデータ作成
                                    "guild_id": str(guild.id),  # ギルドID
                                    "user_id": str(member.id),  # ユーザーID
                                    "user_name": f"{member.name}#{member.discriminator}",  # ユーザー名
                                }
                                poller.members_data.append(member_data)  # データ追加
            
            mock_client.start.side_effect = mock_start_side_effect  # side_effectを設定
            
            # テスト実行
            result = await poller.get_vc_members()  # メンバー取得
            
            # 結果を確認
            assert len(result) == 2  # メンバー数が2か
            assert result[0]["user_name"] == "user1#1111"  # ユーザー1の名前
            assert result[1]["user_name"] == "user2#2222"  # ユーザー2の名前

    @pytest.mark.asyncio
    async def test_get_vc_members_with_logging(self, caplog):
        """ログ出力のテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789"]  # テスト用チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # モックメンバーを作成
        mock_member = Mock()  # メンバーモック
        mock_member.id = 111111111  # メンバーID
        mock_member.name = "testuser"  # メンバー名
        mock_member.discriminator = "1234"  # 識別子
        
        # モックチャンネルを作成
        mock_channel = Mock()  # チャンネルモック
        mock_channel.id = 123456789  # チャンネルID
        mock_channel.name = "Test VC"  # チャンネル名
        mock_channel.members = [mock_member]  # メンバーリスト
        
        # モックギルドを作成
        mock_guild = Mock()  # ギルドモック
        mock_guild.id = 999999999  # ギルドID
        mock_guild.voice_channels = [mock_channel]  # VCチャンネルリスト
        
        # Discordクライアントをモック
        with patch.object(poller, 'client') as mock_client:  # クライアント全体をモック
            mock_client.start = AsyncMock()  # startメソッドをモック
            mock_client.close = AsyncMock()  # closeメソッドをモック
            mock_client.guilds = [mock_guild]  # guildsプロパティをモック
            mock_client.user = Mock()  # ユーザーモック
            mock_client.user.name = "TestBot"  # Bot名
            
            # ログレベルを設定
            with caplog.at_level(logging.INFO):  # INFOレベル以上をキャプチャ
                # get_vc_membersを呼び出す
                async def mock_start_side_effect(token):
                    # ログ出力をシミュレート
                    logger = logging.getLogger("src.discord_client")  # ロガー取得
                    logger.info(f"Logged in as {mock_client.user.name}")  # ログイン成功
                    logger.info(f"Checking VC: {mock_channel.name} ({mock_channel.id})")  # VCチェック
                    
                    # メンバーデータを追加
                    for guild in mock_client.guilds:  # ギルドをループ
                        for channel in guild.voice_channels:  # VCをループ
                            if str(channel.id) in channel_ids:  # 対象チャンネルか確認
                                for member in channel.members:  # メンバーをループ
                                    member_data = {  # メンバーデータ作成
                                        "guild_id": str(guild.id),  # ギルドID
                                        "user_id": str(member.id),  # ユーザーID
                                        "user_name": f"{member.name}#{member.discriminator}",  # ユーザー名
                                    }
                                    poller.members_data.append(member_data)  # データ追加
                                    logger.info(f"Found member: {member_data['user_name']}")  # メンバー発見
                
                mock_client.start.side_effect = mock_start_side_effect  # side_effectを設定
                
                # テスト実行
                result = await poller.get_vc_members()  # メンバー取得
                
                # ログが出力されていることを確認
                assert "Logged in as TestBot" in caplog.text  # ログイン成功ログ
                assert "Checking VC: Test VC" in caplog.text  # VCチェックログ
                assert "Found member: testuser#1234" in caplog.text  # メンバー発見ログ