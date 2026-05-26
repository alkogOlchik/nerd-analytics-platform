# Модель определения категории отзыва

Папка `categories` относится к задаче классификации `final_category`: по отзыву и, в одном из экспериментов, дополнительным полям нужно определить категорию обращения. В качестве целевой переменной используется колонка `final_category` из таблицы `reviews`

## Файлы в папке

### `predict_categories.py`

Инференс-скрипт для применения уже обученной модели категории к `pandas.DataFrame`.

Что делает файл:

- загружает модель из `reviews_categories_comment_only.pkl`;
- загружает препроцессоры из `reviews_categories_comment_only_preprocessors.pkl`;
- очищает текст из колонки `comment`;
- приводит текст к нижнему регистру;
- удаляет ссылки, `www`-ссылки, упоминания пользователей, цифры и пунктуацию;
- оставляет русские и английские буквы;
- удаляет русские стоп-слова NLTK, но специально сохраняет отрицания `не`, `нет`, `ни`, `без`, потому что они важны для смысла отзыва;
- лемматизирует слова через `pymorphy3`;
- строит признаки теми же векторизаторами, которые были сохранены после обучения;
- объединяет word-level TF-IDF и char-level TF-IDF через `scipy.sparse.hstack`;
- применяет модель;
- возвращает копию входного датафрейма с новой колонкой `predicted_category`.

Основные функции:

- `clean_text(text, russian_stopwords=None)` - нормализует и лемматизирует текст.
- `load_model(model)` - загружает модель через `joblib.load`.
- `load_preprocessing(preprocessing)` - загружает словарь с препроцессорами.
- `build_features(df, preprocessing)` - превращает входной датафрейм в sparse-матрицу признаков.
- `predict_categories(df, model=..., preprocessing=...)` - основной публичный интерфейс для предсказания категорий.

Что принимает на вход:

- `df`: `pandas.DataFrame` с колонкой `comment`;
- опционально `model`: путь к `.pkl` модели или объект модели;
- опционально `preprocessing`: путь к `reviews_categories_comment_only_preprocessors.pkl`.

Что возвращает:

- `pandas.DataFrame`, содержащий все исходные колонки и дополнительную колонку `predicted_category`.

### `reviews_categories.ipynb`

Исследовательский ноутбук для задачи определения категории с использованием текста и дополнительных признаков.

На каких данных работает:

- читает `nerd_analytics_v25.xlsx`, лист `reviews`;
- оставляет колонки `id`, `comment`, `sentiment`, `rating`, `keywords_positive`, `keywords_neutral`, `keywords_negative`, `product`, `final_category`;
- в датасете в ноутбуке указано 1235 строк;
- целевая переменная: `final_category`;
- группы для кросс-валидации: очищенный текст `clean_comment`, чтобы одинаковые или близко продублированные комментарии не попадали одновременно в train и validation.

Какие признаки строятся:

- `clean_comment`: очищенный и лемматизированный текст `comment`;
- word-level TF-IDF: `TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2, max_df=0.95)`;
- char-level TF-IDF: `TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=20000)`;
- one-hot для `sentiment`;
- числовой `rating`, масштабированный через `StandardScaler`;
- итоговая матрица признаков собирается через `hstack([word_tfidf, char_tfidf, sentiment_onehot, rating_scaled])`.

Какая валидация используется:

- `StratifiedGroupKFold`;
- `N_SPLITS = 5`;
- несколько seed: `[42, 101, 202, 303, 404]`;
- всего получается 25 оценок качества;
- метрика для Optuna: `macro_f1`, потому что классы категорий несбалансированы и важно качество по всем категориям, а не только по самым частым.

Какие модели перебираются:

- `LogisticRegression`;
- `SVC`;
- `CatBoostClassifier`.

Какие гиперпараметры перебираются:

- для `SVC`: `C`, `kernel` (`linear` или `rbf`), `class_weight`;
- для `LogisticRegression`: `C`, `solver` (`lbfgs` или `saga`), `class_weight`;
- для `CatBoostClassifier`: `iterations`, `depth`, `learning_rate`, `l2_leaf_reg`, `random_strength`, `bagging_temperature`, `border_count`, `auto_class_weights`.

Результат Optuna:

