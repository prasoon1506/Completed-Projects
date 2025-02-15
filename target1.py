import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
from io import BytesIO
import base64
from concurrent.futures import ThreadPoolExecutor
from sklearn.model_selection import GridSearchCV
def preprocess_data(df):
    months = ['Apr', 'May', 'June', 'July', 'Aug', 'Sep']
    for month in months:
        df[f'Achievement({month})'] = df[f'Monthly Achievement({month})'] / df[f'Month Tgt ({month})']
        df[f'Target({month})'] = df[f'Month Tgt ({month})']
    df['PrevYearSep'] = df['Total Sep 2023']
    df['PrevYearOct'] = df['Total Oct 2023']
    df['YoYGrowthSep'] = (df['Monthly Achievement(Sep)'] - df['PrevYearSep']) / df['PrevYearSep']
    df['ZoneBrand'] = df['Zone'] + '_' + df['Brand']
    df['CumulativeAchievement'] = df[[f'Achievement({month})' for month in months]].sum(axis=1)
    df['TrendSlope'] = np.polyfit(range(len(months)), df[[f'Achievement({month})' for month in months]].values.T, 1)[0]
    df['LastMonthAchievement'] = df['Achievement(Sep)']
    df['LastTwoMonthsAvgAchievement'] = df[['Achievement(Aug)', 'Achievement(Sep)']].mean(axis=1)
    numeric_features = [f'Achievement({month})' for month in months] + \[f'Target({month})' for month in months] + \['PrevYearSep', 'PrevYearOct', 'YoYGrowthSep', 'CumulativeAchievement', 'TrendSlope', 'LastMonthAchievement', 'LastTwoMonthsAvgAchievement']
    categorical_features = ['ZoneBrand']
    feature_columns = numeric_features + categorical_features
    target_column = 'Month Tgt (Oct)'
    return df, feature_columns, target_column, numeric_features, categorical_features
def create_pipeline(numeric_features, categorical_features):
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    preprocessor = ColumnTransformer(
        transformers=[('num', numeric_transformer, numeric_features),('cat', categorical_transformer, categorical_features)])
    xgb_pipeline = Pipeline([('preprocessor', preprocessor),('regressor', xgb.XGBRegressor(random_state=42))])
    gb_pipeline = Pipeline([('preprocessor', preprocessor),('regressor', GradientBoostingRegressor(random_state=42))])
    rf_pipeline = Pipeline([('preprocessor', preprocessor),('regressor', RandomForestRegressor(random_state=42))])
    return xgb_pipeline, gb_pipeline, rf_pipeline
def hyperparameter_tuning(pipeline, X, y):
    if isinstance(pipeline.named_steps['regressor'], xgb.XGBRegressor):
        param_grid = {'regressor__n_estimators': [100, 200, 300],'regressor__max_depth': [3, 5, 7],'regressor__learning_rate': [0.01, 0.1, 0.3]}
    elif isinstance(pipeline.named_steps['regressor'], GradientBoostingRegressor):
        param_grid = {'regressor__n_estimators': [100, 200, 300],'regressor__max_depth': [3, 5, 7],'regressor__learning_rate': [0.01, 0.1, 0.3]}
    elif isinstance(pipeline.named_steps['regressor'], RandomForestRegressor):
        param_grid = {'regressor__n_estimators': [100, 200, 300],'regressor__max_depth': [3, 5, 7],'regressor__min_samples_split': [2, 5, 10]}
    else:
        raise ValueError("Unknown regressor type")
    grid_search = GridSearchCV(pipeline, param_grid, cv=5, n_jobs=-1, scoring='neg_mean_squared_error')
    grid_search.fit(X, y)
    return grid_search.best_estimator_
def train_model(X, y, xgb_pipeline, gb_pipeline, rf_pipeline):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    with st.spinner("Tuning XGBoost model..."):
        xgb_pipeline = hyperparameter_tuning(xgb_pipeline, X_train, y_train)
    with st.spinner("Tuning Gradient Boosting model..."):
        gb_pipeline = hyperparameter_tuning(gb_pipeline, X_train, y_train)
    with st.spinner("Tuning Random Forest model..."):
        rf_pipeline = hyperparameter_tuning(rf_pipeline, X_train, y_train)
    models = [xgb_pipeline, gb_pipeline, rf_pipeline]
    model_names = ['XGBoost', 'Gradient Boosting', 'Random Forest']
    for name, model in zip(model_names, models):
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
        rmse_scores = np.sqrt(-cv_scores)
        st.write(f"{name} Cross-validation RMSE: {rmse_scores.mean():.4f} (+/- {rmse_scores.std() * 2:.4f})")
    return xgb_pipeline, gb_pipeline, rf_pipeline
