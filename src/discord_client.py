"""Discord Botクライアント - VC在室メンバーの取得"""  # モジュールの説明

import os  # 環境変数の取得用
from typing import List, Dict, Any  # 型ヒント用
import asyncio  # 非同期処理用
import discord  # Discord API用
from discord.ext import commands  # Botコマンド拡張用
from loguru import logger  # ログ出力用（loguru）


class DiscordVCPoller:
    """Discord VCの在室メンバーを取得するクラス"""  # クラスの説明

    def __init__(self, token: str, allowed_channel_ids: List[str], mask_usernames: bool = False, excluded_users: List[str] = None):
        """初期化処理

        Args:
            token: Discord Botトークン
            allowed_channel_ids: 監視対象のVCチャンネルIDリスト
            mask_usernames: ユーザー名をマスキングするかどうか（本番・テスト環境用）
            excluded_users: 記録から除外するユーザー名のリスト
        """  # 初期化処理の説明
        self.token = token  # Botトークンを保存
        self.allowed_channel_ids = allowed_channel_ids  # 監視対象チャンネルIDを保存
        self.mask_usernames = mask_usernames  # ユーザー名マスキング設定
        self.excluded_users = excluded_users or []  # 除外ユーザーリスト（デフォルト空リスト）
        self.intents = discord.Intents.default()  # デフォルトのIntentsを取得
        self.intents.voice_states = True  # ボイスステート権限を有効化
        self.intents.guilds = True  # ギルド情報権限を有効化
        self.intents.members = True  # メンバー情報権限を有効化
        self.client = None  # クライアントは後で作成
        self.members_data = []  # メンバー情報を格納するリスト

    def _mask_username(self, username: str) -> str:
        """ユーザー名をマスキング（最初の3文字のみ表示）

        Args:
            username: 元のユーザー名

        Returns:
            マスキングされたユーザー名
        """
        if not self.mask_usernames or not username:
            return username  # マスキング不要または空文字の場合はそのまま返す

        if len(username) <= 3:
            return username + "***"  # 3文字以下の場合は全体表示+マスク
        else:
            return username[:3] + "*" * (len(username) - 3)  # 最初の3文字+残りをマスク

    async def get_vc_members(self) -> List[Dict[str, Any]]:
        """VCに在室しているメンバー情報を取得

        Returns:
            メンバー情報のリスト（vc_name, user_id, user_name含む）
        """  # メソッドの説明
        # メンバーデータを毎回クリア（重複防止）
        self.members_data = []  # リストを初期化

        # 新しいクライアントを作成
        self.client = discord.Client(intents=self.intents)  # 新しいクライアントを作成

        try:
            # データ取得完了フラグ
            data_collected = asyncio.Event()  # 非同期イベント

            @self.client.event
            async def on_ready():
                """Bot接続完了時の処理"""  # イベントハンドラの説明
                try:
                    logger.info(f"Discordにログインしました：{self.client.user}")  # ログイン成功をログ出力

                    for guild in self.client.guilds:  # 全ギルドをループ
                        for channel in guild.voice_channels:  # 各ギルドのVCをループ
                            if str(channel.id) in self.allowed_channel_ids:  # 監視対象チャンネルか確認
                                logger.info(f"VCをチェック中: {channel.name} (ID: {channel.id})")  # チェック中のVCをログ出力
                                logger.info(f"  現在のメンバー数: {len(channel.members)}名")  # メンバー数を出力

                                for member in channel.members:  # VCのメンバーをループ
                                    # 除外ユーザーをスキップ
                                    if member.name in self.excluded_users:  # 除外リストに含まれている場合
                                        masked_name = self._mask_username(member.name)  # ログ用にマスキング
                                        logger.info(f"  メンバーをスキップ（除外対象）: {masked_name}")  # 除外ログ
                                        continue  # 次のメンバーへ

                                    member_data = {  # メンバー情報を辞書に格納
                                        "vc_name": channel.name,  # VCの名前
                                        "user_id": str(member.id),  # ユーザーID（文字列）
                                        "user_name": member.name,  # ユーザー名（識別番号は新システムでは不要）
                                        "display_name": member.display_name,  # サーバーでの表示名（ニックネーム）
                                    }
                                    self.members_data.append(member_data)  # リストに追加
                                    member_name = member_data.get('user_name', 'unknown')  # ユーザー名を取得
                                    masked_name = self._mask_username(member_name)  # ログ用にマスキング
                                    logger.info(f"  メンバーを発見: {masked_name}")  # メンバー発見をログ出力（マスキング済み）

                    logger.info(f"取得完了: 合計{len(self.members_data)}名のメンバーを取得")  # 取得完了ログ
                finally:
                    data_collected.set()  # データ取得完了を通知
                    await self.client.close()  # クライアント接続を閉じる

            # Botを起動（非同期タスクとして）
            bot_task = asyncio.create_task(self.client.start(self.token))  # タスク作成

            # データ取得完了まで待機（最大30秒）
            try:
                await asyncio.wait_for(data_collected.wait(), timeout=30.0)  # タイムアウト付き待機
            except asyncio.TimeoutError:  # タイムアウト時
                logger.error("Discord接続がタイムアウトしました")  # エラーログ
                raise

        except Exception as e:  # エラー発生時
            logger.error(f"Discordへの接続に失敗しました: {e}")  # エラーをログ出力
            raise  # エラーを再発生
        finally:
            # 確実にクライアントをクリーンアップ
            if self.client:  # クライアントが存在すれば
                if not self.client.is_closed():  # まだ閉じていなければ
                    await self.client.close()  # 閉じる
                # HTTPセッションも確実に閉じる
                if hasattr(self.client, 'http') and self.client.http:  # HTTPセッションがあれば
                    await self.client.http.close()  # セッションを閉じる

        return self.members_data  # メンバー情報を返す

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""  # メソッドの説明
        return self  # 自身を返す

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""  # メソッドの説明
        if not self.client.is_closed():  # クライアントが閉じていない場合
            await self.client.close()  # クライアントを閉じる