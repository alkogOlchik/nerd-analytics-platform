"""Tool for capturing a user review from within the chat."""

from __future__ import annotations

from typing import Any, Dict

from langchain_core.tools import tool


@tool
def submit_review(rating: int, comment: str, product: str) -> Dict[str, Any]:
    """Сохранить отзыв пользователя о продукте или сервисе.

    Используй этот инструмент когда пользователь хочет оставить отзыв.
    ПЕРЕД вызовом убедись, что собрал все три параметра — задавай уточняющие
    вопросы по одному, если что-то не указано.

    Args:
        rating: оценка от 1 до 5 звёзд (целое число).
        comment: текст отзыва от пользователя.
        product: название продукта или ресурса, о котором отзыв.
    """
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return {"error": "Оценка должна быть целым числом от 1 до 5"}
    if not comment or not comment.strip():
        return {"error": "Текст отзыва не может быть пустым"}
    if not product or not product.strip():
        return {"error": "Необходимо указать продукт или ресурс"}
    return {
        "review_captured": True,
        "rating": rating,
        "comment": comment.strip(),
        "product": product.strip(),
    }
