# 🌅 Morning Digest

毎朝 LINE に パーソナライズされた情報配信を自動化するシステム

## ✨ 特徴

- **自動キュレーション** — Claude Haiku がリアルタイムで最適な記事を選別
- **複数情報源** — Hacker News + RSS フィード（TechCrunch, AI Weekly, Lenny's）
- **カード型UI** — LINE フレックスメッセージで見やすく表示
- **完全自動化** — GitHub Actions で毎朝 7:00（JST）に配信
- **格安運用** — 月額コスト約 $0.05（Claude Haiku + GitHub Actions）
- **セキュリティ重視** — API キーは暗号化 + GitHub Secrets で管理

## 📋 配信内容

毎朝、以下のジャンルから最新情報を自動配信：

| ジャンル | 情報源 |
|---------|--------|
| 🤖 AI・テクノロジー | Hacker News, TechCrunch, AI Weekly |
| 📊 PM・プロダクトスキル | Lenny's Newsletter, Reddit |
| 📚 ビジネス・書籍・動画 | Hacker News, Reddit |
| 💹 株・仮想通貨・インデックス | 予定中（Phase 2） |

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/KurokiTaichi/morning-digest.git
cd morning-digest
```

### 2. 環境変数を設定

```bash
cp .env.example .env
```

`.env` に以下の情報を入力：

```env
ANTHROPIC_API_KEY=sk-ant-...
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_USER_ID=U...
```

### 3. 依存関係をインストール

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. ローカルテスト

```bash
python -m src.main
```

## 📱 LINE への配信設定

### LINE Messaging API チャネル作成

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. 新規チャネルを作成（Messaging API）
3. **Channel access token** をコピー → `.env` に入力
4. **User ID** を取得 → `.env` に入力

## 🔧 GitHub Actions での自動実行

### Secrets に登録

GitHub リポジトリの **Settings → Secrets and variables** に以下を登録：

```
ANTHROPIC_API_KEY
LINE_CHANNEL_ACCESS_TOKEN
LINE_USER_ID
```

### 自動配信スケジュール

毎朝 **7:00（JST）** に自動実行

手動実行したい場合：
```bash
gh workflow run morning_digest.yml -R <owner>/<repo>
```

## 📊 配信メッセージ例

```
┌─────────────────────────────────┐
│ 🤖 AI・テクノロジー               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ New AI Model Beats GPT-4         │
│                                  │
│ OpenAI が新型AIモデルを発表。    │
│ 自動推論機能が大幅改善され、    │
│ 従来のモデルより35%高速化。    │
│ 複雑な問題解決能力も向上し...   │
│                                  │
│ 📅 2時間前                       │
│ ⭐⭐⭐⭐⭐                      │
│                                  │
│ ┌──────────────────────────┐   │
│ │    記事を読む              │   │
│ └──────────────────────────┘   │
└─────────────────────────────────┘
```

## 🛠️ アーキテクチャ

```
Hacker News API + RSS フィード
        ↓
【収集】 最大90記事を収集
        ↓
【フィルタ】 24時間以内、重複除去 → 最大40件
        ↓
【キュレーション】 Claude Haiku で評価・日本語要約生成
        ↓
【選別】 スコア上位、ジャンルバランス → 8件
        ↓
【フォーマット】 フレックスメッセージに整形
        ↓
【配信】 LINE Messaging API → ユーザーのLINE
```

## 💰 コスト試算

- **Claude API（Haiku）** — 月額 ~$0.05
- **LINE Messaging API** — 月額 $0（無料枠内）
- **GitHub Actions** — 月額 $0（無料枠内）

**月間総コスト：約 $0.05**

## 📚 API キー取得方法

### ANTHROPIC_API_KEY

1. [console.anthropic.com](https://console.anthropic.com) にログイン
2. **API keys** → **Create Key**
3. トークンをコピー

### LINE_CHANNEL_ACCESS_TOKEN & LINE_USER_ID

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. Messaging API チャネルを選択
3. **Channel access token** をコピー
4. チャネル設定で **User ID** を確認

## 🔐 セキュリティ

- API キーは `.env`（`.gitignore` 対象）で管理
- GitHub Secrets で暗号化保管
- 本番環境（GitHub Actions）では環境変数として注入
- ローカル開発時は `~/.secrets/` で暗号化ストレージを活用可能

## 🚀 今後の拡張（Phase 2）

- [ ] 🪙 仮想通貨価格（CoinGecko API）
- [ ] 📈 株価情報（Yahoo Finance）
- [ ] 🔴 Reddit API 統合
- [ ] 🇯🇵 日本語フィード追加
- [ ] 📊 ジャンル別カスタマイズ

## 📝 設定カスタマイズ

### `src/config.py`

```python
# ジャンル定義
GENRES = {
    "ai_tech": {...},
    "pm_product": {...},
    ...
}

# RSS フィード
RSS_FEEDS = {
    "rss_techcrunch": "https://...",
    ...
}

# 配信設定
TARGET_ARTICLE_COUNT = 8  # 配信する記事数
MAX_ARTICLES_BEFORE_CURATOR = 40  # Claude に評価させる最大件数
```

## 🐛 トラブルシューティング

### LINE にメッセージが届かない

- API キーが正しいか確認
- LINE チャネルが有効になっているか確認
- User ID が正しいか確認

### Claude API エラーが出る

- `ANTHROPIC_API_KEY` が正しく設定されているか確認
- アカウントの利用限度額を確認

## 📄 ライセンス

MIT

## 🙏 謝辞

- [Claude API](https://anthropic.com/) — AI キュレーション
- [LINE Messaging API](https://developers.line.biz/) — 配信インフラ
- [Hacker News API](https://github.com/HackerNews/API) — ニュースソース
