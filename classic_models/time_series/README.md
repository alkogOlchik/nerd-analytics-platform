# Time Series Ticket Forecast

Проект прогнозирует количество тикетов поддержки на неделю вперед в разрезе пар:

- `product`
- `final_category`

Основной workflow состоит из двух частей:

- `tickets_time_series.ipynb` - обучение, подбор модели, оценка качества, сохранение артефактов.
- `tickets_time_series_predict.py` - инференс: загрузка готового `.pkl`-артефакта и построение прогноза без исходного Excel-файла.

## Файлы в папке

### `tickets_time_series.ipynb`

Jupyter/Colab-ноутбук для полного цикла обучения модели временных рядов.

Он:

- читает Excel-файл с тикетами;
- подготавливает дневные временные ряды;
- строит лаговые, rolling, expanding и календарные признаки;
- обучает несколько моделей;
- подбирает гиперпараметры через Optuna;
- сравнивает модели с бейзлайнами;
- считает метрики на holdout-периоде;
- строит прогноз на неделю вперед;
- сохраняет `.pkl`-артефакт модели;
- сохраняет Excel-файлы с метриками и прогнозом.

### `tickets_time_series_predict.py`

Python-скрипт для применения уже обученной модели.

Он:

- не читает исходный Excel;
- не принимает новый датасет;
- загружает готовый `tickets_time_series_artifacts.pkl`;
- берет из `.pkl` сохраненную историю `history_daily`;
- строит рекурсивный прогноз на будущие даты;
- сохраняет Excel с прогнозом.

## Входные данные для ноутбука

Ноутбук ожидает Excel-файл рядом с ноутбуком.
Обязательные колонки:

- `date` - дата создания тикета;
- `product` - продукт;
- `final_category` - финальная категория тикета.

## Подготовка данных в ноутбуке

Cтроится полный календарь:

- все даты от минимальной до максимальной даты;
- все найденные пары `product × final_category`;
- для отсутствующих комбинаций ставится `tickets = 0`.

На текущем прогоне в ноутбуке было:

- 6 продуктов;
- 8 категорий;
- 48 рядов `product × final_category`;
- горизонт прогноза: 7 дней;
- holdout-период: 28 дней.

## Признаки модели

Модель прогнозирует количество тикетов по каждому `series_id` на каждый день.

Целевая переменная:

```python
target_col = 'tickets'
```

Категориальные признаки:

```python
cat_features = ['product', 'final_category']
```

Числовые признаки строятся из истории ряда и календаря.

### Лаги

Для каждого ряда строятся лаги:

```python
lag_1, lag_2, lag_3, lag_4, lag_5, lag_6, lag_7,
lag_14, lag_21, lag_28, lag_35, lag_42, lag_56
```

Важно: лаги строятся через `shift`, то есть текущий день не попадает в свои же признаки.

### Rolling-признаки

Для окон:

```python
3, 7, 14, 28, 56
```

строятся:

- `rolling_mean`;
- `rolling_median`;
- `rolling_std`;
- `rolling_min`;
- `rolling_max`;
- `rolling_nonzero_share`.

Rolling-признаки считаются по `shifted = grouped.shift(1)`, то есть только по прошлым значениям.

### EWM и expanding

Также используются:

- `ewm_mean_7`;
- `ewm_mean_28`;
- `expanding_mean`;
- `expanding_nonzero_share`;
- `series_age_days`;
- `days_since_nonzero`.

### Агрегированные исторические признаки

Добавляются признаки по общему дневному объему:

- `global_lag_1`;
- `global_rolling_mean_7`;
- `global_rolling_mean_28`.

Добавляются признаки по продукту:

- `product_lag_1`;
- `product_rolling_mean_7`;
- `product_rolling_mean_28`.

Добавляются признаки по категории:

- `category_lag_1`;
- `category_rolling_mean_7`;
- `category_rolling_mean_28`.

### Календарные признаки

Добавляются:

