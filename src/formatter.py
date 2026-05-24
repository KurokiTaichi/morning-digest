import logging
from datetime import datetime
from .collectors.base import Article
from .config import GENRES, TARGET_ARTICLE_COUNT

logger = logging.getLogger(__name__)


class MessageFormatter:
    """キュレーション済み記事を LINE メッセージに整形"""

    def format_line_message(self, articles: list[Article]) -> str:
        """LINE メッセージを生成"""
        if not articles:
            return "本日配信する記事がありません。"

        # スコア順でソート、高スコアから選ぶ
        scored_articles = [a for a in articles if a.curator_score is not None]
        scored_articles.sort(key=lambda x: x.curator_score, reverse=True)

        # ジャンルごとにバランスを取る
        selected = self._select_balanced_articles(scored_articles, TARGET_ARTICLE_COUNT)

        # メッセージを構築
        message = self._build_message(selected)
        return message

    def _select_balanced_articles(self, articles: list[Article], target_count: int) -> list[Article]:
        """
        ジャンルバランスを考慮して記事を選択
        各ジャンルから最低1件を確保
        """
        if not articles:
            return []

        selected = []
        by_genre = {}

        # ジャンルごとにグループ化
        for article in articles:
            genre = article.genre or "unknown"
            if genre not in by_genre:
                by_genre[genre] = []
            by_genre[genre].append(article)

        # 各ジャンルから1件ずつ選ぶ
        for genre, genre_articles in by_genre.items():
            if genre_articles:
                selected.append(genre_articles[0])

        # まだ足りない場合は高スコア順に追加
        if len(selected) < target_count:
            remaining = [a for a in articles if a not in selected]
            selected.extend(remaining[:target_count - len(selected)])

        return selected[:target_count]

    def _build_message(self, articles: list[Article]) -> str:
        """LINE メッセージを構築"""
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        # ジャンルごとにグループ化
        by_genre = {}
        for article in articles:
            genre = article.genre or "unknown"
            if genre not in by_genre:
                by_genre[genre] = []
            by_genre[genre].append(article)

        lines = []
        lines.append(f"📰 {timestamp} の朝刊")
        lines.append("")

        # ジャンルごとに表示
        for genre_key, genre_config in GENRES.items():
            if genre_key in by_genre:
                genre_articles = by_genre[genre_key]
                emoji = genre_config.get("emoji", "")
                label = genre_config["label"]

                lines.append(f"{emoji} {label}")
                for i, article in enumerate(genre_articles, 1):
                    score_bar = "★" * min(5, article.curator_score // 2) if article.curator_score else ""
                    lines.append(f"{i}. {article.title}")
                    lines.append(f"   {article.curator_summary or ''}")
                    lines.append(f"   🔗 {article.url}")
                    if score_bar:
                        lines.append(f"   {score_bar}")
                lines.append("")

        lines.append("🎯 今日も頑張ろう！")

        return "\n".join(lines)
