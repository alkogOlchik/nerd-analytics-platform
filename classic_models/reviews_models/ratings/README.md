# Модель предсказания рейтинга отзыва

Папка `ratings` относится к задаче предсказания числовой оценки `rating` по отзыву. В проекте это порядковая шкала от 1 до 5, поэтому качество оценивается не только точным совпадением, но и ошибками MAE/RMSE, а также попаданием в диапазон плюс-минус 1 балл.

## Файлы в папке

### `predict_ratings.py`

Инференс-скрипт для применения уже обученной модели рейтинга к `pandas.DataFrame`.

Что делает файл:

- загружает `CatBoostClassifier` из `reviews_ratings.cbm`;
- загружает препроцессоры из `reviews_ratings_preprocessors.pkl`;
- очищает и лемматизирует колонку `comment`;
- строит word-level TF-IDF признаки;
- строит char-level TF-IDF признаки;
- кодирует категориальные признаки через сохранённый `OneHotEncoder`;
- объединяет текстовые и категориальные признаки через `hstack`;
- применяет модель;
- округляет предсказание до ближайшего целого;
- ограничивает результат диапазоном от 1 до 5 через `np.clip`;
- возвращает копию исходного датафрейма с колонкой `predicted_rating`.

Основные константы:

- `COMMENT_COLUMN = 'comment'`;
- `CAT_COLUMNS = ['product', 'final_category', 'sentiment']`;
- `PREDICTION_COLUMN = 'predicted_rating'`;
- `DEFAULT_MODEL_PATH = 'reviews_ratings.cbm'`;
- `DEFAULT_PREPROCESSING_PATH = 'reviews_ratings_preprocessors.pkl'`.

Основные функции:

- `clean_text(text, russian_stopwords=None)` - нормализует текст, удаляет мусор, убирает стоп-слова, лемматизирует через `pymorphy3`.
- `load_model(model)` - создаёт `CatBoostClassifier` и загружает `.cbm` файл через `load_model`.
- `load_preprocessing(preprocessing)` - загружает словарь препроцессоров через `joblib`.
- `build_features(df, preprocessing)` - строит sparse-матрицу признаков в том же порядке, что и при обучении.
- `predict_ratings(df, model=..., preprocessing=...)` - возвращает датафрейм с предсказанным рейтингом.

Что принимает на вход:

- `df`: `pandas.DataFrame` с колонками `comment`, `product`, `final_category`, `sentiment`;
- опционально `model`: путь к `reviews_ratings.cbm`;
- опционально `preprocessing`: путь к `reviews_ratings_preprocessors.pkl`.

Что возвращает:

- `pandas.DataFrame` со всеми исходными колонками и новой колонкой `predicted_rating`.

### `reviews_ratings.ipynb`

Основной выбранный ноутбук для рейтинга. Он использует не только текст комментария, но и дополнительные признаки `product`, `final_category`, `sentiment`.

На каких данных работает:

- читает `nerd_analytics_v25.xlsx`, лист `reviews`;
- использует колонки `id`, `comment`, `sentiment`, `rating`, `keywords_positive`, `keywords_neutral`, `keywords_negative`, `product`, `final_category`;
- целевая переменная: `rating`;
- признаки: `comment`, `product`, `final_category`, `sentiment`;
- после предсказания значения приводятся к целым оценкам 1-5.

Какие признаки строятся:

- `clean_comment`: очищенный, лемматизированный текст;
- word-level TF-IDF: `TfidfVectorizer(max_features=25000, ngram_range=(1, 2), min_df=2, max_df=0.95)`;
- char-level TF-IDF: `TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=15000)`;
- one-hot признаки для `product`, `final_category`, `sentiment`;
- итоговая матрица: `hstack([word_tfidf, char_tfidf, onehot_product_final_category_sentiment])`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- seed: `[42, 101, 202, 303, 404]`;
- всего 25 фолдов/запусков оценки;
- оптимизация в Optuna идёт по минимизации `MAE`.

Почему используется MAE:

- рейтинг является порядковой шкалой;
- ошибка на 1 балл лучше, чем ошибка на 3 балла;
- `MAE` напрямую отражает среднюю абсолютную ошибку в баллах;
- дополнительно смотрится `RMSE`, точная accuracy и `within_1`.

Какие модели перебираются:

- `LogisticAT` из `mord`;
- `LogisticIT` из `mord`;
- `OrdinalRidge` из `mord`;
- `CatBoostClassifier`.

Почему есть ordinal-модели:

- рейтинг 1-5 является не просто набором классов, а упорядоченной шкалой;
- ordinal-модели учитывают порядок классов;
- для них sparse TF-IDF признаки дополнительно сжимаются через `TruncatedSVD`, потому что ordinal-модели не так удобно работают с очень большой разреженной матрицей.

Какие гиперпараметры перебираются:

- для `LogisticAT`, `LogisticIT`, `OrdinalRidge`: `alpha`, `n_components` для `TruncatedSVD`;
- для `CatBoostClassifier`: `iterations`, `depth`, `learning_rate`, `l2_leaf_reg`, `random_strength`, `bagging_temperature`, `border_count`, `auto_class_weights`.

