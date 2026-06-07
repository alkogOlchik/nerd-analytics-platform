"""Сериализация keywords в varchar (через запятую)."""


def join_keywords(words: list[str]) -> str | None:
    cleaned = [w.strip() for w in words if w and w.strip()]
    return ", ".join(cleaned) if cleaned else None


def split_keywords(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]
