import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import numpy as np
from datetime import datetime
def generate_deviation_report(df):
    output_file = 'consumption_deviation_report.xlsx'
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    workbook = writer.book

    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'font_color': 'white',
        'bg_color': '#2E86C1',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    number_format = workbook.add_format({
        'num_format': '#,##0',
        'border': 1
    })
    
    percentage_format = workbook.add_format({
        'num_format': '0.0%',
        'border': 1
    })

    # Find February 2025 column
    feb_col = None
    for col in df.columns:
        try:
            date = pd.to_datetime(col)
            if date.strftime('%Y-%m') == '2025-02':
                feb_col = col
                break
        except (ValueError, TypeError):
            continue

    # Find planned usage column
    planned_col = None
    possible_planned_cols = ['1', 1, '1.0', 1.0]
    for col in possible_planned_cols:
        if col in df.columns or str(col) in df.columns:
            planned_col = col if col in df.columns else str(col)
            break

    if planned_col is None or feb_col is None:
        raise ValueError("Required columns not found in the data")

    # Prepare report data
    report_data = []
    for _, row in df.iterrows():
        actual_usage = row[feb_col]
        planned_usage = float(row[planned_col])
        projected_till_9th = (9/28) * planned_usage
        
        # Calculate metrics
        deviation = actual_usage - projected_till_9th
        deviation_percent = (deviation / projected_till_9th * 100) if projected_till_9th != 0 else 0
        daily_rate = actual_usage / 9
        projected_month_end = daily_rate * 28
        month_end_variance = projected_month_end - planned_usage
        month_end_variance_percent = (month_end_variance / planned_usage * 100) if planned_usage != 0 else 0

        report_data.append({
            'Plant Name': row['Cement Plant Sname'],
            'Bag Name': row['MAKTX'],
            'Actual Usage (Till 9th Feb)': actual_usage,
            'Daily Average': daily_rate,
            'Projected Usage (Till 9th Feb)': projected_till_9th,
            'Deviation': deviation,
            'Deviation %': deviation_percent,
            'Full Month Plan': planned_usage,
            'Projected Month End': projected_month_end,
            'Month End Variance': month_end_variance,
            'Month End Variance %': month_end_variance_percent
        })

    # Create main report DataFrame
    report_df = pd.DataFrame(report_data)

    # Generate plant-level statistics
    plant_stats = []
    for plant in report_df['Plant Name'].unique():
        plant_data = report_df[report_df['Plant Name'] == plant]
        
        stats = {
            'Plant Name': plant,
            'Total Bag Types': len(plant_data),
            'Total Actual Usage': plant_data['Actual Usage (Till 9th Feb)'].sum(),
            'Total Planned Usage': plant_data['Full Month Plan'].sum(),
            'Average Daily Usage': plant_data['Daily Average'].sum(),
            'Average Deviation %': plant_data['Deviation %'].mean(),
            'Projected Month End Total': plant_data['Projected Month End'].sum(),
            'Overall Month End Variance %': ((plant_data['Projected Month End'].sum() - 
                                           plant_data['Full Month Plan'].sum()) / 
                                          plant_data['Full Month Plan'].sum() * 100)
        }
        plant_stats.append(stats)

    plant_stats_df = pd.DataFrame(plant_stats)

    # Write Plant Statistics sheet
    plant_stats_df.to_excel(writer, sheet_name='Plant Statistics', index=False)
    plant_stats_sheet = writer.sheets['Plant Statistics']
    
    # Format Plant Statistics sheet
    for col_num, value in enumerate(plant_stats_df.columns.values):
        plant_stats_sheet.write(0, col_num, value, header_format)
    
    plant_stats_sheet.set_column('A:A', 20)  # Plant name
    plant_stats_sheet.set_column('B:H', 15)  # Numeric columns
    
    # Set print settings for Plant Statistics
    plant_stats_sheet.set_paper(9)  # A4 paper
    plant_stats_sheet.set_portrait()
    plant_stats_sheet.repeat_rows(0)  # Repeat header row
    plant_stats_sheet.set_print_scale(90)
    
    # Write main Deviation Report
    report_df.to_excel(writer, sheet_name='Deviation Report', index=False)
    worksheet = writer.sheets['Deviation Report']

    # Format Deviation Report
    for col_num, value in enumerate(report_df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Set column widths
    worksheet.set_column('A:B', 20)  # Plant and Bag names
    worksheet.set_column('C:K', 15)  # Numeric columns

    # Set print settings for Deviation Report
    worksheet.set_paper(9)  # A4 paper
    worksheet.set_portrait()
    worksheet.repeat_rows(0)  # Repeat header row
    worksheet.set_print_scale(90)
    worksheet.set_h_pagebreaks([])
    worksheet.set_v_pagebreaks([])
    
    # Add filters
    worksheet.autofilter(0, 0, len(report_df), len(report_df.columns)-1)

    # Create summary pivot sheet
    pivot_df = report_df.pivot_table(
        values=['Actual Usage (Till 9th Feb)', 'Projected Usage (Till 9th Feb)', 
                'Full Month Plan', 'Deviation %'],
        index=['Plant Name'],
        aggfunc={
            'Actual Usage (Till 9th Feb)': 'sum',
            'Projected Usage (Till 9th Feb)': 'sum',
            'Full Month Plan': 'sum',
            'Deviation %': 'mean'
        }
    )
    
    pivot_df.to_excel(writer, sheet_name='Summary Pivot')
    pivot_sheet = writer.sheets['Summary Pivot']
    
    # Format pivot sheet
    pivot_sheet.set_column('A:A', 20)
    pivot_sheet.set_column('B:E', 15)
    
    # Set print settings for pivot sheet
    pivot_sheet.set_paper(9)
    pivot_sheet.set_portrait()
    pivot_sheet.repeat_rows(0)
    pivot_sheet.set_print_scale(90)
    
    writer.close()
    return output_file
def format_date_for_display(date):
    if isinstance(date, str):
        date = pd.to_datetime(date)
    return date.strftime('%b %Y')
def calculate_statistics(data_df):
    stats = {'Total Usage': data_df['Usage'].sum(),'Average Monthly Usage': data_df['Usage'].mean(),'Highest Usage': data_df['Usage'].max(),'Lowest Usage': data_df['Usage'].min(),'Usage Variance': data_df['Usage'].var(),'Month-over-Month Change': (data_df['Usage'].iloc[-1] - data_df['Usage'].iloc[-2]) / data_df['Usage'].iloc[-2] * 100}
    return stats
def create_year_over_year_comparison(data_df):
    data_df['Year'] = data_df['Date'].dt.year
    data_df['Month'] = data_df['Date'].dt.month
    yearly_comparison = data_df.pivot(index='Month', columns='Year', values='Usage')
    return yearly_comparison
def prepare_correlation_data(df, selected_bags, plant_name):
    month_columns = [col for col in df.columns if col not in ['Cement Plant Sname', 'MAKTX']]
    correlation_data = {}
    for bag in selected_bags:
        bag_data = df[df['MAKTX'] == bag][month_columns].iloc[0]
        correlation_data[bag] = bag_data
    correlation_df = pd.DataFrame(correlation_data)
    return correlation_df
def main():
    st.set_page_config(page_title="Cement Plant Bag Usage Analysis",layout='wide',initial_sidebar_state='expanded')
    st.markdown("""<style>.main {padding: 2rem;}.stTitle {font-size: 2.5rem !important;padding-bottom: 2rem;}.stats-card {background-color: #f8f9fa;padding: 1.5rem;border-radius: 10px;box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);}.announcement {background-color: #e3f2fd;padding: 1rem;border-radius: 10px;border-left: 5px solid #1976d2;margin: 1rem 0;}.stTabs [data-baseweb="tab-list"] {gap: 2rem;}.stTabs [data-baseweb="tab"] {height: 4rem;}div[data-testid="stMetricValue"] {font-size: 1.8rem;}</style>""", unsafe_allow_html=True)
    st.title("📊 Cement Plant Bag Usage Analysis")
    st.markdown("""<div class='announcement'><h3>🤖 Coming Soon: AI-Powered Demand Forecasting</h3><p>We are currently developing a robust Machine Learning model for accurate demand projections. This advanced forecasting system will help optimize inventory management and improve supply chain efficiency. Stay tuned for this exciting update!</p></div>""", unsafe_allow_html=True)
    with st.sidebar:
        st.header("📁 Data Input")
        uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx', 'xls'])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            df = df.iloc[:, 1:]  # Remove the first column
            if st.sidebar.button('Generate Deviation Report'):
             output_file = generate_deviation_report(df)
             with open(output_file, 'rb') as f:
                excel_data = f.read()
             st.sidebar.download_button(label="📥 Download Deviation Report",data=excel_data,file_name="consumption_deviation_report.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
             st.sidebar.success("Report generated successfully!")
            with st.sidebar:
                st.header("🎯 Filters")
                unique_plants = sorted(df['Cement Plant Sname'].unique())
                selected_plant = st.selectbox('Select Cement Plant:', unique_plants)
                plant_bags = df[df['Cement Plant Sname'] == selected_plant]['MAKTX'].unique()
                selected_bag = st.selectbox('Select Primary Bag:', sorted(plant_bags))
                st.header("📊 Correlation Analysis")
                selected_bags_correlation = st.multiselect('Select Bags for Correlation Analysis:',sorted(plant_bags),default=[selected_bag] if selected_bag else None,help="Select multiple bags to analyze their demand correlation")
            selected_data = df[(df['Cement Plant Sname'] == selected_plant) & (df['MAKTX'] == selected_bag)]
            if not selected_data.empty:
                month_columns = [col for col in df.columns if col not in ['Cement Plant Sname', 'MAKTX']]
                all_usage_data = []
                for month in month_columns:
                    date = pd.to_datetime(month)
                    usage = selected_data[month].iloc[0]
                    all_usage_data.append({'Date': date,'Usage': usage})
                all_data_df = pd.DataFrame(all_usage_data)
                all_data_df = all_data_df.sort_values('Date')
                all_data_df['Month'] = all_data_df['Date'].apply(format_date_for_display)
                stats = calculate_statistics(all_data_df)
                st.subheader("📈 Key Metrics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💼 Total Usage", f"{stats['Total Usage']:,.0f}")
                with col2:
                    st.metric("📊 Average Monthly", f"{stats['Average Monthly Usage']:,.0f}")
                with col3:
                    st.metric("⭐ Highest Usage", f"{stats['Highest Usage']:,.0f}")
                with col4:
                    st.metric("📅 MoM Change", f"{stats['Month-over-Month Change']:,.1f}%")
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Usage Trend", "📊 Year Comparison", "🔄 Correlation Analysis", "📑 Historical Data"])
                with tab1:
                    apr_2024_date = pd.to_datetime('2024-04-01')
                    plot_data = all_data_df[all_data_df['Date'] >= apr_2024_date].copy()
                    if any(plot_data['Date'].dt.strftime('%Y-%m') == '2025-02'):
                        feb_data = plot_data[plot_data['Date'].dt.strftime('%Y-%m') == '2025-02']
                        feb_usage = feb_data['Usage'].iloc[0]
                        daily_avg = feb_usage / 9
                        projected_usage = daily_avg * 29
                        plot_data.loc[plot_data['Date'].dt.strftime('%Y-%m') == '2025-02', 'Projected'] = projected_usage
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=plot_data['Month'],y=plot_data['Usage'],name='Actual Usage',line=dict(color='#2E86C1', width=3),mode='lines+markers',marker=dict(size=10, symbol='circle')))
                    if 'Projected' in plot_data.columns:
                        fig.add_trace(go.Scatter(x=plot_data['Month'],y=plot_data['Projected'],name='Projected (Feb)',line=dict(color='#E67E22', width=2, dash='dash'),mode='lines'))
                    fig.add_shape(type="line",x0="Jan 2025",x1="Jan 2025",y0=0,y1=plot_data['Usage'].max() * 1.1,line=dict(color="#E74C3C", width=2, dash="dash"),)
                    fig.add_annotation(x="Jan 2025",y=plot_data['Usage'].max() * 1.15,text="Brand Rejuvenation<br>(15th Jan 2025)",showarrow=True,arrowhead=1,ax=0,ay=-40,font=dict(size=12, color="#E74C3C"),bgcolor="white",bordercolor="#E74C3C",borderwidth=2)
                    if any(plot_data['Month'] == 'Feb 2025'):
                        feb_data = plot_data[plot_data['Month'] == 'Feb 2025']
                        fig.add_annotation(x="Feb 2025",y=feb_data['Usage'].iloc[0],text="Till 9th Feb",showarrow=True,arrowhead=1,ax=0,ay=-40,font=dict(size=12),bgcolor="white",bordercolor="#2E86C1",borderwidth=2)
                    fig.update_layout(
                        title={'text': f'Monthly Usage Trend for {selected_bag}<br><sup>{selected_plant}</sup>','y':0.95,'x':0.5,'xanchor': 'center','yanchor': 'top','font': dict(size=20)},xaxis_title='Month',yaxis_title='Usage',legend_title='Type',hovermode='x unified',plot_bgcolor='white',paper_bgcolor='white',showlegend=True,
                        xaxis=dict(showgrid=True,gridcolor='rgba(0,0,0,0.1)',tickangle=45),
                        yaxis=dict(showgrid=True,gridcolor='rgba(0,0,0,0.1)',zeroline=True,zerolinecolor='rgba(0,0,0,0.2)'),
                        legend=dict(yanchor="top",y=0.99,xanchor="left",x=0.01,bgcolor='rgba(255, 255, 255, 0.8)'))
                    st.plotly_chart(fig, use_container_width=True)
                with tab2:
                    yearly_comparison = create_year_over_year_comparison(all_data_df)
                    fig_heatmap = px.imshow(yearly_comparison,labels=dict(x="Year", y="Month", color="Usage"),aspect="auto",color_continuous_scale="RdYlBu_r")
                    fig_heatmap.update_layout(title="Year-over-Year Usage Comparison",xaxis_title="Year",yaxis_title="Month",)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                with tab3:
                    if len(selected_bags_correlation) > 1:
                        st.subheader("Bag Demand Correlation Analysis")
                        correlation_df = prepare_correlation_data(df[df['Cement Plant Sname'] == selected_plant],selected_bags_correlation,selected_plant)
                        correlation_matrix = correlation_df.corr()
                        fig_corr = px.imshow(correlation_matrix,labels=dict(x="Bag Type", y="Bag Type", color="Correlation"),aspect="auto",color_continuous_scale="RdBu",title=f"Demand Correlation Matrix - {selected_plant}")
                        fig_corr.update_layout(width=800,height=800,)
                        st.plotly_chart(fig_corr, use_container_width=True)
                        st.subheader("Correlation Insights")
                        correlations = []
                        for i in range(len(correlation_matrix.columns)):
                            for j in range(i+1, len(correlation_matrix.columns)):
                                correlations.append({'Bag 1': correlation_matrix.columns[i],'Bag 2': correlation_matrix.columns[j],'Correlation': correlation_matrix.iloc[i,j]})
                        if correlations:
                            correlations_df = pd.DataFrame(correlations)
                            correlations_df = correlations_df.sort_values('Correlation', ascending=False)
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("Strongest Positive Correlations:")
                                st.dataframe(correlations_df[correlations_df['Correlation'] > 0].head().style.format({'Correlation': '{:.2f}'}).background_gradient(cmap='Blues'))
                            with col2:
                                st.write("Strongest Negative Correlations:")
                                st.dataframe(correlations_df[correlations_df['Correlation'] < 0].sort_values('Correlation').head().style.format({'Correlation': '{:.2f}'}).background_gradient(cmap='Reds'))
                            if not correlations_df.empty:
                                top_pair = correlations_df.iloc[0]
                                fig_scatter = px.scatter(correlation_df,x=top_pair['Bag 1'],y=top_pair['Bag 2'],title=f"Demand Relationship: {top_pair['Bag 1']} vs {top_pair['Bag 2']}")
                                fig_scatter.update_layout(xaxis_title=top_pair['Bag 1'],yaxis_title=top_pair['Bag 2'],showlegend=True,)
                                st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.info("Please select at least two bags in the sidebar for correlation analysis.")
                with tab4:
                    st.subheader("📜 Complete Historical Data")
                    display_df = pd.DataFrame({'Date': all_data_df['Date'],'Month-Year': all_data_df['Date'].apply(lambda x: x.strftime('%b %Y')),'Usage': all_data_df['Usage']})
                    display_df['% Change'] = display_df['Usage'].pct_change() * 100
                    display_df = display_df.sort_values('Date', ascending=False)
                    display_df = display_df.drop('Date', axis=1)
                    styled_df = display_df.style.format({'Usage': '{:,.2f}','% Change': '{:+.2f}%'})
                    styled_df = styled_df.background_gradient(subset=['Usage'], cmap='Blues')
                    styled_df = styled_df.background_gradient(subset=['% Change'], cmap='RdYlGn')
                    st.dataframe(styled_df, use_container_width=True)
                    csv = display_df.to_csv(index=False)
                    st.download_button(label="📥 Download Historical Data",data=csv,file_name=f"historical_data_{selected_plant}_{selected_bag}.csv",mime="text/csv")
        except Exception as e:
            st.error(f"An error occurred while processing the data: {str(e)}")
            st.write("Please make sure your Excel file has the correct format and try again.")
if __name__ == '__main__':
    main()