def predict_sales(df, region, brand, xgb_pipeline, gb_pipeline, rf_pipeline, feature_columns):
    region_data = df[(df['Zone'] == region) & (df['Brand'] == brand)].copy()
    if len(region_data) > 0:
        X_pred = region_data[feature_columns].iloc[-1:] 
        xgb_pred = xgb_pipeline.predict(X_pred)[0]
        gb_pred = gb_pipeline.predict(X_pred)[0]
        rf_pred = rf_pipeline.predict(X_pred)[0]
        ensemble_pred = (xgb_pred + gb_pred + rf_pred) / 3
        predictions = [xgb_pred, gb_pred, rf_pred]
        confidence_interval = 1.96 * np.std(predictions) / np.sqrt(len(predictions))
        return ensemble_pred, ensemble_pred - confidence_interval, ensemble_pred + confidence_interval
    else:
        return None, None, None
def generate_combined_report(df, regions, brands, xgb_pipeline, gb_pipeline, rf_pipeline, feature_columns):
    main_table_data = [['Region', 'Brand', 'Month Target\n(Oct)', 'Monthly Achievement\n(Sep)', 'Predicted\nAchievement(Oct)', 'CI', 'RMSE']]
    with ThreadPoolExecutor() as executor:
        futures = []
        for region in regions:
            for brand in brands:
                futures.append(executor.submit(predict_sales, df, region, brand, xgb_pipeline, gb_pipeline, rf_pipeline, feature_columns))
        valid_data = False
        for future, (region, brand) in zip(futures, [(r, b) for r in regions for b in brands]):
            try:
                oct_achievement, lower_achievement, upper_achievement = future.result()
                if oct_achievement is not None:
                    region_data = df[(df['Zone'] == region) & (df['Brand'] == brand)]
                    if not region_data.empty:
                        oct_target = region_data['Month Tgt (Oct)'].iloc[-1]
                        sept_achievement = region_data['Monthly Achievement(Sep)'].iloc[-1]
                        rmse = np.sqrt(mean_squared_error(region_data['Monthly Achievement(Sep)'], region_data['Month Tgt (Sep)']))
                        main_table_data.append([region, brand, f"{oct_target:.0f}", f"{sept_achievement:.0f}",f"{oct_achievement:.0f}", f"({lower_achievement:.2f},\n{upper_achievement:.2f})", f"{rmse:.4f}"])
                        valid_data = True
                    else:
                        st.warning(f"No data available for {region} and {brand}")
            except Exception as e:
                st.warning(f"Error processing {region} and {brand}: {str(e)}")
    if valid_data:
        fig, ax = plt.subplots(figsize=(12, len(main_table_data) * 0.5))
        ax.axis('off')
        table = ax.table(cellText=main_table_data[1:], colLabels=main_table_data[0], cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(fontweight='bold', color='white')
                cell.set_facecolor('#4CAF50')
            elif row % 2 == 0:
                cell.set_facecolor('#f2f2f2')
            cell.set_edgecolor('white')
        plt.title("Combined Sales Predictions Report", fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        pdf_buffer = BytesIO()
        plt.savefig(pdf_buffer, format='pdf', bbox_inches='tight')
        plt.close(fig)
        pdf_buffer.seek(0)
        return base64.b64encode(pdf_buffer.getvalue()).decode()
    else:
        st.warning("No valid data available for any region and brand combination.")
        return None
def combined_report_app():
    st.title("📊 Improved Sales Prediction Report Generator")
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        try:
            with st.spinner("Loading and processing data..."):
                df = pd.read_excel(uploaded_file)
                regions = df['Zone'].unique().tolist()
                brands = df['Brand'].unique().tolist()
                df, feature_columns, target_column, numeric_features, categorical_features = preprocess_data(df)
                X = df[feature_columns]
                y = df[target_column]
                xgb_pipeline, gb_pipeline, rf_pipeline = create_pipeline(numeric_features, categorical_features)
                sample_size = min(1000, len(X))
                X_sample = X.sample(n=sample_size, random_state=42)
                y_sample = y.loc[X_sample.index]
                xgb_pipeline, gb_pipeline, rf_pipeline = train_model(X_sample, y_sample, xgb_pipeline, gb_pipeline, rf_pipeline)
            st.success("Data processed and models trained successfully!")
            if st.button("Generate Combined Report"):
                with st.spinner("Generating combined report..."):
                    combined_report_data = generate_combined_report(df, regions, brands, xgb_pipeline, gb_pipeline, rf_pipeline, feature_columns)
                if combined_report_data:
                    st.success("Combined report generated successfully!")
                    st.download_button(label="Download Combined PDF Report",data=base64.b64decode(combined_report_data),file_name="combined_prediction_report.pdf",mime="application/pdf")
                else:
                    st.error("Unable to generate combined report. Please check the warnings above for more details.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.exception(e)
if __name__ == "__main__":
    combined_report_app()
