import os
from dotenv import load_dotenv

load_dotenv()

# 環境変数の読み込み
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

# ジャンル定義
GENRES = {
    "ai_tech": {
        "label": "AI・テクノロジー",
        "keywords": ["AI", "LLM", "machine learning", "GPT", "Claude", "agent", "neural", "deep learning"],
        "sources": ["hackernews", "rss_techcrunch", "rss_aiweekly"],
        "emoji": "🤖",
    },
    "pm_product": {
        "label": "PM・プロダクトスキル",
        "keywords": ["product management", "roadmap", "OKR", "user research", "ux", "strategy"],
        "sources": ["reddit_pm", "rss_lenny"],
        "emoji": "📊",
    },
    "business": {
        "label": "ビジネス・書籍・動画",
        "keywords": ["startup", "leadership", "book", "strategy", "entrepreneur"],
        "sources": ["hackernews", "reddit_entrepreneur"],
        "emoji": "📚",
    },
    "finance": {
        "label": "株・仮想通貨・インデックス",
        "sources": ["coingecko", "yahoo_finance"],
        "emoji": "💹",
    },
}

# RSS フィード定義
RSS_FEEDS = {
    "rss_techcrunch": "https://techcrunch.com/feed/",
    "rss_aiweekly": "https://aiweekly.co/issues.rss",
    "rss_lenny": "https://www.lennysnewsletter.com/feed",
}

# 記事収集の制限
MAX_ARTICLES_PER_SOURCE = 20  # 各ソースから最大何件取得するか
TARGET_ARTICLE_COUNT = 8  # 最終的に LINE に載せる記事数
MAX_ARTICLES_BEFORE_CURATOR = 40  # Claude に渡す前の最大件数

def validate_env():
    """起動時に必須環境変数をチェック"""
    required = ["ANTHROPIC_API_KEY", "LINE_CHANNEL_ACCESS_TOKEN", "LINE_USER_ID"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(f"必須環境変数が未設定です: {', '.join(missing)}")