- лучшая модель: `LogisticRegression`;
- лучшие параметры: `C=9.839975622808534`, `solver='saga'`, `class_weight='balanced'`;
- лучший средний CV score в Optuna: `0.4043711798725888`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.4568 +/- 0.1744`;
- `Macro F1: 0.4044 +/- 0.1804`;
- по объединённым CV-предсказаниям accuracy около `0.47`, macro avg F1 около `0.48`, weighted avg F1 около `0.47`.

Что сохраняет:

- `reviews_categories.pkl` через `joblib.dump(best_model, 'reviews_categories.pkl')`.

Этот ноутбук полезен как расширенный эксперимент: он проверяет, помогает ли модели знать не только текст, но и уже размеченные поля `sentiment` и `rating`.

### `reviews_categories_comment_only.ipynb`

Основной выбранный ноутбук для категории. Он решает ту же задачу `final_category`, но использует только текст комментария.

На каких данных работает:

- читает `nerd_analytics_v25.xlsx`, лист `reviews`;
- использует целевую переменную `final_category`;
- для признаков берёт только `comment`;
- создаёт `clean_comment` через ту же очистку, удаление стоп-слов и лемматизацию;
- группы для кросс-валидации также строятся по `clean_comment`.

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

- лучшая модель: `LogisticRegression`;
- лучшие параметры: `C=0.20820359820478732`, `solver='saga'`, `class_weight=None`;
- лучший mean CV score: `0.4410035231298915`.

Финальные метрики на кросс-валидации:

- `Accuracy: 0.4817 +/- 0.1283`;
- `Macro F1: 0.4410 +/- 0.1452`;
- по объединённым CV-предсказаниям accuracy около `0.48`, macro avg F1 около `0.50`, weighted avg F1 около `0.49`.

Что сохраняет:

- `reviews_categories_comment_only.pkl`.

Почему выбран именно этот ноутбук:

- он даёт лучший `macro_f1`: `0.4410` против `0.4044` у варианта с дополнительными признаками;
- он проще в эксплуатации: для предсказания нужна только колонка `comment`, не нужно иметь заранее известные `sentiment` и `rating`;
- он не создаёт зависимость категории от других предсказанных моделей, поэтому пайплайн инференса проще и устойчивее;
- именно его артефакты используются в `predict_categories.py`: `reviews_categories_comment_only.pkl` и `reviews_categories_comment_only_preprocessors.pkl`.

### `save_category_comment_only_preprocessors.ipynb`

Служебный ноутбук для сохранения препроцессоров, которые нужны `predict_categories.py`.

Что делает:

- ищет файл `nerd_analytics_v25.xlsx` в текущей папке, на уровень выше или на два уровня выше;
- читает лист `reviews`;
- берёт `comment` и `final_category`;
- повторяет текстовую очистку из выбранного comment-only ноутбука;
- обучает `word_vectorizer` и `char_vectorizer` на полном наборе комментариев;
- сохраняет всё в `reviews_categories_comment_only_preprocessors.pkl`.

Что лежит в сохранённом `bundle`:

- `task = 'category_comment_only'`;
- `model_file = 'reviews_categories_comment_only.pkl'`;
- `text_column = 'comment'`;
- `target_column = 'final_category'`;
- `word_vectorizer`;
- `char_vectorizer`;
- параметры и исходник функции очистки текста;
- метаданные: путь к данным, лист, количество строк, количество word/char признаков, порядок признаков.

Важно: этот ноутбук сохраняет только препроцессоры, а не саму модель. Модель сохраняется в `reviews_categories_comment_only.ipynb`.

## Общий пайплайн для категории

1. Открыть `reviews_categories_comment_only.ipynb`.
2. Обучить и выбрать лучшую модель по `macro_f1`.
3. Сохранить `reviews_categories_comment_only.pkl`.
4. Запустить `save_category_comment_only_preprocessors.ipynb`.
5. Получить `reviews_categories_comment_only_preprocessors.pkl`.
6. Использовать `predict_categories.py` для инференса на новых данных.

Итоговый выбранный вариант: `reviews_categories_comment_only.ipynb`, потому что он показал лучший `macro_f1`, требует только текст комментария и совпадает с текущим инференс-скриптом.
