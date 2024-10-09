import streamlit as st
import io
import base64
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, Indenter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Sales Prediction Simulator", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    body {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stApp {
        background-image: linear-gradient(45deg, #1e3799, #0c2461);
    }
    .big-font {
        font-size: 48px !important;
        font-weight: bold;
        color: lime;
        text-align: center;
        text-shadow: 2px 2px 4px #000000;
    }
    .subheader {
        font-size: 24px;
        color: mocassin;
        text-align: center;
    }
    .stButton>button {
        background-color: #4a69bd;
        color: white;
        border-radius: 20px;
        border: 2px solid #82ccdd;
        padding: 10px 24px;
        font-size: 16px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #82ccdd;
        color: #0c2461;
        transform: scale(1.05);
    }
    .stProgress > div > div > div > div {
        background-color: #4a69bd;
    }
    .stSelectbox {
        background-color: #1e3799;
    }
    .stDataFrame {
        background-color: #0c2461;
    }
    .metric-value {
        color: gold !important;
        font-size: 24px !important;
        font-weight: bold !important;
    }
    .metric-label {
        color: white !important;
    }
    h3 {
        color: #ff9f43 !important;
        font-size: 28px !important;
        font-weight: bold !important;
        text-shadow: 1px 1px 2px #000000;
    }
    /* Updated styles for file uploader */
    .stFileUploader {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .custom-file-upload {
        display: inline-block;
        padding: 10px 20px;
        cursor: pointer;
        background-color: #4a69bd;
        color: #ffffff;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .custom-file-upload:hover {
        background-color: #82ccdd;
        color: #0c2461;
    }
    .file-upload-text {
        font-size: 18px;
        color: fuchsia;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* Style for uploaded file name */
    .uploaded-filename {
        background-color: rgba(255, 255, 255, 0.2);
        color: cyan;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)
def custom_file_uploader(label, type):
    st.markdown(f'<p class="file-upload-text">{label}</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=type, key="file_uploader")
    return uploaded_file

@st.cache_data
def load_data(file):
    data = pd.read_excel(file)
    return data

@st.cache_resource
def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model, X_test, y_test

def create_monthly_performance_graph(data):
    months = ['Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct']
    colors = px.colors.qualitative.Pastel

    fig = go.Figure()

    for i, month in enumerate(months):
        if month != 'Oct':
            target = data[f'Month Tgt ({month})'].iloc[0]
            achievement = data[f'Monthly Achievement({month})'].iloc[0]
            percentage = (achievement / target * 100) if target != 0 else 0
            
            fig.add_trace(go.Bar(
                x=[f"{month} Tgt", f"{month} Ach"],
                y=[target, achievement],
                name=month,
                marker_color=colors[i],
                text=[f"{target:,.0f}", f"{achievement:,.0f}<br>{percentage:.1f}%"],
                textposition='auto'
            ))
        else:
            target = data['Month Tgt (Oct)'].iloc[0]
            projection = data['Predicted Oct 2024'].iloc[0]
            percentage = (projection / target * 100) if target != 0 else 0
            
            fig.add_trace(go.Bar(
                x=[f"{month} Tgt", f"{month} Proj"],
                y=[target, projection],
                name=month,
                marker_color=[colors[i], 'red'],
                text=[f"{target:,.0f}", f"{projection:,.0f}<br><span style='color:black'>{percentage:.1f}%</span>"],
                textposition='auto'
            ))

    fig.update_layout(
        title='Monthly Performance',
        plot_bgcolor='rgba(255,255,255,0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_color='#ffffff',
        legend_font_color='#ffffff',
        height=500,
        width=800,
        barmode='group'
    )
    fig.update_xaxes(tickfont_color='#ffffff')
    fig.update_yaxes(title_text='Sales', tickfont_color='#ffffff')
    fig.update_traces(textfont_color='black')
    
    return fig
def create_target_vs_projected_graph(data):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data['Zone'], y=data['Month Tgt (Oct)'], name='Month Target (Oct)', marker_color='#4a69bd'))
    fig.add_trace(go.Bar(x=data['Zone'], y=data['Predicted Oct 2024'], name='Projected Sales (Oct)', marker_color='#82ccdd'))
    
    fig.update_layout(
        title='October 2024: Target vs Projected Sales',
        barmode='group',
        plot_bgcolor='rgba(255,255,255,0.1)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#ffffff',
        title_font_color='#ffffff',
        legend_font_color='#ffffff',
        height=500
    )
    fig.update_xaxes(title_text='Zone', tickfont_color='#ffffff')
    fig.update_yaxes(title_text='Sales', tickfont_color='#ffffff')
    
    return fig

def prepare_data_for_pdf(data):
    # Filter out specified zones
    excluded_zones = ['Bihar', 'J&K', 'North-I', 'Punjab,HP and J&K', 'U.P.+U.K.', 'Odisha+Jharkhand+Bihar']
    filtered_data = data[~data['Zone'].isin(excluded_zones)]

    # Further filter to include only LC and PHD brands
    filtered_data = filtered_data[filtered_data['Brand'].isin(['LC', 'PHD'])]

    # Calculate totals for LC, PHD, and LC+PHD
    lc_data = filtered_data[filtered_data['Brand'] == 'LC']
    phd_data = filtered_data[filtered_data['Brand'] == 'PHD']
    lc_phd_data = filtered_data

    totals = []
    for brand_data, brand_name in [(lc_data, 'LC'), (phd_data, 'PHD'), (lc_phd_data, 'LC+PHD')]:
        total_month_tgt_oct = brand_data['Month Tgt (Oct)'].sum()
        total_predicted_oct_2024 = brand_data['Predicted Oct 2024'].sum()
        total_oct_2023 = brand_data['Total Oct 2023'].sum()
        total_yoy_growth = (total_predicted_oct_2024 - total_oct_2023) / total_oct_2023 * 100

        totals.append({
            'Zone': 'All India Total',
            'Brand': brand_name,
            'Month Tgt (Oct)': total_month_tgt_oct,
            'Predicted Oct 2024': total_predicted_oct_2024,
            'Total Oct 2023': total_oct_2023,
            'YoY Growth': total_yoy_growth
        })

    # Concatenate filtered data with totals
    final_data = pd.concat([filtered_data, pd.DataFrame(totals)], ignore_index=True)

    # Round the values
    final_data['Month Tgt (Oct)'] = final_data['Month Tgt (Oct)'].round().astype(int)
    final_data['Predicted Oct 2024'] = final_data['Predicted Oct 2024'].round().astype(int)
    final_data['Total Oct 2023'] = final_data['Total Oct 2023'].round().astype(int)
    final_data['YoY Growth'] = final_data['YoY Growth'].round(2)

    return final_data

def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=0.2*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1
    title = Paragraph("Sales Predictions for October 2024", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.15*inch))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Prepare data for PDF
    pdf_data = prepare_data_for_pdf(data)

    table_data = [['Zone', 'Brand', 'Month Tgt (Oct)', 'Predicted Oct 2024', 'Total Oct 2023', 'YoY Growth']]
    for _, row in pdf_data.iterrows():
        table_data.append([
            row['Zone'],
            row['Brand'],
            f"{row['Month Tgt (Oct)']:,}",
            f"{row['Predicted Oct 2024']:,}",
            f"{row['Total Oct 2023']:,}",
            f"{row['YoY Growth']:.2f}%"
        ])
    table_data[0][-1] = table_data[0][-1] + "*"  

    table = Table(table_data, colWidths=[1.25*inch, 0.80*inch, 1.5*inch, 1.75*inch, 1.5*inch, 1.20*inch], 
                  rowHeights=[0.60*inch] + [0.38*inch] * (len(table_data) - 1))
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A708B')),
        ('BACKGROUND', (0, len(table_data) - 3), (-1, len(table_data) - 1), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -4), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
    ])
    table.setStyle(style)
    elements.append(table)

    footnote_style = getSampleStyleSheet()['Normal']
    footnote_style.fontSize = 8
    footnote_style.leading = 10 
    footnote_style.alignment = 0
    footnote = Paragraph("*YoY Growth is calculated using October 2023 sales and predicted October 2024 sales.", footnote_style)
    indented_footnote = Indenter(left=-0.75*inch)
    elements.append(Spacer(1, 0.15*inch))
    elements.append(indented_footnote)
    elements.append(footnote)
    elements.append(Indenter(left=0.5*inch))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    st.markdown('<p class="big-font">Sales Prediction Simulator</p>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Upload your data and unlock the future of sales!</p>', unsafe_allow_html=True)
    uploaded_file = custom_file_uploader("Choose your sales data file (Excel format)", ["xlsx"])

    if uploaded_file is not None:
        st.markdown(f'<div class="uploaded-filename">Uploaded file: {uploaded_file.name}</div>', unsafe_allow_html=True)
        data = load_data(uploaded_file)

        features = ['Month Tgt (Oct)', 'Monthly Achievement(Sep)', 'Total Sep 2023', 'Total Oct 2023',
                    'Monthly Achievement(Apr)', 'Monthly Achievement(May)', 'Monthly Achievement(June)',
                    'Monthly Achievement(July)', 'Monthly Achievement(Aug)']

        X = data[features]
        y = data['Total Oct 2023']

        model, X_test, y_test = train_model(X, y)

        st.sidebar.header("Control Panel")
        
        # Initialize session state for filters if not already present
        if 'selected_brands' not in st.session_state:
            st.session_state.selected_brands = []
        if 'selected_zones' not in st.session_state:
            st.session_state.selected_zones = []

        # Brand filter
        st.sidebar.subheader("Select Brands")
        for brand in data['Brand'].unique():
            if st.sidebar.checkbox(brand, key=f"brand_{brand}"):
                if brand not in st.session_state.selected_brands:
                    st.session_state.selected_brands.append(brand)
            elif brand in st.session_state.selected_brands:
                st.session_state.selected_brands.remove(brand)

        # Zone filter
        st.sidebar.subheader("Select Zones")
        for zone in data['Zone'].unique():
            if st.sidebar.checkbox(zone, key=f"zone_{zone}"):
                if zone not in st.session_state.selected_zones:
                    st.session_state.selected_zones.append(zone)
            elif zone in st.session_state.selected_zones:
                st.session_state.selected_zones.remove(zone)

        # Apply filters
        if st.session_state.selected_brands and st.session_state.selected_zones:
            filtered_data = data[data['Brand'].isin(st.session_state.selected_brands) & 
                                 data['Zone'].isin(st.session_state.selected_zones)]
        else:
            filtered_data = data
        col1, col2 = st.columns(2)

        with col1:
            
            st.markdown("<h3>Model Performance Metrics</h3>", unsafe_allow_html=True)
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            st.markdown(f'<div class="metric-label">Accuracy Score</div><div class="metric-value">{r2:.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-label">Error Margin</div><div class="metric-value">{np.sqrt(mse):.2f}</div>', unsafe_allow_html=True)

            feature_importance = pd.DataFrame({
                'feature': features,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)

            fig_importance = px.bar(feature_importance, x='importance', y='feature', orientation='h',
                                    title='Feature Impact Analysis', labels={'importance': 'Impact', 'feature': 'Feature'})
            fig_importance.update_layout(
                plot_bgcolor='rgba(255,255,255,0.1)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font_color='mocassin',
                title_font_color='mocassin',
                xaxis_title_font_color='mocassin',
                yaxis_title_font_color='mocassin',
                legend_font_color='mocassin'
            )
            fig_importance.update_xaxes(tickfont_color='#ffffff')
            fig_importance.update_yaxes(tickfont_color='#ffffff')
            st.plotly_chart(fig_importance, use_container_width=True)

        with col2:
            
            st.markdown("<h3>Sales Forecast Visualization</h3>", unsafe_allow_html=True)

            X_2024 = filtered_data[features].copy()
            X_2024['Total Oct 2023'] = filtered_data['Total Oct 2023']
            predictions_2024 = model.predict(X_2024)
            filtered_data['Predicted Oct 2024'] = predictions_2024
            filtered_data['YoY Growth'] = (filtered_data['Predicted Oct 2024'] - filtered_data['Total Oct 2023']) / filtered_data['Total Oct 2023'] * 100

            fig_predictions = go.Figure()
            fig_predictions.add_trace(go.Bar(x=filtered_data['Zone'], y=filtered_data['Total Oct 2023'], name='Oct 2023 Sales', marker_color='#4a69bd'))
            fig_predictions.add_trace(go.Bar(x=filtered_data['Zone'], y=filtered_data['Predicted Oct 2024'], name='Predicted Oct 2024 Sales', marker_color='#82ccdd'))
            fig_predictions.update_layout(
                title='Sales Projection: 2023 vs 2024', 
                barmode='group', 
                plot_bgcolor='rgba(255,255,255,0.1)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font_color='#ffffff',
                title_font_color='#ffffff',
                legend_font_color='#ffffff'
            )
            fig_predictions.update_xaxes(title_text='Zone', tickfont_color='#ffffff')
            fig_predictions.update_yaxes(title_text='Sales', tickfont_color='#ffffff')
            st.plotly_chart(fig_predictions, use_container_width=True)
            fig_target_vs_projected = create_target_vs_projected_graph(filtered_data)
            st.plotly_chart(fig_target_vs_projected, use_container_width=True)
        st.markdown("<h3>Monthly Performance by Zone and Brand</h3>", unsafe_allow_html=True)
        
        # Create dropdowns for zone and brand selection
        col_zone, col_brand = st.columns(2)
        with col_zone:
            selected_zone = st.selectbox("Select Zone", options=filtered_data['Zone'].unique())
        with col_brand:
            selected_brand = st.selectbox("Select Brand", options=filtered_data[filtered_data['Zone']==selected_zone]['Brand'].unique())
        
        # Filter data based on selection
        selected_data = filtered_data[(filtered_data['Zone'] == selected_zone) & (filtered_data['Brand']==selected_brand)]
        if not selected_data.empty:
            fig_monthly_performance = create_monthly_performance_graph(selected_data)
            
            # Update the graph with the selected data
            months = ['Apr', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct']
            for i, month in enumerate(months):
                if month != 'Oct':
                    fig_monthly_performance.data[i].y = [
                        selected_data[f'Month Tgt ({month})'].iloc[0],
                        selected_data[f'Monthly Achievement({month})'].iloc[0]
                    ]
                else:
                    fig_monthly_performance.data[i].y = [
                        selected_data['Month Tgt (Oct)'].iloc[0],
                        selected_data['Predicted Oct 2024'].iloc[0]
                    ]
            
            st.plotly_chart(fig_monthly_performance, use_container_width=True)
        else:
            st.warning("No data available for the selected Zone and Brand combination.")
        st.markdown("<h3>Detailed Sales Forecast</h3>", unsafe_allow_html=True)
        st.dataframe(filtered_data[['Zone', 'Brand', 'Month Tgt (Oct)', 'Predicted Oct 2024', 'Total Oct 2023', 'YoY Growth']])

        pdf_buffer = create_pdf(filtered_data)
        st.download_button(
            label="Download Forecast Report",
            data=pdf_buffer,
            file_name="sales_forecast_2024.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Upload your sales data to begin the simulation!")

if __name__ == "__main__":
    main()
