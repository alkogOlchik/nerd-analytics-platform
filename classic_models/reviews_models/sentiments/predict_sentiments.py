from __future__ import annotations
from pathlib import Path
from typing import Any
import joblib
import nltk
import pandas as pd
import pymorphy3
import re
from scipy.sparse import hstack
from catboost import CatBoostClassifier
from nltk.corpus import stopwords


COMMENT_COLUMN = "comment"
PREDICTION_COLUMN = "predicted_sentiment"
DEFAULT_MODEL_PATH = "reviews_sentiments_comment_only.cbm"
DEFAULT_PREPROCESSING_PATH = "reviews_sentiments_comment_only_preprocessors.pkl"

_MORPH = pymorphy3.MorphAnalyzer()
_BAD_STOPWORDS = {"не", "нет", "ни", "без"}
try:
    _RUSSIAN_STOPWORDS = [word for word in stopwords.words("russian") if word not in _BAD_STOPWORDS]
except LookupError:
    nltk.download("stopwords", quiet=True)
    _RUSSIAN_STOPWORDS = [word for word in stopwords.words("russian") if word not in _BAD_STOPWORDS]


def clean_text(text: Any, russian_stopwords: list[str] | set[str] | None = None) -> str:
    text = str(text)
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"[^а-яa-zё\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    lemmas = []
    for word in text.split():
        if word not in _RUSSIAN_STOPWORDS:
            lemmas.append(_MORPH.parse(word)[0].normal_form)

    return " ".join(lemmas)


def load_model(model: str | Path | Any) -> Any:
    model_path = Path(model)
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(str(model_path))
    return loaded_model


def load_preprocessing(preprocessing: str | Path | dict[str, Any]) -> dict[str, Any]:
    preprocessing = joblib.load(preprocessing)
    return preprocessing


def build_features(df: pd.DataFrame, preprocessing: str | Path | dict[str, Any]):
    preprocessing = load_preprocessing(preprocessing)
    _validate_preprocessing(preprocessing)

    text_column = preprocessing.get("text_column", COMMENT_COLUMN)
    russian_stopwords = preprocessing.get("preprocessing", {}).get("russian_stopwords")
    clean_comments = df[text_column].apply(lambda text: clean_text(text, russian_stopwords))
    word_features = preprocessing["word_vectorizer"].transform(clean_comments)
    char_features = preprocessing["char_vectorizer"].transform(clean_comments)
    return hstack([word_features, char_features])


def predict_sentiments(
    df: pd.DataFrame,
    model: str | Path | Any = DEFAULT_MODEL_PATH,
    preprocessing: str | Path | dict[str, Any] = DEFAULT_PREPROCESSING_PATH,
) -> pd.DataFrame:

    loaded_model = load_model(model)
    features = build_features(df, preprocessing)
    predictions = loaded_model.predict(features)

    result = df.copy()
    result[PREDICTION_COLUMN] = _flatten_predictions(predictions)
    return result


def _flatten_predictions(predictions: Any) -> list[Any]:
    if hasattr(predictions, "flatten"):
        predictions = predictions.flatten()
    return list(predictions)


def _validate_preprocessing(preprocessing: dict[str, Any]) -> None:
    missing = {"word_vectorizer", "char_vectorizer"} - set(preprocessing)
    if missing:
        raise ValueError(f"preprocessing is missing keys: {sorted(missing)}")


### Проверяем
data = pd.read_excel('../data/nerd_analytics_v25.xlsx', sheet_name='reviews')
print(predict_sentiments(data)['predicted_sentiment'].value_counts())