- `dayofweek`;
- `dayofmonth`;
- `weekofyear`;
- `month`;
- `quarter`;
- `is_month_start`;
- `is_month_end`;
- `is_weekend`;
- `days_from_start`;
- `dow_sin`;
- `dow_cos`;
- `month_sin`;
- `month_cos`.

## Разделение train/test

В ноутбуке используются параметры:

```python
HORIZON_DAYS = 7
TEST_DAYS = 28
MIN_TRAIN_DAYS = 84
ARIMA_MAX_SERIES = 40
```

Holdout строится как последние 28 дней данных:

```python
test_start = features['date'].max() - pd.Timedelta(days=TEST_DAYS - 1)
train = features[features['date'] < test_start]
test = features[features['date'] >= test_start]
```

На текущем прогоне:

- train: `2025-09-17` - `2026-04-20`;
- test: `2026-04-21` - `2026-05-18`;
- train shape: `(10368, 80)`;
- test shape: `(1344, 80)`.

## Метрики

Используются те же метрики для всех моделей:

- `MAE` - средняя абсолютная ошибка;
- `RMSE` - корень из средней квадратичной ошибки;
- `MAPE` - средняя абсолютная процентная ошибка;
- `WAPE` - суммарная абсолютная ошибка, деленная на суммарный факт.

Формула WAPE:

```python
sum(abs(y_true - y_pred)) / max(sum(abs(y_true)), 1)
```

Для этих данных `MAPE` получается огромным и практически непоказательным, потому что в рядах много нулей. Основные метрики для сравнения:

- `MAE`;
- `RMSE`;
- `WAPE`.

## Бейзлайны

В ноутбуке считаются два бейзлайна:

### `baseline_rolling_mean_7`

Прогноз равен среднему значению ряда за последние 7 дней.

Результат на текущем holdout:

- `MAE = 0.327381`;
- `RMSE = 0.605038`;
- `WAPE = 1.623616`.

### `baseline_series_weekday_mean`

Прогноз равен среднему значению ряда для такого же дня недели.

Результат на текущем holdout:

- `MAE = 0.338542`;
- `RMSE = 0.609327`;
- `WAPE = 1.678967`.

## Какие модели перебирались

Optuna перебирает следующие типы моделей:

- `ridge`;
- `poisson`;
- `random_forest`;
- `extra_trees`;
- `hist_gradient_boosting`;
- `sarimax`.

Количество trials:

```python
n_trials = 60
```

### Ridge

Перебирается:

```python
alpha: 0.01 ... 100.0, log scale
```

### PoissonRegressor

Перебирается:

```python
alpha: 0.0001 ... 10.0, log scale
```

Используется:

```python
max_iter = 1000
```

### RandomForestRegressor

Перебирается:

- `n_estimators`: 200 ... 700;
- `max_depth`: 4 ... 24;
- `min_samples_leaf`: 1 ... 15;
- `max_features`: `sqrt`, `0.5`, `0.8`, `1.0`.

### ExtraTreesRegressor

Перебирается:

- `n_estimators`: 200 ... 700;
- `max_depth`: 4 ... 28;
- `min_samples_leaf`: 1 ... 12;
- `max_features`: `sqrt`, `0.5`, `0.8`, `1.0`.

### HistGradientBoostingRegressor

Перебирается:

- `loss`: `squared_error` или `poisson`;
- `learning_rate`: 0.01 ... 0.2;
- `max_iter`: 100 ... 800;
- `max_leaf_nodes`: 15 ... 95;
- `min_samples_leaf`: 5 ... 50;
- `l2_regularization`: 0.0 ... 10.0.

### SARIMAX

Перебирается:

```python
order = (p, d, q)
p: 0 ... 2
d: 0 ... 1
q: 0 ... 2
```

и сезонная часть:

```python
seasonal_order = (P, D, Q, 7)
P: 0 ... 1
D: 0 ... 1
Q: 0 ... 1
```

SARIMAX обучается не на всех рядах, а на наиболее крупных рядах, ограниченных:

```python
ARIMA_MAX_SERIES = 40
```

