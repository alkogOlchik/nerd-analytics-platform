# Модель определения категории тикета

Папка `tickets_categories` относится к задаче классификации `final_category`: по тикету и первому клиентскому сообщению нужно определить итоговую категорию обращения. В ноутбуках сравниваются два варианта: модель только по тексту сообщения и модель с дополнительными признаками тикета.

## Файлы в папке

### `predict_ticket_categories.py`

Инференс-скрипт для применения уже обученной модели категории тикета к двум `pandas.DataFrame`: таблице тикетов и таблице истории чата.

Что делает файл:

- загружает сохранённый `joblib` bundle из `tickets_categories_with_features.pkl`;
- принимает датафрейм тикетов `data` и датафрейм сообщений `chat_history`;
- повторяет тот же join, что и в обучающих ноутбуках;
- берёт первое клиентское сообщение по каждому тикету;
- очищает текст из колонки `message`;
- приводит текст к нижнему регистру;
- удаляет ссылки, `www`-ссылки, упоминания пользователей, цифры и пунктуацию;
- оставляет русские и английские буквы;
- удаляет русские стоп-слова NLTK, но сохраняет отрицания `не`, `нет`, `ни`, `без`;
- лемматизирует слова через `pymorphy3`;
- строит признаки теми же препроцессорами, которые были сохранены после обучения;
- объединяет word-level TF-IDF, char-level TF-IDF, one-hot признаки и числовые признаки через `scipy.sparse.hstack`;
- применяет модель;
- дополнительно возвращает колонку `keywords` с тремя словами или биграммами, которые повлияли на выбор предсказанного класса;
- если слово входит в выбранную биграмму, отдельно это слово в `keywords` не дублируется;
- возвращает копию объединённого датафрейма с колонками `predicted_category` и `keywords`.

Основные константы:

- `DEFAULT_MODEL_PATH = 'tickets_categories_with_features.pkl'`;
- `PREDICTION_COLUMN = 'predicted_category'`;
- `KEYWORDS_COLUMN = 'keywords'`.

Основные функции:

- `clean_text(text, russian_stopwords=None)` - нормализует и лемматизирует текст.
- `load_bundle(model_path=...)` - загружает сохранённый bundle с моделью и препроцессорами.
- `prepare_tickets_dataframe(data, chat_history)` - повторяет подготовку входного датафрейма и join с первым сообщением клиента.
- `build_features(df, bundle)` - превращает датафрейм в sparse-матрицу признаков.
- `build_keywords(clean_messages_series, predictions, bundle, top_n=3)` - выбирает ключевые слова и биграммы для предсказанного класса.
- `predict_ticket_categories(data, chat_history, model_path=...)` - основной публичный интерфейс для предсказания категорий.

Что принимает на вход:

- `data`: `pandas.DataFrame` с тикетами, где есть `id` или `ticket_id`, `product`, `priority`, `reopened_count`;
- `chat_history`: `pandas.DataFrame` с колонками `ticket_id`, `role`, `message`, `created_at`;
- опционально `model_path`: путь к `tickets_categories_with_features.pkl` или уже загруженный bundle.

Что возвращает:

- `pandas.DataFrame`, содержащий исходные колонки тикета, первое клиентское сообщение `message`, колонку `predicted_category` и колонку `keywords`.


### `tickets_categories_with_features.ipynb`

Основной выбранный ноутбук для категории тикета. Он использует текст первого клиентского сообщения и дополнительные признаки тикета.

На каких данных работает:

- читает `../data/nerd_analytics_v25.xlsx`, лист `tickets`;
- читает `../data/nerd_analytics_v25.xlsx`, лист `chat_history`;
- оставляет только сообщения клиента `role == 'client'`;
- сортирует сообщения по `created_at`;
- берёт первое клиентское сообщение для каждого `ticket_id`;
- делает `inner` join тикетов с первым клиентским сообщением;
- целевая переменная: `final_category`;
- входные признаки: `message`, `product`, `priority`, `reopened_count`;
- в датасете после join используется 3000 строк.

Какие признаки строятся:

- `clean_message`: очищенный и лемматизированный текст первого клиентского сообщения;
- word-level TF-IDF: `TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2, max_df=0.95)`;
- char-level TF-IDF: `TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=20000)`;
- one-hot признаки для `product` и `priority`;
- числовой `reopened_count`, масштабированный через `StandardScaler`;
- итоговая матрица признаков собирается через `hstack([word_tfidf, char_tfidf, categorical_one_hot, numeric_scaled])`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- seed: `[42, 101, 202, 303, 404]`;
- всего получается 25 оценок качества;
- метрика для Optuna: `macro_f1`, потому что классов несколько и важно качество по всем категориям, а не только по самым частым;
- `Optuna` запускается на `40` trials.

