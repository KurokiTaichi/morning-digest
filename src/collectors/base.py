from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime


@dataclass
class Article:
    """記事データクラス"""
    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    genre: Optional[str] = None
    curator_score: Optional[int] = None  # Claude キュレーション後のスコア（0-10）
    curator_summary: Optional[str] = None  # Claude による日本語要約


class BaseCollector(ABC):
    """全コレクターの抽象基底クラス"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def collect(self) -> list[Article]:
        """記事を収集して返す"""
        pass

    def filter_recent(self, articles: list[Article], hours: int = 24) -> list[Article]:
        """指定時間以内の記事をフィルタ"""
        if not articles or not articles[0].published_at:
            return articles

        now = datetime.utcnow()
        return [
            a for a in articles
            if a.published_at and (now - a.published_at).total_seconds() < hours * 3600
        ]

    def limit(self, articles: list[Article], count: int) -> list[Article]:
        """記事数を制限"""
        return articles[:count]