Для слабых или коротких рядов используется fallback-прогноз по средним значениям дней недели.

## Валидация Optuna

Для подбора гиперпараметров используются временные фолды:

```python
n_splits = 3
valid_days = 14
```

Фолды идут по времени, без перемешивания.

На текущем прогоне лучший CV-результат:

```text
Best MAE: 0.2346230158730159
```

Лучшим по CV оказался `hist_gradient_boosting`, но на holdout он оказался хуже, чем `ridge`.

## Итоговые результаты на holdout

Лучший результат на holdout показала модель:

```text
optuna_ridge
```

Метрики:

```text
MAE  = 0.277530
RMSE = 0.563656
WAPE = 1.376384
```

Сравнение основных результатов:

| model_name | MAE | RMSE | WAPE |
|---|---:|---:|---:|
| `optuna_ridge` | 0.277530 | 0.563656 | 1.376384 |
| `optuna_poisson` | 0.309524 | 0.590097 | 1.535055 |
| `baseline_rolling_mean_7` | 0.327381 | 0.605038 | 1.623616 |
| `optuna_sarimax` | 0.332589 | 0.608105 | 1.649446 |
| `optuna_hist_gradient_boosting` | 0.334821 | 0.611156 | 1.660517 |
| `baseline_series_weekday_mean` | 0.338542 | 0.609327 | 1.678967 |
| `optuna_extra_trees` | 0.344494 | 0.617816 | 1.708487 |
| `optuna_random_forest` | 0.359375 | 0.630924 | 1.782288 |

Вывод по текущему запуску: лучшая модель для сохранения и инференса - `optuna_ridge`.

## Что сохраняет ноутбук

В конце ноутбук формирует словарь `artifact`:

```python
artifact = {
    'model': final_model,
    'best_params': best_params,
    'feature_cols': feature_cols,
    'cat_features': cat_features,
    'num_features': num_features,
    'target_col': target_col,
    'date_col': DATE_COL,
    'product_col': PRODUCT_COL,
    'category_col': CATEGORY_COL,
    'series_keys': series_keys,
    'history_daily': ts,
    'train_end_date': str(features['date'].max().date()),
    'horizon_days': HORIZON_DAYS,
    'arima_max_series': ARIMA_MAX_SERIES,
    'model_results': model_results,
    'series_metrics': series_metrics,
}
```

Самые важные поля:

- `model` - обученная модель или коллекция SARIMAX-моделей;
- `feature_cols` - список признаков, которые нужны для `predict`;
- `series_keys` - список рядов `product × final_category`, для которых нужно делать прогноз;
- `history_daily` - подготовленная история рядов по дням;
- `horizon_days` - горизонт прогноза, сейчас 7 дней;
- `model_results` - таблица сравнения моделей;
- `series_metrics` - метрики по каждому ряду.

## Что делает `tickets_time_series_predict.py`

Скрипт нужен для прогноза без повторного обучения.

Он использует только `.pkl`-артефакт, созданный ноутбуком.

Текущие константы в скрипте:

```python
ARTIFACT_PATH = "tickets_time_series_artifacts.pkl"
OUTPUT_PATH = "tickets_week_forecast_from_artifact.xlsx"
```

Это значит:

- входной `.pkl` должен лежать рядом со скриптом;
- результат будет сохранен рядом со скриптом;
- исходный Excel-файл скрипту не нужен.

## Что принимает `.py`

Скрипт принимает один неявный вход:

```text
tickets_time_series_artifacts.pkl
```

Он не принимает:

- Excel-файл;
- CSV-файл;
- путь через аргументы командной строки;
- новый датасет;
- дату старта прогноза;
- горизонт прогноза через CLI.

Горизонт берется из артефакта:

```python
horizon_days = artifact["horizon_days"]
```

Сейчас это 7 дней.

## Что должно быть внутри `.pkl`

Скрипт ожидает следующие ключи:

- `model`;
- `feature_cols`;
- `product_col`;
- `category_col`;
- `horizon_days`;
- `series_keys`;
- `history_daily`.

