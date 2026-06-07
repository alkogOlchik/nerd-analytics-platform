# Модель определения тональности отзыва

Папка `sentiments` относится к задаче классификации `sentiment`: по отзыву нужно определить тональность. В ноутбуках сравниваются два варианта: модель только по тексту комментария и модель с дополнительными признаками.

## Файлы в папке

### `predict_sentiments.py`

Инференс-скрипт для применения уже обученной модели тональности к `pandas.DataFrame`.

Что делает файл:

- загружает `CatBoostClassifier` из `reviews_sentiments_comment_only.cbm`;
- загружает препроцессоры из `reviews_sentiments_comment_only_preprocessors.pkl`;
- очищает текст из колонки `comment`;
- приводит текст к нижнему регистру;
- удаляет ссылки, `www`-ссылки, упоминания, цифры и пунктуацию;
- оставляет буквы русского и английского алфавита;
- удаляет русские стоп-слова, кроме отрицаний `не`, `нет`, `ни`, `без`;
- лемматизирует слова через `pymorphy3`;
- строит word-level TF-IDF и char-level TF-IDF признаки;
- объединяет признаки через `hstack`;
- применяет CatBoost-модель;
- дополнительно извлекает слова и биграммы из очищенного комментария, оценивает их тональность той же моделью и формирует колонки `keywords_positive`, `keywords_negative`, `keywords_neutral`;
- заполняет только ту keyword-колонку, которая соответствует итоговому `predicted_sentiment`, остальные keyword-колонки остаются пустыми списками;
- возвращает копию датафрейма с новой колонкой `predicted_sentiment` и keyword-колонками.

Основные константы:

- `COMMENT_COLUMN = 'comment'`;
- `PREDICTION_COLUMN = 'predicted_sentiment'`;
- `KEYWORDS_POSITIVE_COLUMN = 'keywords_positive'`;
- `KEYWORDS_NEGATIVE_COLUMN = 'keywords_negative'`;
- `KEYWORDS_NEUTRAL_COLUMN = 'keywords_neutral'`;
- `DEFAULT_MODEL_PATH = 'reviews_sentiments_comment_only.cbm'`;
- `DEFAULT_PREPROCESSING_PATH = 'reviews_sentiments_comment_only_preprocessors.pkl'`.

Основные функции:

- `clean_text(text, russian_stopwords=None)` - нормализация, очистка и лемматизация текста.
- `load_model(model)` - загрузка `.cbm` модели через `CatBoostClassifier().load_model(...)`.
- `load_preprocessing(preprocessing)` - загрузка словаря препроцессоров через `joblib`.
- `build_features(df, preprocessing)` - построение sparse-матрицы признаков.
- `analyze_comment_words(clean_comment, keyword_sentiments)` - распределение слов и биграмм очищенного комментария по тональности.
- `keep_only_final_sentiment_keywords(keyword_row, final_sentiment)` - оставляет заполненной только keyword-колонку итоговой тональности.
- `predict_sentiments(df, model=..., preprocessing=...)` - основной интерфейс предсказания.

Что принимает на вход:

- `df`: `pandas.DataFrame` с колонкой `comment`;
- опционально `model`: путь к `reviews_sentiments_comment_only.cbm`;
- опционально `preprocessing`: путь к `reviews_sentiments_comment_only_preprocessors.pkl`.

Что возвращает:

- `pandas.DataFrame` со всеми исходными колонками, новой колонкой `predicted_sentiment` и колонками `keywords_positive`, `keywords_negative`, `keywords_neutral`.

### `reviews_sentiments.ipynb`

Экспериментальный ноутбук для определения тональности с использованием текста и дополнительных факторов.

На каких данных работает:

- читает `nerd_analytics_v25.xlsx`, лист `reviews`;
- использует колонки `id`, `comment`, `sentiment`, `rating`, `keywords_positive`, `keywords_neutral`, `keywords_negative`, `product`, `final_category`;
- целевая переменная: `sentiment`;
- признаки включают очищенный комментарий и дополнительные поля, связанные с отзывом;
- валидация использует группировку по очищенному комментарию, чтобы одинаковые тексты не попадали одновременно в train и validation.

Какие признаки строятся:

- `clean_comment`;
- word-level TF-IDF: `TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2, max_df=0.95)`;
- char-level TF-IDF: `TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=20000)`;
- one-hot признаки для дополнительных категориальных полей;
- итоговая sparse-матрица собирается через `hstack`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- CV seeds: `[67, 101, 202, 303, 404]`;
- метрика Optuna: `macro_f1`;
- `Optuna` запускается на `40` trials.

Какие модели перебираются:

- `SVC`;
- `LogisticRegression`;
- `CatBoostClassifier`.

Какие гиперпараметры перебираются:

- для `SVC`: `C`, `kernel`, `class_weight`;
- для `LogisticRegression`: `C`, `solver`, `class_weight`;
- для `CatBoostClassifier`: `iterations`, `depth`, `learning_rate`, `l2_leaf_reg`, `random_strength`, `bagging_temperature`, `border_count`, `auto_class_weights`.

