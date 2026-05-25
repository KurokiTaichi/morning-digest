import json
import logging
from anthropic import Anthropic
from .collectors.base import Article
from .config import ANTHROPIC_API_KEY, GENRES

logger = logging.getLogger(__name__)


class ArticleCurator:
    """Claude Haiku でニュース記事をキュレーション"""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-haiku-4-5-20251001"

    def curate(self, articles: list[Article]) -> list[Article]:
        """
        全記事を Claude Haiku で一括評価
        スコア（0-10）とジャンルを付与、別処理で日本語要約を生成
        """
        if not articles:
            return []

        # ステップ1: スコア＋ジャンルの評価（シンプルな JSON）
        articles = self._evaluate_articles(articles)

        # ステップ2: 日本語要約の生成
        articles = self._generate_summaries(articles)

        return articles

    def _evaluate_articles(self, articles: list[Article]) -> list[Article]:
        """スコアとジャンルだけを評価（JSON をシンプルに）"""
        articles_list = "\n".join(
            [f"{i+1}. {article.title}" for i, article in enumerate(articles)]
        )

        genres_description = "\n".join([
            f"{genre_key}: {config['label']}"
            for genre_key, config in GENRES.items()
            if 'keywords' in config
        ])

        system_prompt = "JSONのみで返答してください。説明は不要です。"

        user_prompt = f"""記事をジャンル分類・スコアリングしてください。

【ジャンル】
{genres_description}

【記事】
{articles_list}

【形式】各行で: {{"id": 数字, "score": 0-10, "genre": "ai_tech|pm_product|business|finance"}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text

            # 各行をパース
            for line in response_text.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    result = json.loads(line)
                    article_id = result.get("id")
                    if article_id and 0 < article_id <= len(articles):
                        articles[article_id - 1].curator_score = result.get("score", 5)
                        articles[article_id - 1].genre = result.get("genre", "unknown")
                except json.JSONDecodeError:
                    pass

            logger.info(f"Evaluated {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Error evaluating articles: {e}")
            # デフォルト値を設定
            for article in articles:
                article.curator_score = 5
                article.genre = "unknown"
            return articles

    def _generate_summaries(self, articles: list[Article]) -> list[Article]:
        """日本語要約を生成"""
        # スコアが 5 以上の記事だけ要約を生成
        high_score_articles = [a for a in articles if a.curator_score and a.curator_score >= 5]

        if not high_score_articles:
            for article in articles:
                article.curator_summary = ""
            return articles

        summaries_prompt = """以下のタイトルについて、60-100字の日本語要約を1行で生成してください。
改行は含めないでください。

"""
        for article in high_score_articles:
            summaries_prompt += f"ID{articles.index(article)+1}: {article.title}\n"

        summaries_prompt += "\n出力形式: ID番号: 要約テキスト"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": summaries_prompt}]
            )

            response_text = response.content[0].text

            # 出力をパース
            for line in response_text.strip().split("\n"):
                if ":" not in line:
                    continue
                try:
                    id_str, summary = line.split(":", 1)
                    article_id = int(id_str.replace("ID", "").strip())
                    if 0 < article_id <= len(articles):
                        articles[article_id - 1].curator_summary = summary.strip()[:100]
                except (ValueError, IndexError):
                    pass

            logger.info("Generated summaries")
            return articles

        except Exception as e:
            logger.error(f"Error generating summaries: {e}")
            # 要約なしで返す
            for article in articles:
                article.curator_summary = ""
            return articles
