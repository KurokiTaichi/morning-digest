import json
import logging
from datetime import datetime
from .collectors.base import Article
from .config import GENRES, TARGET_ARTICLE_COUNT

logger = logging.getLogger(__name__)


class MessageFormatter:
    """キュレーション済み記事を LINE フレックスメッセージに整形"""

    def format_line_message(self, articles: list[Article]) -> dict:
        """LINE フレックスメッセージ（Flex Message）を生成"""
        if not articles:
            return {
                "type": "text",
                "text": "本日配信する記事がありません。"
            }

        scored_articles = [a for a in articles if a.curator_score is not None]
        scored_articles.sort(key=lambda x: x.curator_score, reverse=True)

        selected = self._select_balanced_articles(scored_articles, TARGET_ARTICLE_COUNT)

        return self._build_flex_message(selected)

    def _get_country_flag(self, source: str) -> str:
        """source から国フラグを取得"""
        source_lower = source.lower()

        # 日本のソース
        if any(jp in source_lower for jp in ["japan", "jp", "日本"]):
            return "🇯🇵"

        # 英語圏のソース（デフォルト）
        return "🇺🇸"

    def _format_date(self, published_at, source: str = "") -> str:
        """記事の作成日時をフォーマット（国フラグ付き）"""
        if not published_at:
            country = self._get_country_flag(source) if source else ""
            return f"📅 日時不明 {country}".strip()

        from datetime import datetime, timezone

        # published_at がタイムゾーン非対応の場合、UTC として扱う
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = now - published_at

        country = self._get_country_flag(source) if source else ""

        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return f"📅 {minutes}分前 {country}".strip()
            return f"📅 {hours}時間前 {country}".strip()
        elif diff.days == 1:
            return f"📅 1日前 {country}".strip()
        else:
            return f"📅 {published_at.strftime('%Y年%m月%d日')} {country}".strip()

    def _select_balanced_articles(self, articles: list[Article], target_count: int) -> list[Article]:
        """ジャンルバランスを考慮して記事を選択"""
        if not articles:
            return []

        selected = []
        by_genre = {}

        for article in articles:
            genre = article.genre or "unknown"
            if genre not in by_genre:
                by_genre[genre] = []
            by_genre[genre].append(article)

        for genre, genre_articles in by_genre.items():
            if genre_articles:
                selected.append(genre_articles[0])

        if len(selected) < target_count:
            remaining = [a for a in articles if a not in selected]
            selected.extend(remaining[:target_count - len(selected)])

        return selected[:target_count]

    def _build_flex_message(self, articles: list[Article]) -> dict:
        """LINE フレックスメッセージを構築"""
        timestamp = datetime.now().strftime("%m月%d日")

        bubbles = []
        for article in articles:
            genre_config = GENRES.get(article.genre, {})
            emoji = genre_config.get("emoji", "📄")
            genre_label = genre_config.get("label", "その他")

            # スコアを星表示
            score = article.curator_score or 0
            stars = "⭐" * min(5, score // 2)

            body_contents = [
                {
                    "type": "box",
                    "layout": "baseline",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": emoji,
                            "size": "sm",
                            "color": "#aaaaaa"
                        },
                        {
                            "type": "text",
                            "text": genre_label,
                            "size": "sm",
                            "color": "#aaaaaa",
                            "margin": "md",
                            "flex": 0
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": self._format_date(article.published_at, article.source),
                    "size": "xxs",
                    "color": "#999999",
                    "margin": "md"
                }
            ]

            # 日本語要約をメイン要素として追加
            if article.curator_summary:
                body_contents.append({
                    "type": "text",
                    "text": article.curator_summary,
                    "weight": "bold",
                    "size": "sm",
                    "color": "#333333",
                    "margin": "md",
                    "wrap": True
                })
            else:
                # 要約がない場合、タイトルをフォールバック
                body_contents.append({
                    "type": "text",
                    "text": article.title[:80],
                    "weight": "bold",
                    "size": "sm",
                    "margin": "md",
                    "wrap": True
                })

            # 評価理由があれば追加（星付き）
            if article.curator_reason:
                star_rating = "★" * min(5, (article.curator_score or 0) // 2) if article.curator_score else ""
                reason_text = f"{star_rating} {article.curator_reason}" if star_rating else article.curator_reason
                body_contents.append({
                    "type": "text",
                    "text": reason_text,
                    "size": "xs",
                    "color": "#999999",
                    "margin": "md"
                })

            bubble = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": body_contents
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "記事を読む",
                                "uri": article.url
                            },
                            "style": "link",
                            "height": "sm"
                        }
                    ]
                }
            }
            bubbles.append(bubble)

        return {
            "type": "flex",
            "altText": f"📰 {timestamp} の朝刊",
            "contents": {
                "type": "carousel",
                "contents": bubbles
            }
        }
