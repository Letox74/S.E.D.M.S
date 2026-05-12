import lightgbm as lgbm
import optuna
from sklearn.metrics import root_mean_squared_error

optuna.logging.set_verbosity(optuna.logging.CRITICAL)


def _get_trials(analytics_count: int) -> int:
    mapping_dict = {
        analytics_count < 5_000: 50,
        analytics_count < 10_000: 45,
        analytics_count < 100_000: 40,
        analytics_count <= 500_000: 35,
        analytics_count > 500_000: 20
    }

    return mapping_dict[True]


async def optimize_regression_model(
        analytics_count: int,
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test
) -> tuple[lgbm.LGBMRegressor, dict[str, int | float]]:
    def objective(trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 1_000),
            "max_depth": trial.suggest_int("max_depth", 2, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.25, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 15, 150),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 100),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
            "min_gain_to_split": trial.suggest_float("min_gain_to_split", 0.2, 0.8),
            "verbosity": -1,
            "cat_features": ["type"],
            "n_jobs": 4,
            "random_state": 42
        }

        lgbm_model = lgbm.LGBMRegressor(**params)
        lgbm_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                       callbacks=[lgbm.callback.early_stopping(25, verbose=False), lgbm.log_evaluation(period=0)])

        preds = lgbm_model.predict(X_test)
        return root_mean_squared_error(y_test, preds)

    # create the study
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=_get_trials(analytics_count), n_jobs=4, timeout=60 * 30)  # 30 minutes

    # train final model
    lgbm_model = lgbm.LGBMRegressor(**study.best_params, verbosity=-1, cat_features=["type"], n_jobs=4, random_state=42)
    lgbm_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
                   callbacks=[lgbm.callback.early_stopping(25, verbose=False), lgbm.log_evaluation(period=0)])

    return lgbm_model, study.best_params
