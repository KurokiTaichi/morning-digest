import feedparser
from datetime import datetime
from .base import BaseCollector, Article
from ..config import RSS_FEEDS
import logging

logger = logging.getLogger(__name__)


class RSSReader(BaseCollector):
    """複数の RSS フィードを読む"""

    def __init__(self, feeds: dict[str, str] = None):
        super().__init__("rss")
        self.feeds = feeds or RSS_FEEDS

    def collect(self) -> list[Article]:
        """全ての RSS フィードから記事を取得"""
        articles = []

        for feed_name, feed_url in self.feeds.items():
            try:
                feed = feedparser.parse(feed_url)

                if feed.bozo:
                    logger.warning(f"RSS parsing error in {feed_name}: {feed.bozo_exception}")

                for entry in feed.entries[:20]:  # 各フィードから最大20件
                    try:
                        title = entry.get("title", "")
                        url = entry.get("link", "")

                        if not title or not url:
                            continue

                        # 公開日時を取得
                        published_at = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6])

                        article = Article(
                            title=title,
                            url=url,
                            source=feed_name,
                            published_at=published_at,
                        )
                        articles.append(article)

                    except (KeyError, ValueError, AttributeError) as e:
                        logger.warning(f"Error parsing RSS entry in {feed_name}: {e}")
                        continue

                logger.info(f"Collected {len(feed.entries)} articles from {feed_name}")

            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_name}: {e}")
                continue

        logger.info(f"Total RSS articles collected: {len(articles)}")
        return articles
