import requests
from datetime import datetime
from .base import BaseCollector, Article
import logging

logger = logging.getLogger(__name__)


class HackerNewsCollector(BaseCollector):
    """Hacker News Top Stories API"""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        super().__init__("hackernews")

    def collect(self) -> list[Article]:
        """Top Stories を取得"""
        try:
            # Top 30 stories ID を取得
            response = requests.get(f"{self.BASE_URL}/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:30]

            articles = []
            for story_id in story_ids:
                try:
                    article_data = requests.get(
                        f"{self.BASE_URL}/item/{story_id}.json",
                        timeout=5
                    ).json()

                    if not article_data or article_data.get("type") != "story":
                        continue

                    # URL がない記事（Ask HN など）はスキップ
                    if "url" not in article_data:
                        continue

                    title = article_data.get("title", "")
                    url = article_data.get("url", "")
                    timestamp = article_data.get("time")

                    article = Article(
                        title=title,
                        url=url,
                        source=self.name,
                        published_at=datetime.fromtimestamp(timestamp) if timestamp else None,
                    )
                    articles.append(article)

                except (requests.RequestException, ValueError, KeyError) as e:
                    logger.warning(f"Error fetching HN story {story_id}: {e}")
                    continue

            logger.info(f"Collected {len(articles)} articles from {self.name}")
            return articles

        except requests.RequestException as e:
            logger.error(f"Error collecting from {self.name}: {e}")
            return []