Результат Optuna:

- лучшая модель: `CatBoostClassifier`;
- лучший mean CV MAE: `0.3436913179453137`;
- лучшие параметры: `iterations=436`, `depth=4`, `learning_rate=0.08512825639759057`, `l2_leaf_reg=9`, `random_strength=3.630280534343451`, `bagging_temperature=3.8388575694499907`, `border_count=100`, `auto_class_weights=None`.

Финальные метрики на кросс-валидации:

- `MAE: 0.3437 +/- 0.1390`;
- `RMSE: 0.5734 +/- 0.1246`;
- `Accuracy exact: 0.6563 +/- 0.1390`;
- `Accuracy within 1: 1.0000 +/- 0.0000`.

Что сохраняет:

- если лучшая модель `CatBoost`, сохраняет `reviews_ratings.cbm`;
- для ordinal-моделей был предусмотрен вариант сохранения `reviews_ratings.pkl`, но по результатам выбран `CatBoost`, поэтому основной артефакт - `.cbm`.

Почему выбран именно этот ноутбук:

- он даёт намного меньший MAE, чем comment-only вариант: `0.3437` против `0.9571`;
- он лучше использует контекст: продукт, категория и тональность сильно связаны с рейтингом;
- exact accuracy выше: `0.6563` против `0.2820`;
- все предсказания в CV попали в диапазон ошибки не больше 1 балла (`within_1 = 1.0`);
- именно его артефакты использует `predict_ratings.py`: `reviews_ratings.cbm` и `reviews_ratings_preprocessors.pkl`.

### `reviews_ratings_comment_only.ipynb`

Экспериментальный ноутбук для рейтинга, где используется только текст комментария.

На каких данных работает:

- читает тот же лист `reviews`;
- целевая переменная: `rating`;
- входной признак: только `comment`;
- строит `clean_comment`;
- не использует `product`, `final_category` и `sentiment`.

Какие признаки строятся:

- word-level TF-IDF: `max_features=25000`, n-граммы `(1, 2)`;
- char-level TF-IDF: символьные n-граммы `(3, 5)`, `max_features=15000`;
- для ordinal-моделей используется `TruncatedSVD`;
- итоговые признаки строятся только из текста.

Какие модели перебираются:

- `LogisticAT`;
- `LogisticIT`;
- `OrdinalRidge`;
- `CatBoostClassifier`.

Какая оптимизация:

- `Optuna`, `50` trials;
- направление: `minimize`;
- целевая метрика: mean CV `MAE`;
- CV seeds: `[42, 101, 202, 303, 404]`.

Финальный результат:

- лучшая модель: `LogisticIT`;
- `MAE: 0.9571 +/- 0.2016`;
- `RMSE: 1.2237 +/- 0.1946`;
- `Accuracy exact: 0.2820 +/- 0.1271`;
- `Accuracy within 1: 0.8101 +/- 0.0954`.

Почему этот ноутбук не выбран:

- качество заметно хуже, чем у варианта с дополнительными признаками;
- текст сам по себе недостаточно стабильно восстанавливает оценку 1-5;
- рейтинг часто зависит от контекста продукта, категории проблемы и тональности, поэтому all-factors модель закономерно выигрывает.

### `save_ratings_preprocessors.ipynb`

Служебный ноутбук для сохранения препроцессоров, которые нужны `predict_ratings.py`.

Что делает:

- ищет `nerd_analytics_v25.xlsx` в нескольких возможных расположениях;
- читает лист `reviews`;
- создаёт `clean_comment`;
- формирует датафрейм с `clean_comment`, `product`, `final_category`, `sentiment`, `rating`;
- обучает `word_vectorizer`;
- обучает `char_vectorizer`;
- обучает `OneHotEncoder` на `product`, `final_category`, `sentiment`;
- собирает полную матрицу признаков для проверки размерности;
- сохраняет `reviews_ratings_preprocessors.pkl`.

Что лежит в сохранённом `bundle`:

- `task = 'rating_all_factors'`;
- `model_file = 'reviews_ratings.cbm'`;
- `text_column = 'comment'`;
- `target_column = 'rating'`;
- `cat_cols = ['product', 'final_category', 'sentiment']`;
- `word_vectorizer`;
- `char_vectorizer`;
- `encoder`;
- параметры очистки текста;
- метаданные: путь к данным, лист, количество строк, количество признаков и порядок признаков.

Важно: этот ноутбук сохраняет только препроцессоры. Саму модель сохраняет `reviews_ratings.ipynb`.

## Общий пайплайн для рейтинга

1. Открыть `reviews_ratings.ipynb`.
2. Обучить модель и подобрать гиперпараметры по MAE.
3. Сохранить `reviews_ratings.cbm`.
4. Запустить `save_ratings_preprocessors.ipynb`.
5. Получить `reviews_ratings_preprocessors.pkl`.
6. Использовать `predict_ratings.py` на датафрейме с колонками `comment`, `product`, `final_category`, `sentiment`.

Итоговый выбранный вариант: `reviews_ratings.ipynb`, потому что модель с текстом, продуктом, категорией и тональностью сильно превосходит comment-only вариант по MAE, RMSE и точности.
