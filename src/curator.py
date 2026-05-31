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
        スコア（0-10）とジャンルを付与、別処理で日本語要約と評価理由を生成
        """
        if not articles:
            return []

        # ステップ1: スコア＋ジャンルの評価（シンプルな JSON）
        articles = self._evaluate_articles(articles)

        # ステップ2: 日本語要約の生成
        articles = self._generate_summaries(articles)

        # ステップ3: 評価理由の生成
        articles = self._generate_evaluation_reasons(articles)

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
        # すべての記事に要約を生成
        if not articles:
            return articles

        summaries_prompt = """以下のニュースタイトルについて、60-100字の簡潔な日本語要約を1行で生成してください。
【重要】改行やコロン以外の記号は絶対に含めないこと。ID番号と要約のみを出力。

"""
        for i, article in enumerate(articles):
            summaries_prompt += f"ID{i+1}: {article.title}\n"

        summaries_prompt += "\n出力形式: ID番号: 要約テキスト"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": summaries_prompt}]
            )

            response_text = response.content[0].text

            # 出力をパース（複数行対応）
            current_id = None
            current_summary = ""

            for line in response_text.strip().split("\n"):
                # ID行を検出
                if line.startswith("ID") and ":" in line:
                    # 前の ID のデータを保存
                    if current_id and current_summary:
                        if 0 < current_id <= len(articles):
                            articles[current_id - 1].curator_summary = current_summary.strip()[:100]

                    # 新しい ID を処理
                    try:
                        id_str, summary = line.split(":", 1)
                        current_id = int(id_str.replace("ID", "").strip())
                        current_summary = summary.strip()
                    except (ValueError, IndexError):
                        current_id = None
                        current_summary = ""
                elif current_id and line.strip():
                    # 継続行を追加
                    current_summary += " " + line.strip()

            # 最後の ID を保存
            if current_id and current_summary:
                if 0 < current_id <= len(articles):
                    articles[current_id - 1].curator_summary = current_summary.strip()[:100]

            logger.info("Generated summaries")
            return articles

        except Exception as e:
            logger.error(f"Error generating summaries: {e}")
            # 要約なしで返す
            for article in articles:
                article.curator_summary = ""
            return articles

    def _generate_evaluation_reasons(self, articles: list[Article]) -> list[Article]:
        """評価理由を生成"""
        if not articles:
            return articles

        reasons_prompt = """各記事のスコア根拠を30-50字で。改行なし。

"""
        for i, article in enumerate(articles):
            score = article.curator_score or 5
            reasons_prompt += f"ID{i+1}: {article.title}\n"

        reasons_prompt += "\n出力: ID番号: 根拠テキスト"

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": reasons_prompt}]
            )

            response_text = response.content[0].text

            # 出力をパース（複数行対応）
            current_id = None
            current_reason = ""

            for line in response_text.strip().split("\n"):
                # ID行を検出
                if line.startswith("ID") and ":" in line:
                    # 前の ID のデータを保存
                    if current_id and current_reason:
                        if 0 < current_id <= len(articles):
                            articles[current_id - 1].curator_reason = current_reason.strip()

                    # 新しい ID を処理
                    try:
                        id_str, reason = line.split(":", 1)
                        current_id = int(id_str.replace("ID", "").strip())
                        current_reason = reason.strip()
                    except (ValueError, IndexError):
                        current_id = None
                        current_reason = ""
                elif current_id and line.strip():
                    # 継続行を追加
                    current_reason += " " + line.strip()

            # 最後の ID を保存
            if current_id and current_reason:
                if 0 < current_id <= len(articles):
                    articles[current_id - 1].curator_reason = current_reason.strip()

            logger.info("Generated evaluation reasons")
            # デバッグ: 評価理由の統計
            with_reason = sum(1 for a in articles if a.curator_reason)
            logger.info(f"Articles with reasons: {with_reason}/{len(articles)}")
            return articles

        except Exception as e:
            import traceback
            logger.error(f"Error generating evaluation reasons: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # デフォルト値を設定
            for article in articles:
                article.curator_reason = ""
            return articles
