import logging
import sys
from datetime import datetime

from .config import validate_env, MAX_ARTICLES_BEFORE_CURATOR
from .collectors.hackernews import HackerNewsCollector
from .collectors.rss_reader import RSSReader
from .curator import ArticleCurator
from .formatter import MessageFormatter
from .line_sender import LineSender
from .collectors.base import Article

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def deduplicate_articles(articles: list[Article]) -> list[Article]:
    """URL の重複をチェック、保持"""
    seen_urls = set()
    unique = []
    for article in articles:
        if article.url not in seen_urls:
            seen_urls.add(article.url)
            unique.append(article)
    logger.info(f"Deduplicated: {len(articles)} -> {len(unique)} articles")
    return unique


def run_morning_digest():
    """朝刊パイプラインを実行"""
    logger.info("=" * 50)
    logger.info("Morning Digest Started")
    logger.info("=" * 50)

    try:
        # 環境変数チェック
        validate_env()
        logger.info("Environment variables validated")

        # ステップ1: 各ソースから記事を収集
        logger.info("Step 1: Collecting articles from sources...")
        all_articles = []

        collectors = [
            HackerNewsCollector(),
            RSSReader(),
        ]

        for collector in collectors:
            try:
                articles = collector.collect()
                logger.info(f"{collector.name}: collected {len(articles)} articles")
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error in {collector.name}: {e}")
                continue

        logger.info(f"Total articles collected: {len(all_articles)}")

        if not all_articles:
            logger.warning("No articles collected. Aborting.")
            LineSender.send_notification(
                "Morning Digest Error",
                "No articles could be collected from any source."
            )
            return

        # ステップ2: 24時間以内の記事に絞る
        logger.info("Step 2: Filtering recent articles (24h)...")
        if all_articles and all_articles[0].published_at:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=24)
            recent = [a for a in all_articles if a.published_at and a.published_at > cutoff]
            all_articles = recent

        logger.info(f"After filtering: {len(all_articles)} articles")

        # ステップ3: 重複を除去
        logger.info("Step 3: Deduplicating articles...")
        all_articles = deduplicate_articles(all_articles)

        # ステップ4: Claude に渡す前に件数を制限
        logger.info(f"Step 4: Limiting to {MAX_ARTICLES_BEFORE_CURATOR} articles for curator...")
        all_articles = all_articles[:MAX_ARTICLES_BEFORE_CURATOR]
        logger.info(f"Final articles for curator: {len(all_articles)}")

        # ステップ5: Claude Haiku で一括キュレーション
        logger.info("Step 5: Curating with Claude Haiku...")
        curator = ArticleCurator()
        curated_articles = curator.curate(all_articles)
        logger.info(f"Curated: {len(curated_articles)} articles")

        # ステップ6: メッセージをフォーマット
        logger.info("Step 6: Formatting message...")
        formatter = MessageFormatter()
        message = formatter.format_line_message(curated_articles)

        # ステップ7: LINE に送信
        logger.info("Step 7: Sending to LINE...")
        success = LineSender.send_message(message)

        if success:
            logger.info("✅ Morning Digest completed successfully!")
        else:
            logger.error("❌ Failed to send message to LINE")
            return False

        logger.info("=" * 50)
        logger.info("Morning Digest Finished")
        logger.info("=" * 50)
        return True

    except Exception as e:
        logger.error(f"Fatal error in morning digest: {e}", exc_info=True)
        try:
            LineSender.send_notification(
                "Morning Digest Fatal Error",
                f"An unexpected error occurred: {str(e)}"
            )
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")
        return False


if __name__ == "__main__":
    success = run_morning_digest()
    sys.exit(0 if success else 1)
