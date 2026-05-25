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

【出力形式】必ず JSON のみ（マークダウン記号なし）
各要約は1行で、改行は含めない。日本語テキストは必ずダブルクォートで囲む。

[{{"id": 1, "score": 9, "genre": "ai_tech", "summary_ja": "OpenAIが新型AIモデルを発表。推論機能が改善され従来より35%高速化。複雑問題の解決能力も向上し研究開発での期待が高い。"}}, {{"id": 2, "score": 6, "genre": "business", "summary_ja": "スタートアップ資金調達のポイント解説。VC交渉術・投資条件・デューデリジェンス対策など実例で説明。初期から後期の調達戦略の違いも解説。"}}]
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
                logger.debug(f"Response text: {response_text[:500]}")
                # JSON パース失敗時はデフォルトスコアを使用
                for i, article in enumerate(articles):
                    article.curator_score = 5
                    article.curator_summary = article.title[:60]
                    article.genre = "unknown"
                return articles

        except Exception as e:
            logger.error(f"Error in curator API call: {e}")
            return articles
