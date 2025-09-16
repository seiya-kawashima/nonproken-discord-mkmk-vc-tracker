"""Discord Botクライアント - VC在室メンバーの取得"""  # モジュールの説明

import os  # 環境変数の取得用
from typing import List, Dict, Any  # 型ヒント用
import asyncio  # 非同期処理用
import discord  # Discord API用
from discord.ext import commands  # Botコマンド拡張用
from loguru import logger  # ログ出力用（loguru）


class DiscordVCPoller:
    """Discord VCの在室メンバーを取得するクラス"""  # クラスの説明

    def __init__(self, token: str, allowed_channel_ids: List[str]):
        """初期化処理

        Args:
            token: Discord Botトークン
            allowed_channel_ids: 監視対象のVCチャンネルIDリスト
        """  # 初期化処理の説明
        self.token = token  # Botトークンを保存
        self.allowed_channel_ids = allowed_channel_ids  # 監視対象チャンネルIDを保存
        self.intents = discord.Intents.default()  # デフォルトのIntentsを取得
        self.intents.voice_states = True  # ボイスステート権限を有効化
        self.intents.guilds = True  # ギルド情報権限を有効化
        self.intents.members = True  # メンバー情報権限を有効化
        self.client = None  # クライアントは後で作成
        self.members_data = []  # メンバー情報を格納するリスト

    async def get_vc_members(self) -> List[Dict[str, Any]]:
        """VCに在室しているメンバー情報を取得

        Returns:
            メンバー情報のリスト（vc_name, user_id, user_name含む）
        """  # メソッドの説明
        # メンバーデータを毎回クリア（重複防止）
        self.members_data = []  # リストを初期化

        # 新しいクライアントを作成（古いクライアントは破棄）
        if self.client:  # 既存のクライアントがあれば
            if not self.client.is_closed():  # まだ閉じていなければ
                await self.client.close()  # 閉じる

        self.client = discord.Client(intents=self.intents)  # 新しいクライアントを作成

        @self.client.event
        async def on_ready():
            """Bot接続完了時の処理"""  # イベントハンドラの説明
            logger.info(f"Discordにログインしました：{self.client.user}")  # ログイン成功をログ出力

            for guild in self.client.guilds:  # 全ギルドをループ
                for channel in guild.voice_channels:  # 各ギルドのVCをループ
                    if str(channel.id) in self.allowed_channel_ids:  # 監視対象チャンネルか確認
                        logger.info(f"VCをチェック中: {channel.name} (ID: {channel.id})")  # チェック中のVCをログ出力
                        logger.info(f"  現在のメンバー数: {len(channel.members)}名")  # メンバー数を出力

                        for member in channel.members:  # VCのメンバーをループ
                            member_data = {  # メンバー情報を辞書に格納
                                "vc_name": channel.name,  # VCの名前
                                "user_id": str(member.id),  # ユーザーID（文字列）
                                "user_name": f"{member.name}#{member.discriminator}",  # ユーザー名#識別子
                            }
                            self.members_data.append(member_data)  # リストに追加
                            member_name = member_data.get('user_name', 'unknown')  # ユーザー名を取得
                            logger.info(f"  メンバーを発見: {member_name}")  # メンバー発見をログ出力

            logger.info(f"取得完了: 合計{len(self.members_data)}名のメンバーを取得")  # 取得完了ログ
            await self.client.close()  # クライアント接続を閉じる

        try:
            await self.client.start(self.token)  # Botを起動
        except Exception as e:  # エラー発生時
            logger.error(f"Discordへの接続に失敗しました: {e}")  # エラーをログ出力
            raise  # エラーを再発生
        finally:
            # 確実にクライアントを閉じる
            if self.client and not self.client.is_closed():  # クライアントが開いていれば
                await self.client.close()  # 閉じる

        return self.members_data  # メンバー情報を返す

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""  # メソッドの説明
        return self  # 自身を返す

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""  # メソッドの説明
        if not self.client.is_closed():  # クライアントが閉じていない場合
            await self.client.close()  # クライアントを閉じる