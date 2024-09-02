import streamlit as st 

import pandas as pd 

import numpy as np 

import matplotlib.pyplot as plt 

import xgboost as xgb 

from sklearn.metrics import mean_squared_error 

from scipy import stats 

from io import BytesIO 

import base64 

import matplotlib.backends.backend_pdf 

 

# Set page config 

st.set_page_config(page_title="Brand Price Analysis", layout="wide") 

 

# Initialize session state 

if 'df' not in st.session_state: 

    st.session_state.df = None 

if 'district_benchmarks' not in st.session_state: 

    st.session_state.district_benchmarks = {} 

 

def transform_data(df): 

    brands = ['UTCL', 'JKS', 'JKLC', 'Ambuja', 'Wonder', 'Shree'] 

    transformed_df = df[['Zone', 'REGION', 'Dist Code', 'Dist Name']].copy() 

    brand_columns = [col for col in df.columns if any(brand in col for brand in brands)] 

    num_weeks = len(brand_columns) // len(brands) 

    month_names = ['June', 'July', 'August', 'September', 'October', 'November', 'December', 

                   'January', 'February', 'March', 'April', 'May'] 

    month_index = 0 

    week_counter = 1 

 

    for i in range(num_weeks): 

        start_idx = i * len(brands) 

        end_idx = (i + 1) * len(brands) 

        week_data = df[brand_columns[start_idx:end_idx]] 

        if i == 0: 

            week_name = month_names[month_index] 

            month_index += 1 

        elif i == 1: 

            week_name = month_names[month_index] 

            month_index += 1 

        else: 

            week_name = f"W-{week_counter} {month_names[month_index]}" 

            if week_counter == 4: 

                week_counter = 1 

                month_index += 1 

            else: 

                week_counter += 1 

        week_data = week_data.rename(columns={col: f"{brand} ({week_name})" for brand, col in zip(brands, week_data.columns)}) 

        week_data.replace(0, np.nan, inplace=True) 

        transformed_df = pd.merge(transformed_df, week_data, left_index=True, right_index=True) 

 

    return transformed_df 

 

def plot_district_graph(df, district_name, benchmark_brands, desired_diff): 

    brands = ['UTCL', 'JKS', 'JKLC', 'Ambuja', 'Wonder', 'Shree'] 

     

    def sort_key(x): 

        months = 'June July August September October November December January February March April May'.split() 

        if 'W-' in x: 

            week, month = x.split() 

            return (months.index(month), int(week.split('-')[1])) 

        else: 

            return (months.index(x), 0) 

 

    week_names = sorted(list(set([col.split(' (')[1].split(')')[0] for col in df.columns if '(' in col])), 

                        key=sort_key) 

 

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(20, 10), gridspec_kw={'width_ratios': [3, 1]}) 

    district_df = df[df["Dist Name"] == district_name] 

    price_diffs = [] 

    stats_table_data = {} 

    predictions = {} 

 

    for brand in brands: 

        brand_prices = [district_df[f"{brand} ({week})"].iloc[0] if f"{brand} ({week})" in district_df.columns else np.nan for week in week_names] 

 

        valid_prices = [p for p in brand_prices if not np.isnan(p)] 

        if valid_prices: 

            price_diff = valid_prices[-1] - valid_prices[0] 

        else: 

            price_diff = np.nan 

        price_diffs.append(price_diff) 

        line, = ax.plot(week_names, brand_prices, marker='o', linestyle='-', label=f"{brand} ({price_diff:.0f})") 

 

        for week, price in zip(week_names, brand_prices): 

            if not np.isnan(price): 

                ax.text(week, price, str(round(price)), fontsize=8) 

 

        if valid_prices: 

            stats_table_data[brand] = { 

                'Min': np.min(valid_prices), 

                'Max': np.max(valid_prices), 

                'Average': np.mean(valid_prices), 

                'Median': np.median(valid_prices), 

                'First Quartile': np.percentile(valid_prices, 25), 

                'Third Quartile': np.percentile(valid_prices, 75), 

                'Variance': np.var(valid_prices), 

                'Skewness': pd.Series(valid_prices).skew(), 

                'Kurtosis': pd.Series(valid_prices).kurtosis() 

            } 

        else: 

            stats_table_data[brand] = {stat: np.nan for stat in ['Min', 'Max', 'Average', 'Median', 'First Quartile', 'Third Quartile', 'Variance', 'Skewness', 'Kurtosis']} 

 

        # Prediction using XGBoost 

        if len(valid_prices) > 2: 

            train_data = np.array(range(len(valid_prices))).reshape(-1, 1) 

            train_labels = np.array(valid_prices) 

            model = xgb.XGBRegressor(objective='reg:squarederror') 

            model.fit(train_data, train_labels) 

            next_week = len(valid_prices) 

            prediction = model.predict(np.array([[next_week]])) 

 

            errors = abs(model.predict(train_data) - train_labels) 

            confidence = 0.95 

            n = len(valid_prices) 

            t_crit = stats.t.ppf((1 + confidence) / 2, n - 1) 

            margin_of_error = t_crit * errors.std() / np.sqrt(n) 

            confidence_interval = (prediction - margin_of_error, prediction + margin_of_error) 

 

            predictions[brand] = { 

                'Prediction': prediction[0], 

                'Confidence Interval': confidence_interval 

            } 

        else: 

            predictions[brand] = { 

                'Prediction': np.nan, 

                'Confidence Interval': (np.nan, np.nan) 

            } 

 

    ax.set_xlabel('Month/Week', weight='bold') 

    ax.set_ylabel('Whole Sale Price (in Rs.)', weight='bold') 

    ax.set_title(f"{district_name} - Brands Price Trend", weight='bold') 

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=6, prop={'weight': 'bold'}) 

    plt.setp(ax.get_xticklabels())

 

    # Benchmark brand information on the right side with improved styling 

    ax2.axis('off') 

    text_str = 'Benchmark Brands:\n\n' 

    if benchmark_brands: 

        for benchmark_brand in benchmark_brands: 

            jklc_prices = [district_df[f"JKLC ({week})"].iloc[0] for week in week_names if f"JKLC ({week})" in district_df.columns] 

            benchmark_prices = [district_df[f"{benchmark_brand} ({week})"].iloc[0] for week in week_names if f"{benchmark_brand} ({week})" in district_df.columns] 

            actual_diff = np.nan 

            if jklc_prices and benchmark_prices: 

                for i in range(len(jklc_prices) - 1, -1, -1): 

                    if not np.isnan(jklc_prices[i]) and not np.isnan(benchmark_prices[i]): 

                        actual_diff = jklc_prices[i] - benchmark_prices[i] 

                        break 

 

            brand_text = f"╔══ {benchmark_brand} ══╗\n" 

            brand_text += f"║ Actual Diff: {actual_diff:+.2f} Rs. ║\n" 

            if benchmark_brand in desired_diff and desired_diff[benchmark_brand] is not None: 

                brand_desired_diff = desired_diff[benchmark_brand] 

                brand_text += f"║ Desired Diff: {brand_desired_diff:+.2f} Rs. ║\n" 

                required_increase_decrease = brand_desired_diff - actual_diff 

                brand_text += f"║ Required Change: {required_increase_decrease:+.2f} Rs. ║\n" 

            brand_text += "╚" + "═" * (len(benchmark_brand) + 6) + "╝\n\n" 

 

            text_str += brand_text 

 

    ax2.text(0, 0.95, text_str, va='top', ha='left', transform=ax2.transAxes, family='monospace', fontsize=10) 

 

    plt.tight_layout() 

    return fig, stats_table_data, predictions 

 

