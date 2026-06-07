import joblib
import numpy as np
import pandas as pd
import sklearn


ARTIFACT_PATH = "tickets_time_series_artifacts.pkl"
OUTPUT_PATH = "tickets_week_forecast_from_artifact.xlsx"

def add_time_features(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["dayofweek"] = result["date"].dt.dayofweek
    result["dayofmonth"] = result["date"].dt.day
    result["weekofyear"] = result["date"].dt.isocalendar().week.astype(int)
    result["month"] = result["date"].dt.month
    result["quarter"] = result["date"].dt.quarter
    result["is_month_start"] = result["date"].dt.is_month_start.astype(int)
    result["is_month_end"] = result["date"].dt.is_month_end.astype(int)
    result["is_weekend"] = result["dayofweek"].isin([5, 6]).astype(int)
    result["days_from_start"] = (result["date"] - result["date"].min()).dt.days

    result["dow_sin"] = np.sin(2 * np.pi * result["dayofweek"] / 7)
    result["dow_cos"] = np.cos(2 * np.pi * result["dayofweek"] / 7)
    result["month_sin"] = np.sin(2 * np.pi * result["month"] / 12)
    result["month_cos"] = np.cos(2 * np.pi * result["month"] / 12)
    return result


def add_aggregate_history_features(
    data: pd.DataFrame,
    product_col: str,
    category_col: str,
) -> pd.DataFrame:
    result = data.copy()

    daily_total = result.groupby("date", as_index=False)["tickets"].sum(min_count=1).sort_values("date")
    shifted_total = daily_total["tickets"].shift(1)
    daily_total["global_lag_1"] = shifted_total
    daily_total["global_rolling_mean_7"] = shifted_total.rolling(7).mean()
    daily_total["global_rolling_mean_28"] = shifted_total.rolling(28).mean()
    result = result.merge(daily_total.drop(columns="tickets"), on="date", how="left")

    for group_col, prefix in [(product_col, "product"), (category_col, "category")]:
        aggregate = (
            result.groupby([group_col, "date"], as_index=False)["tickets"]
            .sum(min_count=1)
            .sort_values([group_col, "date"])
        )
        shifted = aggregate.groupby(group_col)["tickets"].shift(1)
        aggregate[f"{prefix}_lag_1"] = shifted
        aggregate[f"{prefix}_rolling_mean_7"] = (
            shifted.groupby(aggregate[group_col]).rolling(7).mean().reset_index(level=0, drop=True)
        )
        aggregate[f"{prefix}_rolling_mean_28"] = (
            shifted.groupby(aggregate[group_col]).rolling(28).mean().reset_index(level=0, drop=True)
        )
        result = result.merge(aggregate.drop(columns="tickets"), on=[group_col, "date"], how="left")

    return result


def add_lag_features(data: pd.DataFrame, product_col: str, category_col: str) -> pd.DataFrame:
    result = data.sort_values(["series_id", "date"]).copy()
    grouped = result.groupby("series_id")["tickets"]

    for lag in [1, 2, 3, 4, 5, 6, 7, 14, 21, 28, 35, 42, 56]:
        result[f"lag_{lag}"] = grouped.shift(lag)

    shifted = grouped.shift(1)
    for window in [3, 7, 14, 28, 56]:
        rolling = shifted.groupby(result["series_id"]).rolling(window)
        result[f"rolling_mean_{window}"] = (
            rolling.mean().reset_index(level=0, drop=True)
        )
        result[f"rolling_median_{window}"] = (
            rolling.median().reset_index(level=0, drop=True)
        )
        result[f"rolling_std_{window}"] = (
            rolling.std().reset_index(level=0, drop=True)
        )
        result[f"rolling_min_{window}"] = (
            rolling.min().reset_index(level=0, drop=True)
        )
        result[f"rolling_max_{window}"] = (
            rolling.max().reset_index(level=0, drop=True)
        )
        result[f"rolling_nonzero_share_{window}"] = (
            shifted.gt(0)
            .astype(float)
            .groupby(result["series_id"])
            .rolling(window)
            .mean()
            .reset_index(level=0, drop=True)
        )

    result["ewm_mean_7"] = shifted.groupby(result["series_id"]).transform(
        lambda series: series.ewm(span=7, adjust=False).mean()
    )
    result["ewm_mean_28"] = shifted.groupby(result["series_id"]).transform(
        lambda series: series.ewm(span=28, adjust=False).mean()
    )
    result["diff_1"] = result["lag_1"] - result["lag_2"]
    result["diff_7"] = result["lag_7"] - result["lag_14"]
    result["ratio_lag_1_to_mean_7"] = result["lag_1"] / (result["rolling_mean_7"] + 1)
    result["ratio_mean_7_to_mean_28"] = result["rolling_mean_7"] / (result["rolling_mean_28"] + 1)
    result["expanding_mean"] = (
        shifted.groupby(result["series_id"])
        .expanding()
        .mean()
        .reset_index(level=0, drop=True)
    )
    result["expanding_nonzero_share"] = (
        shifted.gt(0)
        .astype(float)
        .groupby(result["series_id"])
        .expanding()
        .mean()
        .reset_index(level=0, drop=True)
    )
    result["series_age_days"] = result.groupby("series_id").cumcount()

    last_nonzero_date = (
        result["date"]
        .where(result["tickets"].gt(0))
        .groupby(result["series_id"])
        .ffill()
        .groupby(result["series_id"])
        .shift(1)
    )
    result["days_since_nonzero"] = (result["date"] - last_nonzero_date).dt.days
    result["days_since_nonzero"] = result["days_since_nonzero"].fillna(
        result["series_age_days"] + 1
    )

    result = add_aggregate_history_features(result, product_col, category_col)
    return add_time_features(result)


def arima_fallback_forecast(y_train: pd.Series, horizon: int) -> np.ndarray:
    if y_train.empty:
        return np.zeros(horizon)

    recent_mean = y_train.tail(7).mean()
    weekday_means = y_train.groupby(y_train.index.dayofweek).mean()
    future_dates = pd.date_range(
        y_train.index.max() + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )
    values = [weekday_means.get(date.dayofweek, recent_mean) for date in future_dates]
    return np.nan_to_num(
        np.asarray(values, dtype=float),
        nan=recent_mean if pd.notna(recent_mean) else 0.0,
    )


def allocate_daily_integer_predictions(
    forecast: pd.DataFrame,
    prediction_col: str = "prediction",
    output_col: str = "prediction_rounded",
) -> pd.DataFrame:
    result = forecast.copy()
    result["_base_prediction"] = np.floor(result[prediction_col]).astype(int)
    result["_fraction"] = result[prediction_col] - result["_base_prediction"]
    result[output_col] = result["_base_prediction"]

    for _, day_part in result.groupby("date", sort=False):
        daily_target = int(np.rint(day_part[prediction_col].sum()))
        daily_current = int(day_part[output_col].sum())
        to_add = max(daily_target - daily_current, 0)
        if to_add:
            add_index = day_part.sort_values("_fraction", ascending=False).head(to_add).index
            result.loc[add_index, output_col] += 1

    return result.drop(columns=["_base_prediction", "_fraction"])


def make_future_forecast(artifact: dict) -> pd.DataFrame:
    model = artifact["model"]
    feature_cols = artifact["feature_cols"]
    product_col = artifact["product_col"]
    category_col = artifact["category_col"]
    horizon_days = artifact["horizon_days"]
    series_keys = artifact["series_keys"]

    history_cols = [product_col, category_col, "date", "series_id", "tickets"]
    history_ext = artifact["history_daily"][history_cols].copy()
    history_ext["date"] = pd.to_datetime(history_ext["date"])

    if isinstance(model, dict) and model.get("kind") == "sarimax":
        future_dates = pd.date_range(
            history_ext["date"].max() + pd.Timedelta(days=1),
            periods=horizon_days,
            freq="D",
        )
        forecasts = []
        for _, row in series_keys.iterrows():
            series_id = row["series_id"]
            y_train = (
                history_ext[history_ext["series_id"] == series_id]
                .set_index("date")["tickets"]
                .sort_index()
                .asfreq("D")
                .fillna(0)
            )
            if series_id in model["models"]:
                pred = model["models"][series_id].forecast(steps=horizon_days).values
            else:
                pred = arima_fallback_forecast(y_train, horizon_days)
            forecasts.append(
                pd.DataFrame(
                    {
                        "date": future_dates,
                        product_col: row[product_col],
                        category_col: row[category_col],
                        "series_id": series_id,
                        "prediction": np.clip(pred, 0, None),
                    }
                )
            )

        result = pd.concat(forecasts, ignore_index=True)
        return allocate_daily_integer_predictions(result)

    forecasts = []

    for _ in range(horizon_days):
        next_date = history_ext["date"].max() + pd.Timedelta(days=1)
        future_rows = series_keys.copy()
        future_rows["date"] = next_date
        future_rows["tickets"] = np.nan

        tmp = pd.concat([history_ext, future_rows], ignore_index=True, sort=False)
        tmp_features = add_lag_features(tmp, product_col, category_col)
        pred_rows = tmp_features[tmp_features["date"] == next_date].copy()
        pred_rows["prediction"] = np.clip(model.predict(pred_rows[feature_cols]), 0, None)
        pred_rows = allocate_daily_integer_predictions(pred_rows)
        forecasts.append(
            pred_rows[
                ["date", product_col, category_col, "series_id", "prediction", "prediction_rounded"]
            ]
        )

        future_rows["tickets"] = pred_rows["prediction_rounded"].values
        history_ext = pd.concat([history_ext, future_rows[history_cols]], ignore_index=True)

    return pd.concat(forecasts, ignore_index=True)


def main() -> None:
    artifact = joblib.load(ARTIFACT_PATH)
    forecast = make_future_forecast(artifact)

    product_col = artifact["product_col"]
    category_col = artifact["category_col"]
    pivot = forecast.pivot_table(
        index=[product_col, category_col],
        columns="date",
        values="prediction_rounded",
        aggfunc="sum",
        fill_value=0,
    )
    pivot["week_total"] = pivot.sum(axis=1)

    with pd.ExcelWriter(OUTPUT_PATH) as writer:
        forecast.to_excel(writer, sheet_name="forecast_long", index=False)
        pivot.reset_index().to_excel(writer, sheet_name="forecast_pivot", index=False)

    print(f"Saved forecast to {OUTPUT_PATH}")


### Проверяем
print(sklearn.__version__)
main()
