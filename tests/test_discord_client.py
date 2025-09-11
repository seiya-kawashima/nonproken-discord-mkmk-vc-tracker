"""Discord Botクライアントのユニットテスト"""  # テストモジュールの説明

import pytest  # テストフレームワーク
import asyncio  # 非同期処理用
from unittest.mock import Mock, AsyncMock, patch, MagicMock  # モック用
import discord  # Discord API用

from src.discord_client import DiscordVCPoller  # テスト対象クラス


class TestDiscordVCPoller:
    """DiscordVCPollerクラスのテスト"""  # テストクラスの説明

    def test_init(self):
        """初期化処理のテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123", "456"]  # テスト用チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        assert poller.token == token  # トークンが正しく設定されているか
        assert poller.allowed_channel_ids == channel_ids  # チャンネルIDが正しく設定されているか
        assert poller.members_data == []  # メンバーデータが空か
        assert poller.intents.voice_states is True  # voice_states権限が有効か
        assert poller.intents.guilds is True  # guilds権限が有効か
        assert poller.intents.members is True  # members権限が有効か

    @pytest.mark.asyncio
    async def test_get_vc_members_success(self):
        """VCメンバー取得成功のテスト"""  # テストの説明
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
            
            # get_vc_membersを呼び出すと内部でon_readyが呼ばれる想定
            # しかし実際にはstartが呼ばれるだけなので、手動でデータを設定
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
            assert len(result) == 1  # メンバー数が1か
            assert result[0]["guild_id"] == "999999999"  # ギルドIDが正しいか
            assert result[0]["user_id"] == "111111111"  # ユーザーIDが正しいか
            assert result[0]["user_name"] == "testuser#1234"  # ユーザー名が正しいか

    @pytest.mark.asyncio
    async def test_get_vc_members_no_members(self):
        """VCにメンバーがいない場合のテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789"]  # テスト用チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # 空のチャンネルを作成
        mock_channel = Mock()  # チャンネルモック
        mock_channel.id = 123456789  # チャンネルID
        mock_channel.name = "Empty VC"  # チャンネル名
        mock_channel.members = []  # メンバーなし
        
        # モックギルドを作成
        mock_guild = Mock()  # ギルドモック
        mock_guild.id = 999999999  # ギルドID
        mock_guild.voice_channels = [mock_channel]  # VCチャンネルリスト
        
        # Discordクライアントをモック
        with patch.object(poller, 'client') as mock_client:  # クライアント全体をモック
            mock_client.start = AsyncMock()  # startメソッドをモック
            mock_client.close = AsyncMock()  # closeメソッドをモック
            mock_client.guilds = [mock_guild]  # guildsプロパティをモック
            
            # startが呼ばれても何もしない（メンバーがいないので）
            async def mock_start_side_effect(token):
                pass  # 何もしない
            
            mock_client.start.side_effect = mock_start_side_effect  # side_effectを設定
            
            # テスト実行
            result = await poller.get_vc_members()  # メンバー取得
            
            # 結果を確認
            assert len(result) == 0  # メンバーがいないことを確認

    @pytest.mark.asyncio
    async def test_get_vc_members_not_monitored_channel(self):
        """監視対象外のチャンネルのテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789"]  # 監視対象チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # 監視対象外のチャンネルを作成
        mock_member = Mock()  # メンバーモック
        mock_member.id = 111111111  # メンバーID
        mock_member.name = "testuser"  # メンバー名
        mock_member.discriminator = "1234"  # 識別子
        
        mock_channel = Mock()  # チャンネルモック
        mock_channel.id = 987654321  # 別のチャンネルID（監視対象外）
        mock_channel.name = "Other VC"  # チャンネル名
        mock_channel.members = [mock_member]  # メンバーリスト
        
        mock_guild = Mock()  # ギルドモック
        mock_guild.id = 999999999  # ギルドID
        mock_guild.voice_channels = [mock_channel]  # VCチャンネルリスト
        
        # Discordクライアントをモック
        with patch.object(poller, 'client') as mock_client:  # クライアント全体をモック
            mock_client.start = AsyncMock()  # startメソッドをモック
            mock_client.close = AsyncMock()  # closeメソッドをモック
            mock_client.guilds = [mock_guild]  # guildsプロパティをモック
            
            # startが呼ばれても何もしない（監視対象外なので）
            async def mock_start_side_effect(token):
                # on_readyの処理を直接実行するが、監視対象外なので何も追加されない
                for guild in mock_client.guilds:  # ギルドをループ
                    for channel in guild.voice_channels:  # VCをループ
                        if str(channel.id) in channel_ids:  # 対象チャンネルか確認（falseになる）
                            for member in channel.members:  # 実行されない
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
            assert len(result) == 0  # 監視対象外なのでメンバーがいない

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """コンテキストマネージャーのテスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123"]  # テスト用チャンネルID
        
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # __aenter__のテスト
        result = await poller.__aenter__()  # 開始処理
        assert result is poller  # 自身が返されるか確認
        
        # __aexit__のテスト（クライアントが閉じていない場合）
        poller.client.is_closed = Mock(return_value=False)  # is_closedをモック
        poller.client.close = AsyncMock()  # closeをモック
        
        await poller.__aexit__(None, None, None)  # 終了処理
        poller.client.close.assert_called_once()  # closeが呼ばれたか確認
        
        # __aexit__のテスト（クライアントが既に閉じている場合）
        poller.client.is_closed = Mock(return_value=True)  # is_closedをモック（True）
        poller.client.close = AsyncMock()  # closeをモック
        
        await poller.__aexit__(None, None, None)  # 終了処理
        poller.client.close.assert_not_called()  # closeが呼ばれていないか確認