Какие модели перебираются:

- `SVC`;
- `LogisticRegression`;
- `CatBoostClassifier`.

Какие гиперпараметры перебираются:

- для `SVC`: `C`, `kernel` (`linear` или `rbf`), `class_weight`;
- для `LogisticRegression`: `C`, `solver` (`lbfgs` или `saga`), `class_weight`;
- для `CatBoostClassifier`: `iterations`, `depth`, `learning_rate`, `l2_leaf_reg`, `random_strength`, `bagging_temperature`, `border_count`, `auto_class_weights`.

Результат Optuna:

- лучшая модель: `LogisticRegression`;
- лучшие параметры: `C=3.9349286049156182`, `solver='saga'`, `class_weight='balanced'`;
- лучший mean CV score: `0.09622793698963505`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.1569 +/- 0.1073`;
- `Macro F1: 0.0962 +/- 0.0631`;
- по объединённым CV-предсказаниям accuracy около `0.16`, macro avg F1 около `0.16`, weighted avg F1 около `0.16`.

Что сохраняет:

- `tickets_categories_with_features.pkl`.

Что лежит в сохранённом bundle:

- `task = 'tickets_category_with_features'`;
- обученная модель;
- тип модели и параметры модели;
- `word_vectorizer`;
- `char_vectorizer`;
- `encoder` для `product` и `priority`;
- `numeric_scaler` для `reopened_count`;
- параметры очистки текста;
- порядок признаков;
- метрики CV;
- метаданные: путь к данным, листы, количество строк, классы и количество признаков.

Почему выбран именно этот ноутбук:

- он лучше по основной метрике `macro_f1`: `0.0962` против `0.0782` у варианта только по тексту;
- использует доступные на инференсе признаки тикета: `product`, `priority`, `reopened_count`;
- именно его bundle используется в `predict_ticket_categories.py`.

Важно: абсолютное качество модели пока слабое, поэтому этот вариант выбран как лучший из двух текущих экспериментов, но не как финальная высокоточная production-модель.

### `tickets_categories_comment_only.ipynb`

Экспериментальный ноутбук для категории тикета, где используется только текст первого клиентского сообщения.

На каких данных работает:

- читает `../data/nerd_analytics_v25.xlsx`, лист `tickets`;
- читает `../data/nerd_analytics_v25.xlsx`, лист `chat_history`;
- берёт первое клиентское сообщение по каждому тикету;
- целевая переменная: `final_category`;
- входной признак: только `message`;
- создаёт `clean_message` через ту же очистку, удаление стоп-слов и лемматизацию.

Какие признаки строятся:

- word-level TF-IDF: `max_features=30000`, n-граммы `(1, 2)`, `min_df=2`, `max_df=0.95`;
- char-level TF-IDF: символьные n-граммы `(3, 5)`, `max_features=20000`;
- итоговая матрица: `hstack([word_tfidf, char_tfidf])`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- seed: `[42, 101, 202, 303, 404]`;
- метрика оптимизации: `macro_f1`;
- `Optuna` запускается на `40` trials.

Какие модели перебираются:

- `SVC`;
- `LogisticRegression`;
- `CatBoostClassifier`.

Результат Optuna:

- лучшая модель: `SVC`;
- лучшие параметры: `C=3.8700335721489627`, `kernel='linear'`, `class_weight='balanced'`;
- лучший mean CV score: `0.07819356653707712`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.2093 +/- 0.1780`;
- `Macro F1: 0.0782 +/- 0.0696`;
- по объединённым CV-предсказаниям accuracy около `0.21`, macro avg F1 около `0.20`, weighted avg F1 около `0.19`.

Что сохраняет:

- `tickets_categories_comment_only.pkl`.

Почему этот ноутбук не выбран:

- он уступает варианту с признаками по основной метрике `macro_f1`;
- текст первого клиентского сообщения часто слишком короткий, поэтому дополнительных признаков тикета не хватает;
- `predict_ticket_categories.py` использует выбранный вариант `tickets_categories_with_features.pkl`.

## Общий пайплайн для категории тикета

1. Открыть `tickets_categories_with_features.ipynb`.
2. Обучить модель и подобрать гиперпараметры по `macro_f1`.
3. Сохранить `tickets_categories_with_features.pkl`.
4. Положить `tickets_categories_with_features.pkl` рядом с `predict_ticket_categories.py`.
5. Использовать `predict_ticket_categories.py` для инференса на двух датафреймах: `data` и `chat_history`.

Итоговый выбранный вариант: `tickets_categories_with_features.ipynb`, потому что он показал лучший `macro_f1` среди двух текущих вариантов и использует признаки, доступные на этапе предсказания.
