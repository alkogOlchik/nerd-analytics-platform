from __future__ import annotations
from pathlib import Path
from typing import Any
import re
import joblib
import nltk
import numpy as np
import pandas as pd
import pymorphy3
from nltk.corpus import stopwords
from scipy.sparse import csr_matrix, hstack

DEFAULT_MODEL_PATH = "tickets_categories_with_features.pkl"
PREDICTION_COLUMN = "predicted_category"
KEYWORDS_COLUMN = "keywords"

_MORPH = pymorphy3.MorphAnalyzer()
_BAD_STOPWORDS = {"не", "нет", "ни", "без"}
try:
    _RUSSIAN_STOPWORDS = [word for word in stopwords.words("russian") if word not in _BAD_STOPWORDS]
except LookupError:
    nltk.download("stopwords", quiet=True)
    _RUSSIAN_STOPWORDS = [word for word in stopwords.words("russian") if word not in _BAD_STOPWORDS]


def clean_text(text: Any, russian_stopwords: list[str] | set[str] | None = None) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"www\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"[^а-яa-zё\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    stop_words = set(russian_stopwords or _RUSSIAN_STOPWORDS)
    lemmas = []
    for word in text.split():
        if word not in stop_words:
            lemmas.append(_MORPH.parse(word)[0].normal_form)

    return " ".join(lemmas)


def load_bundle(model_path: str | Path | dict[str, Any] = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    if isinstance(model_path, dict):
        _validate_bundle(model_path)
        return model_path

    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model bundle not found: {path}")

    bundle = joblib.load(path)
    _validate_bundle(bundle)
    return bundle


def prepare_tickets_dataframe(data: pd.DataFrame, chat_history: pd.DataFrame) -> pd.DataFrame:
    chat_history = chat_history.loc[
        chat_history["ticket_id"].notna() & (chat_history["role"] == "client"),
        ["ticket_id", "message", "created_at"],
    ].sort_values("created_at")
    chat_history = chat_history.drop_duplicates(subset="ticket_id", keep="first")

    if "ticket_id" not in data.columns and "id" in data.columns:
        data = data.rename(columns={"id": "ticket_id"})

    result = pd.merge(
        data,
        chat_history[["ticket_id", "message"]],
        on="ticket_id",
        how="inner",
    )
    return result


def build_features(df: pd.DataFrame, bundle: dict[str, Any]):
    preprocessors = bundle["preprocessors"]
    config = bundle.get("config", {})
    categorical_columns = config.get("categorical_columns", ["product", "priority"])
    numeric_columns = config.get("numeric_columns", ["reopened_count"])
    categorical_fill_value = config.get("categorical_fill_value", "unknown")
    numeric_fill_value = config.get("numeric_fill_value", 0)

    prepared = df.copy()
    prepared["clean_message"] = clean_messages(prepared, bundle)
    prepared[categorical_columns] = prepared[categorical_columns].fillna(categorical_fill_value).astype(str)
    prepared[numeric_columns] = prepared[numeric_columns].fillna(numeric_fill_value)

    word_features = preprocessors["word_vectorizer"].transform(prepared["clean_message"])
    char_features = preprocessors["char_vectorizer"].transform(prepared["clean_message"])
    cat_features = preprocessors["encoder"].transform(prepared[categorical_columns])
    numeric_features = csr_matrix(preprocessors["numeric_scaler"].transform(prepared[numeric_columns]))

    return hstack([word_features, char_features, cat_features, numeric_features]), prepared["clean_message"]


def clean_messages(df: pd.DataFrame, bundle: dict[str, Any]) -> pd.Series:
    config = bundle.get("config", {})
    text_column = config.get("text_column", "message")
    russian_stopwords = config.get("russian_stopwords")
    return df[text_column].apply(lambda text: clean_text(text, russian_stopwords))


def predict_ticket_categories(
    data: pd.DataFrame,
    chat_history: pd.DataFrame,
    model_path: str | Path | dict[str, Any] = DEFAULT_MODEL_PATH,
) -> pd.DataFrame:
    bundle = load_bundle(model_path)
    merged = prepare_tickets_dataframe(data, chat_history)
    _validate_input_columns(merged, bundle)

    features, clean_messages_series = build_features(merged, bundle)
    model = bundle["model"]
    predictions = _flatten_predictions(model.predict(features))

    result = merged.copy()
    result[PREDICTION_COLUMN] = predictions
    result[KEYWORDS_COLUMN] = build_keywords(clean_messages_series, predictions, bundle)
    return result


def build_keywords(
    clean_messages_series: pd.Series,
    predictions: list[Any],
    bundle: dict[str, Any],
    top_n: int = 3,
) -> list[str]:
    model = bundle["model"]
    word_vectorizer = bundle["preprocessors"]["word_vectorizer"]
    word_features = word_vectorizer.transform(clean_messages_series)
    feature_names = word_vectorizer.get_feature_names_out()

    if not hasattr(model, "coef_") or not hasattr(model, "classes_"):
        return [
            ", ".join(_select_non_overlapping_phrases(_active_terms(row, feature_names), top_n))
            for row in word_features
        ]

    coefs = np.asarray(model.coef_)
    classes = list(model.classes_)

    keyword_rows = []
    for row_idx, prediction in enumerate(predictions):
        try:
            class_idx = classes.index(prediction)
        except ValueError:
            keyword_rows.append("")
            continue

        if coefs.shape[0] != len(classes):
            keyword_rows.append(", ".join(_select_non_overlapping_phrases(_active_terms(word_features[row_idx], feature_names), top_n)))
            continue

        row = word_features[row_idx].tocoo()
        scored_terms = []
        for feature_idx, value in zip(row.col, row.data):
            score = float(value * coefs[class_idx, feature_idx])
            if score > 0:
                scored_terms.append((feature_names[feature_idx], score))

        scored_terms.sort(key=lambda item: item[1], reverse=True)
        phrases = [term for term, _ in scored_terms]
        if not phrases:
            phrases = _active_terms(word_features[row_idx], feature_names)

        keyword_rows.append(", ".join(_select_non_overlapping_phrases(phrases, top_n)))

    return keyword_rows


def _active_terms(row: Any, feature_names: np.ndarray) -> list[str]:
    row = row.tocoo()
    terms = [(feature_names[idx], value) for idx, value in zip(row.col, row.data)]
    terms.sort(key=lambda item: item[1], reverse=True)
    return [term for term, _ in terms]


def _select_non_overlapping_phrases(phrases: list[str], top_n: int) -> list[str]:
    selected: list[str] = []

    for phrase in phrases:
        phrase_words = phrase.split()
        if len(phrase_words) == 1 and any(phrase in selected_phrase.split() for selected_phrase in selected):
            continue

        if len(phrase_words) > 1:
            selected = [
                selected_phrase
                for selected_phrase in selected
                if not (len(selected_phrase.split()) == 1 and selected_phrase in phrase_words)
            ]

        if phrase not in selected:
            selected.append(phrase)

        if len(selected) >= top_n:
            break

    return selected


def _flatten_predictions(predictions: Any) -> list[Any]:
    if hasattr(predictions, "flatten"):
        predictions = predictions.flatten()
    return list(predictions)


def _validate_bundle(bundle: dict[str, Any]) -> None:
    missing_bundle_keys = {"model", "preprocessors"} - set(bundle)
    if missing_bundle_keys:
        raise ValueError(f"Model bundle is missing keys: {sorted(missing_bundle_keys)}")

    missing_preprocessors = {"word_vectorizer", "char_vectorizer", "encoder", "numeric_scaler"} - set(bundle["preprocessors"])
    if missing_preprocessors:
        raise ValueError(f"Model bundle preprocessors are missing keys: {sorted(missing_preprocessors)}")


def _validate_input_columns(df: pd.DataFrame, bundle: dict[str, Any]) -> None:
    config = bundle.get("config", {})
    required_columns = [
        config.get("text_column", "message"),
        *config.get("categorical_columns", ["product", "priority"]),
        *config.get("numeric_columns", ["reopened_count"]),
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Input data is missing columns: {missing}")

### Проверка
data = pd.read_excel('../data/nerd_analytics_v25.xlsx', sheet_name='tickets')
chat_history = pd.read_excel('../data/nerd_analytics_v25.xlsx', sheet_name='chat_history')
predict_ticket_categories(data, chat_history).to_excel('check.xlsx')
