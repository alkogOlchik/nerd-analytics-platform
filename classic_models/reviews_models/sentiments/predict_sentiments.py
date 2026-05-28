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
KEYWORDS_POSITIVE_COLUMN = "keywords_positive"
KEYWORDS_NEGATIVE_COLUMN = "keywords_negative"
KEYWORDS_NEUTRAL_COLUMN = "keywords_neutral"
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
    if not isinstance(model, str | Path):
        return model
    model_path = Path(model)
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(str(model_path))
    return loaded_model


def load_preprocessing(preprocessing: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(preprocessing, dict):
        return preprocessing
    preprocessing = joblib.load(preprocessing)
    return preprocessing


def build_features(df: pd.DataFrame, preprocessing: str | Path | dict[str, Any]):
    preprocessing = load_preprocessing(preprocessing)
    _validate_preprocessing(preprocessing)

    clean_comments = clean_comments_from_df(df, preprocessing)
    return build_features_from_clean_comments(clean_comments, preprocessing)


def clean_comments_from_df(df: pd.DataFrame, preprocessing: dict[str, Any]) -> pd.Series:
    text_column = preprocessing.get("text_column", COMMENT_COLUMN)
    russian_stopwords = preprocessing.get("preprocessing", {}).get("russian_stopwords")
    return df[text_column].apply(lambda text: clean_text(text, russian_stopwords))


def build_features_from_clean_comments(clean_comments: pd.Series, preprocessing: dict[str, Any]):
    word_features = preprocessing["word_vectorizer"].transform(clean_comments)
    char_features = preprocessing["char_vectorizer"].transform(clean_comments)
    return hstack([word_features, char_features])


def build_keyword_sentiment_dict(
    clean_comments: pd.Series,
    model: Any,
    preprocessing: dict[str, Any],
) -> dict[str, str]:
    word_vectorizer = preprocessing["word_vectorizer"]
    known_features = set(word_vectorizer.get_feature_names_out())
    phrases = sorted({
        phrase
        for comment in clean_comments
        for phrase in _comment_words_and_bigrams(comment)
        if phrase in known_features
    })

    if not phrases:
        return {}

    phrase_features = build_features_from_clean_comments(pd.Series(phrases), preprocessing)
    phrase_predictions = _flatten_predictions(model.predict(phrase_features))
    return dict(zip(phrases, phrase_predictions))


def analyze_comment_words(clean_comment: str, keyword_sentiments: dict[str, str]) -> dict[str, list[str]]:
    text = str(clean_comment).split()
    positive_words = []
    negative_words = []
    neutral_words = []

    i = 0
    while i < len(text):
        if i < len(text) - 1:
            bigram = f"{text[i]} {text[i + 1]}"
            sentiment = keyword_sentiments.get(bigram)
            if sentiment in {"positive", "negative", "neutral"}:
                _append_keyword_by_sentiment(bigram, sentiment, positive_words, negative_words, neutral_words)
                i += 2
                continue

        word = text[i]
        sentiment = keyword_sentiments.get(word, "neutral")
        _append_keyword_by_sentiment(word, sentiment, positive_words, negative_words, neutral_words)
        i += 1

    return {
        KEYWORDS_POSITIVE_COLUMN: positive_words,
        KEYWORDS_NEGATIVE_COLUMN: negative_words,
        KEYWORDS_NEUTRAL_COLUMN: neutral_words,
    }


def keep_only_final_sentiment_keywords(
    keyword_row: dict[str, list[str]],
    final_sentiment: str,
) -> dict[str, list[str]]:
    result = {
        KEYWORDS_POSITIVE_COLUMN: [],
        KEYWORDS_NEGATIVE_COLUMN: [],
        KEYWORDS_NEUTRAL_COLUMN: [],
    }
    sentiment_to_column = {
        "positive": KEYWORDS_POSITIVE_COLUMN,
        "negative": KEYWORDS_NEGATIVE_COLUMN,
        "neutral": KEYWORDS_NEUTRAL_COLUMN,
    }
    column = sentiment_to_column.get(str(final_sentiment))
    if column:
        result[column] = keyword_row[column]
    return result


def predict_sentiments(
    df: pd.DataFrame,
    model: str | Path | Any = DEFAULT_MODEL_PATH,
    preprocessing: str | Path | dict[str, Any] = DEFAULT_PREPROCESSING_PATH,
) -> pd.DataFrame:

    loaded_model = load_model(model)
    loaded_preprocessing = load_preprocessing(preprocessing)
    _validate_preprocessing(loaded_preprocessing)

    clean_comments = clean_comments_from_df(df, loaded_preprocessing)
    features = build_features_from_clean_comments(clean_comments, loaded_preprocessing)
    predictions = _flatten_predictions(loaded_model.predict(features))
    keyword_sentiments = build_keyword_sentiment_dict(clean_comments, loaded_model, loaded_preprocessing)
    keyword_rows = clean_comments.apply(lambda text: analyze_comment_words(text, keyword_sentiments))
    filtered_keyword_rows = [
        keep_only_final_sentiment_keywords(keyword_row, prediction)
        for keyword_row, prediction in zip(keyword_rows, predictions)
    ]
    keyword_df = pd.DataFrame(filtered_keyword_rows, index=df.index)

    result = df.copy()
    result[PREDICTION_COLUMN] = predictions
    result[[KEYWORDS_POSITIVE_COLUMN, KEYWORDS_NEGATIVE_COLUMN, KEYWORDS_NEUTRAL_COLUMN]] = keyword_df[
        [KEYWORDS_POSITIVE_COLUMN, KEYWORDS_NEGATIVE_COLUMN, KEYWORDS_NEUTRAL_COLUMN]
    ]
    return result


def _flatten_predictions(predictions: Any) -> list[Any]:
    if hasattr(predictions, "flatten"):
        predictions = predictions.flatten()
    return list(predictions)


def _comment_words_and_bigrams(clean_comment: str) -> set[str]:
    words = str(clean_comment).split()
    phrases = set(words)
    phrases.update(f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))
    return phrases


def _append_keyword_by_sentiment(
    keyword: str,
    sentiment: str,
    positive_words: list[str],
    negative_words: list[str],
    neutral_words: list[str],
) -> None:
    if sentiment == "positive":
        positive_words.append(keyword)
    elif sentiment == "negative":
        negative_words.append(keyword)
    else:
        neutral_words.append(keyword)


def _validate_preprocessing(preprocessing: dict[str, Any]) -> None:
    missing = {"word_vectorizer", "char_vectorizer"} - set(preprocessing)
    if missing:
        raise ValueError(f"preprocessing is missing keys: {sorted(missing)}")

data = pd.read_excel("../../data/nerd_analytics_v25.xlsx", sheet_name="reviews")
predict_sentiments(data).to_excel("sentiments.xlsx", index=False)
