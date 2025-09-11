"""Discord Botクライアントの実際のon_readyテスト"""  # テストモジュールの説明

import pytest  # テストフレームワーク
import asyncio  # 非同期処理用
from unittest.mock import Mock, AsyncMock, patch, MagicMock  # モック用
import logging  # ログ出力用

from src.discord_client import DiscordVCPoller  # テスト対象クラス


class TestDiscordVCPollerReal:
    """DiscordVCPollerの実際のon_readyイベントテスト"""  # テストクラスの説明

    @pytest.mark.asyncio
    @patch('src.discord_client.discord.Client')
    async def test_on_ready_event(self, mock_client_class):
        """on_readyイベントの実行テスト"""  # テストの説明
        token = "test_token"  # テスト用トークン
        channel_ids = ["123456789"]  # テスト用チャンネルID
        
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
        
        # モッククライアント作成
        mock_client_instance = Mock()  # クライアントインスタンス
        mock_client_instance.guilds = [mock_guild]  # ギルドリスト
        mock_client_instance.user = Mock()  # ユーザーモック
        mock_client_instance.user.name = "TestBot"  # Bot名
        mock_client_instance.close = AsyncMock()  # closeメソッド
        
        # startメソッドをモック（on_readyを手動実行）
        async def mock_start(token):
            # on_readyイベントハンドラを取得して実行
            on_ready = None  # on_readyハンドラ
            for attr_name in dir(mock_client_instance):  # 属性をループ
                attr = getattr(mock_client_instance, attr_name)  # 属性取得
                if hasattr(attr, '__name__') and attr.__name__ == 'on_ready':  # on_readyか確認
                    on_ready = attr  # ハンドラを保存
                    break  # ループ終了
            
            if on_ready:  # ハンドラがある場合
                await on_ready()  # 実行
        
        mock_client_instance.start = mock_start  # startメソッドを設定
        mock_client_class.return_value = mock_client_instance  # インスタンスを返す
        
        # DiscordVCPollerインスタンス作成
        poller = DiscordVCPoller(token, channel_ids)  # インスタンス作成
        
        # on_readyの実際のコードを実行
        @poller.client.event
        async def on_ready():
            """Bot接続完了時の処理"""  # イベントハンドラの説明
            logger = logging.getLogger("src.discord_client")  # ロガー取得
            logger.info(f"Logged in as {poller.client.user}")  # ログイン成功をログ出力

            for guild in poller.client.guilds:  # 全ギルドをループ
                for channel in guild.voice_channels:  # 各ギルドのVCをループ
                    if str(channel.id) in poller.allowed_channel_ids:  # 監視対象チャンネルか確認
                        logger.info(f"Checking VC: {channel.name} ({channel.id})")  # チェック中のVCをログ出力
                        
                        for member in channel.members:  # VCのメンバーをループ
                            member_data = {  # メンバー情報を辞書に格納
                                "guild_id": str(guild.id),  # ギルドID（文字列）
                                "user_id": str(member.id),  # ユーザーID（文字列）
                                "user_name": f"{member.name}#{member.discriminator}",  # ユーザー名#識別子
                            }
                            poller.members_data.append(member_data)  # リストに追加
                            logger.info(f"Found member: {member_data['user_name']}")  # メンバー発見をログ出力

            await poller.client.close()  # クライアント接続を閉じる
        
        # クライアントのモック設定を更新
        poller.client.guilds = [mock_guild]  # ギルドを設定
        poller.client.user = mock_client_instance.user  # ユーザーを設定
        poller.client.close = mock_client_instance.close  # closeメソッドを設定
        
        # on_readyを直接実行
        await on_ready()  # on_readyイベントを実行
        
        # アサーション
        assert len(poller.members_data) == 1  # メンバー数が1か
        assert poller.members_data[0]["guild_id"] == "999999999"  # ギルドIDが正しいか
        assert poller.members_data[0]["user_id"] == "111111111"  # ユーザーIDが正しいか
        assert poller.members_data[0]["user_name"] == "testuser#1234"  # ユーザー名が正しいか
        mock_client_instance.close.assert_called_once()  # closeが呼ばれたか