Если какого-то ключа нет, скрипт упадет с `KeyError`.

Именно поэтому ему не нужен исходный Excel.

## Как работает прогноз в `.py`

### Если модель SARIMAX

Если:

```python
isinstance(model, dict) and model.get("kind") == "sarimax"
```

то скрипт:

- строит будущие даты;
- для каждого `series_id` берет обученную SARIMAX-модель;
- если модели для ряда нет, использует fallback по средним значениям дней недели;
- клипует отрицательные прогнозы в 0;
- округляет прогнозы до целых через распределение дробных частей.

### Если модель sklearn Pipeline

Для обычной sklearn-модели скрипт работает рекурсивно:

1. Берет последнюю дату из `history_daily`.
2. Создает строки для следующего дня по всем `series_id`.
3. Ставит для будущего дня `tickets = NaN`.
4. Склеивает историю и будущие строки.
5. Пересчитывает признаки через `add_lag_features`.
6. Делает `model.predict`.
7. Клипует отрицательные значения в 0.
8. Округляет прогнозы до целых.
9. Подставляет `prediction_rounded` обратно в историю как `tickets`.
10. Переходит к следующему дню.

Так повторяется `horizon_days` раз.

## Формат результата `.py`

Скрипт сохраняет Excel:

```text
tickets_week_forecast_from_artifact.xlsx
```

Внутри два листа.

### Лист `forecast_long`

Длинный формат прогноза.

Колонки:

- `date` - прогнозная дата;
- `product` - продукт;
- `final_category` - категория;
- `series_id` - строковый идентификатор ряда;
- `prediction` - сырой вещественный прогноз модели;
- `prediction_rounded` - целочисленный прогноз после округления.

Пример структуры:

| date | product | final_category | series_id | prediction | prediction_rounded |
|---|---|---|---|---:|---:|
| 2026-05-19 | API интеграция | вопрос по оплате | API интеграция \| вопрос по оплате | 0.19 | 0 |

### Лист `forecast_pivot`

Широкий формат прогноза.

Строки:

- `product`;
- `final_category`.

Колонки:

- даты прогноза;
- `week_total`.

Значения:

- сумма `prediction_rounded` по соответствующей дате и категории.

## Зависимости

Минимально нужны:

- `python`;
- `pandas`;
- `numpy`;
- `joblib`;
- `scikit-learn`;
- `openpyxl`;

Для ноутбука дополнительно:

- `optuna`;
- `matplotlib`;
- `statsmodels`;

Пример установки:

```powershell
python -m pip install pandas numpy joblib scikit-learn openpyxl optuna matplotlib statsmodels
```

## Важное про версии `scikit-learn`

Файл `.pkl`, сохраненный через `joblib`, содержит sklearn-объекты:

- `Pipeline`;
- `ColumnTransformer`;
- `SimpleImputer`;
- `OneHotEncoder`;
- `StandardScaler`;
- конкретную модель.

`scikit-learn` не гарантирует совместимость pickle/joblib-артефактов между разными версиями.

Установить конкретную версию:

```powershell
python -m pip install --force-reinstall scikit-learn==1.6.1
```

Если установка `scikit-learn==1.6.1` пытается собирать пакет из исходников и падает на Windows с ошибкой компилятора, вероятно, используется слишком новая версия Python, для которой нет готового wheel. В таком случае лучше создать окружение на Python 3.11 или 3.12.


## Что делать при новых данных

`tickets_time_series_predict.py` не обновляет историю из Excel.

Он использует только `history_daily`, сохраненный внутри `.pkl`.

Если появились новые фактические тикеты:

1. Обновить Excel-файл.
2. Заново прогнать `tickets_time_series.ipynb`.
3. Получить новый `tickets_time_series_artifacts.pkl`.
4. Запустить `tickets_time_series_predict.py` уже с новым `.pkl`.

Без переобучения или обновления артефакта скрипт будет прогнозировать от старой последней даты, которая была сохранена внутри `.pkl`.