def generate_pdf(figs): 

    pdf_buffer = BytesIO() 

    pdf = matplotlib.backends.backend_pdf.PdfPages(pdf_buffer) 

    for fig in figs: 

        pdf.savefig(fig) 

    pdf.close() 

    return pdf_buffer 

 

def main(): 

    st.title("Brand Price Analysis") 

 

    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx") 

    if uploaded_file is not None: 

        try: 

            df = pd.read_excel(uploaded_file, skiprows=2) 

            st.session_state.df = transform_data(df) 

            st.success("File uploaded successfully!") 

        except Exception as e: 

            st.error(f"Error reading file: {e}. Please ensure it is a valid Excel file.") 

            return 

 

    if st.session_state.df is not None: 

        df = st.session_state.df 

         

        col1, col2 = st.columns(2) 

        with col1: 

            zone = st.selectbox("Select Zone", options=df["Zone"].unique()) 

        with col2: 

            region = st.selectbox("Select Region", options=df[df["Zone"] == zone]["REGION"].unique()) 

 

        districts = df[(df["Zone"] == zone) & (df["REGION"] == region)]["Dist Name"].unique() 

        selected_districts = st.multiselect("Select Districts", options=districts) 

 

        benchmark_brands = ['UTCL', 'JKS', 'Ambuja', 'Wonder', 'Shree'] 

 

        # Create a form for each selected district 

        for district in selected_districts: 

            with st.expander(f"Set benchmark brands for {district}"): 

                st.session_state.district_benchmarks[district] = {} 

                selected_benchmarks = st.multiselect(f"Select Benchmark Brands for {district}", options=benchmark_brands) 

                for brand in selected_benchmarks: 

                    st.session_state.district_benchmarks[district][brand] = st.number_input(f"Desired Diff for {brand} in {district}", value=0) 

 

        if st.button("Generate Analysis"): 

            if selected_districts: 

                figs = [] 

                all_stats = {} 

                all_predictions = {} 

                for district in selected_districts: 

                    fig, stats, predictions = plot_district_graph( 

                        df,  

                        district,  

                        st.session_state.district_benchmarks[district].keys(), 

                        st.session_state.district_benchmarks[district] 

                    ) 

                    figs.append(fig) 

                    all_stats[district] = stats 

                    all_predictions[district] = predictions 

                    st.pyplot(fig) 

 

                # Generate PDF with all plots 

                pdf_buffer = generate_pdf(figs) 

                 

                # Download buttons 

                st.download_button( 

                    label="Download All Plots as PDF", 

                    data=pdf_buffer, 

                    file_name="all_plots.pdf", 

                    mime="application/pdf" 

                ) 

 

                # PNG download buttons for individual plots 

                for i, district in enumerate(selected_districts): 

                    png_buffer = BytesIO() 

                    figs[i].savefig(png_buffer, format='png') 

                    png_buffer.seek(0) 

                    st.download_button( 

                        label=f"Download {district} Plot as PNG", 

                        data=png_buffer, 

                        file_name=f"{district}_plot.png", 

                        mime="image/png", 

                        key=f"png_{district}" 

                    ) 

 

                # Display stats and predictions 

                for district in selected_districts: 

                    st.write(f"### Statistics for {district}") 

                    st.dataframe(pd.DataFrame(all_stats[district]).transpose().round(2)) 

 

                    st.write(f"### Predictions for {district}") 

                    st.dataframe(pd.DataFrame(all_predictions[district]).transpose()) 

 

            else: 

                st.warning("Please select at least one district.") 

 

if __name__ == "__main__": 

    main() 
