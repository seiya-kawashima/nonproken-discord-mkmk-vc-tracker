# Discord VC Tracker プロジェクトルール

## 📋 ドキュメント管理ルール

### 必須ドキュメント更新
開発・機能追加・修正を行った際は、必ず以下のドキュメントを作成・更新すること:

1. **README.md** - プロジェクト概要とセットアップ手順を更新
2. **docs/overview.md** - システム全体の概要を更新
3. **個別仕様書** - 各モジュール/機能ごとの詳細仕様書を作成・更新
   - 例: `docs/specs/discord_client_spec.md`
   - 例: `docs/specs/sheets_client_spec.md`
   - 例: `docs/specs/slack_notifier_spec.md`

### ドキュメント更新タイミング
- **新機能追加時**: 実装前に仕様書作成 → 実装 → ドキュメント更新
- **バグ修正時**: 修正内容を仕様書に反映
- **リファクタリング時**: 変更点を仕様書に反映

### ドキュメント構成
```
project/
├── README.md                    # プロジェクト概要
├── docs/
│   ├── specification.md        # 全体仕様書
│   ├── specs/                  # 個別仕様書
│   │   ├── discord_client_spec.md
│   │   ├── sheets_client_spec.md
│   │   └── slack_notifier_spec.md
│   └── todo-archive.md         # 完了TODOアーカイブ
└── .claude/
    └── project_rules.md        # このファイル
```

## 💻 コーディング規約

### Python開発
- **バージョン**: Python 3.11+
- **フォーマッター**: Black
- **リンター**: Flake8
- **型チェック**: mypy

### コメント規約
- すべてのコードに日本語の行末コメントを追加
- 初心者にも理解できる平易な説明を心がける
- 複雑なロジックには詳細な説明を追加

### 命名規則
- **クラス名**: PascalCase (例: `DiscordVCPoller`)
- **関数名**: snake_case (例: `get_vc_members`)
- **定数**: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`)
- **変数**: snake_case (例: `user_name`)

## 🔒 セキュリティ

### 認証情報の取り扱い
- トークンや認証情報は**絶対にコミットしない**
- 環境変数またはGitHub Secretsで管理
- `.gitignore`に必ず追加

### ログ出力
- 認証情報は**マスキング**して出力
- 個人情報は最小限に留める

## 🧪 テスト

### テスト作成ルール
- 新機能追加時は必ずユニットテストを作成
- テストカバレッジ80%以上を目標
- モックを活用して外部依存を排除

### テスト実行
```bash
# ユニットテスト実行
pytest tests/

# カバレッジ確認
pytest --cov=src tests/
```

## 📝 コミットメッセージ

### フォーマット
```
<type>: <subject>

<body>
```

### タイプ
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: コード整形
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: ビルド・設定変更

### 例
```
feat: Discord VCメンバー取得機能を追加

- DiscordVCPollerクラスを実装
- 指定VCのメンバーリストを取得
- エラーハンドリングとリトライ機能を追加
```

## 🚀 デプロイ

### GitHub Actions
- `main`ブランチへのマージで自動デプロイ
- Pull Request時にテスト自動実行
- Secrets設定を事前に確認

## 📊 モニタリング

### ログレベル
- **本番環境**: INFO以上
- **開発環境**: DEBUG以上

### アラート条件
- 3回連続でエラー発生
- API Rate Limit到達
- 認証エラー発生