Результат Optuna:

- лучшая модель: `CatBoostClassifier`;
- лучший mean CV score: `0.4185546038473055`;
- лучшие параметры: `iterations=655`, `depth=9`, `learning_rate=0.10360092983024889`, `l2_leaf_reg=3`, `random_strength=7.925080818531179`, `bagging_temperature=8.236969249945856`, `border_count=172`, `auto_class_weights='Balanced'`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.5078 +/- 0.1195`;
- `Macro F1: 0.4151 +/- 0.1072`;
- по объединённым CV-предсказаниям accuracy около `0.51`, macro avg F1 около `0.43`, weighted avg F1 около `0.52`.

Почему этот ноутбук не выбран:

- он немного уступает comment-only варианту по `macro_f1`;
- требует больше входных данных, что усложняет инференс;
- для тональности текста основной сигнал находится в самом комментарии, поэтому дополнительные поля не дают достаточного выигрыша.

### `reviews_sentiments_comment_only.ipynb`

Основной выбранный ноутбук для тональности. Использует только текст комментария.

На каких данных работает:

- читает `nerd_analytics_v25.xlsx`, лист `reviews`;
- целевая переменная: `sentiment`;
- входной признак: `comment`;
- создаёт `clean_comment`;
- не требует `product`, `rating`, `final_category` или ключевых слов на инференсе.

Какие признаки строятся:

- word-level TF-IDF: `max_features=30000`, n-граммы `(1, 2)`, `min_df=2`, `max_df=0.95`;
- char-level TF-IDF: символьные n-граммы `(3, 5)`, `max_features=20000`;
- итоговая матрица: `hstack([word_tfidf, char_tfidf])`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- CV seeds: `[67, 101, 202, 303, 404]`;
- метрика оптимизации: `macro_f1`;
- `Optuna` запускается на `40` trials.

Какие модели перебираются:

- `SVC`;
- `LogisticRegression`;
- `CatBoostClassifier`.

Результат Optuna:

- лучшая модель: `CatBoostClassifier`;
- лучший mean CV score: `0.4230125221044272`;
- лучшие параметры: `iterations=728`, `depth=4`, `learning_rate=0.06802738881986581`, `l2_leaf_reg=4`, `random_strength=9.918716096056352`, `bagging_temperature=7.205067472832152`, `border_count=208`, `auto_class_weights='Balanced'`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.5000 +/- 0.1120`;
- `Macro F1: 0.4230 +/- 0.1125`;
- по объединённым CV-предсказаниям accuracy около `0.50`, macro avg F1 около `0.44`, weighted avg F1 около `0.52`.

Что сохраняет:

- `reviews_sentiments_comment_only.cbm` через `best_model.save_model(...)`.

Почему выбран именно этот ноутбук:

- `macro_f1` немного выше, чем у варианта с дополнительными признаками: `0.4230` против `0.4151`;
- на инференсе нужна только колонка `comment`;
- модель проще встроить в общий пайплайн;
- именно этот вариант используется в `predict_sentiments.py`.

### `save_sentiment_comment_only_preprocessors.ipynb`

Служебный ноутбук для сохранения препроцессоров, которые нужны `predict_sentiments.py`.

Что делает:

- ищет `nerd_analytics_v25.xlsx` в текущей папке, на уровень выше или на два уровня выше;
- читает лист `reviews`;
- берёт `comment` и `sentiment`;
- применяет ту же очистку текста, что и выбранный ноутбук;
- обучает `word_vectorizer`;
- обучает `char_vectorizer`;
- сохраняет `reviews_sentiments_comment_only_preprocessors.pkl`.

Что лежит в сохранённом `bundle`:

- `task = 'sentiment_comment_only'`;
- `model_file = 'reviews_sentiments_comment_only.cbm'`;
- `text_column = 'comment'`;
- `target_column = 'sentiment'`;
- `word_vectorizer`;
- `char_vectorizer`;
- параметры очистки текста;
- метаданные: путь к данным, лист, количество строк, количество признаков и порядок признаков.

Важно: этот ноутбук сохраняет только препроцессоры. Саму CatBoost-модель сохраняет `reviews_sentiments_comment_only.ipynb`.

## Общий пайплайн для тональности

1. Открыть `reviews_sentiments_comment_only.ipynb`.
2. Подобрать модель и гиперпараметры по `macro_f1`.
3. Сохранить `reviews_sentiments_comment_only.cbm`.
4. Запустить `save_sentiment_comment_only_preprocessors.ipynb`.
5. Получить `reviews_sentiments_comment_only_preprocessors.pkl`.
6. Использовать `predict_sentiments.py` для инференса на датафрейме с колонкой `comment`.

Итоговый выбранный вариант: `reviews_sentiments_comment_only.ipynb`, потому что он немного лучше по `macro_f1`, проще по входным данным и полностью соответствует текущему инференс-скрипту.
