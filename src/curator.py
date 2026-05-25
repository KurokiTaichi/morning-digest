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
        スコア（0-10）とジャンル、日本語要約を付与
        """
        if not articles:
            return []

        # 評価用プロンプトを構築
        articles_list = "\n".join(
            [f"{i+1}. [{article.title}] | {article.url}" for i, article in enumerate(articles)]
        )

        # ジャンルキーワード定義（プロンプトに含める）
        genres_description = "\n".join([
            f"- {genre_key}: {config['label']} (キーワード: {', '.join(config['keywords'])})"
            for genre_key, config in GENRES.items()
            if 'keywords' in config
        ])

        system_prompt = """あなたはニュースキュレーターです。
与えられた記事リストを評価し、JSON形式で結果を返してください。
説明や余計なテキストは不要です。JSONのみ出力してください。"""

        user_prompt = f"""以下の記事リストを評価してください。

【対象ジャンル】
{genres_description}

【記事リスト】
{articles_list}

【評価方法】
各記事について、関連度とスコアをつけてください。
- score 8以上: 高関連・高品質（今日読む価値あり）
- score 5-7: 関連あり
- score 4以下: 関連薄い

【出力形式】JSONのみ（説明不要）
[{{"id": 1, "score": 0-10, "genre": "ai_tech|pm_product|business|finance", "summary_ja": "180字程度の詳しい日本語要約"}}]

例：
[
  {{"id": 1, "score": 9, "genre": "ai_tech", "summary_ja": "OpenAI が新型AIモデルを発表。自動推論機能が大幅改善され、従来のモデルより35%高速化。複雑な問題解決能力も向上し、研究開発やビジネス応用での期待が高まっている。実装方法やAPI の詳細も発表予定。"}},
  {{"id": 2, "score": 6, "genre": "business", "summary_ja": "スタートアップの資金調達における重要ポイントを詳解。VC との交渉時に押さえるべき論点、投資条件の交渉術、デューデリジェンス対策などを実例を交えて説明。初期段階から後期段階までの調達戦略の違いも解説。"}}
]
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            response_text = response.content[0].text

            # JSON をパース
            try:
                # JSON ブロックを抽出（マークダウンの場合に対応）
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text.strip()

                results = json.loads(json_str)

                # 評価結果を元の記事に付与
                result_map = {r["id"]: r for r in results}

                for i, article in enumerate(articles):
                    article_id = i + 1
                    if article_id in result_map:
                        result = result_map[article_id]
                        article.curator_score = result.get("score", 0)
                        article.curator_summary = result.get("summary_ja", "")
                        article.genre = result.get("genre", "")

                logger.info(f"Curated {len(articles)} articles successfully")
                return articles

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse curator response as JSON: {e}")
                logger.debug(f"Response text: {response_text}")
                # スコアなしで返す
                return articles

        except Exception as e:
            logger.error(f"Error in curator API call: {e}")
            return articles
