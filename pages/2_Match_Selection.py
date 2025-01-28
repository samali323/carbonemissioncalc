import streamlit as st
import pandas as pd
import sqlite3
import math
import plotly.express as px
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.calculations import calculate_distance

# Page config
st.set_page_config(
    page_title="Football Travel Emissions Analysis",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    /* Main layout */
    .main {
        background-color: #0e1117;
        color: #ffffff;
        padding: 2rem;
    }
    
    /* Section headers */
    .section-header {
        background-color: #0e1117;
        border-radius: 10px;
        padding: 1rem;
        margin: 1.5rem 0;
        color: white;
        text-align: center !important;
    }
    
    /* Styled table for competition summary */
    .styled-table {
        margin: 25px auto;
        width: 100%;
        text-align: center;
        border-collapse: collapse;
        background-color: #0e1117;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .styled-table th {
        background-color: #1f2937;
        color: #6B7280;
        padding: 12px;
        text-align: center;
        font-weight: normal;
        border-bottom: 1px solid #2d3139;
    }
    
    .styled-table td {
        padding: 12px;
        text-align: center;
        color: white;
        border-bottom: 1px solid #2d3139;
    }
    
    .styled-table tr:hover {
        background-color: #2d3139;
    }
    
    [data-testid="stDataFrame"] {
        width: 100%;
        margin: 0 auto;
        display: flex;
        justify-content: center;
    }
    
    [data-testid="stDataFrame"] div[style*="overflow"] {
        display: flex;
        justify-content: center;
        text-align: center;
    }
    
    .element-container div[data-testid="stDataFrame"] > div {
        background-color: transparent !important;
    }
    
    /* Select box styling */
    div[data-baseweb="select"] {
        margin: 0 auto;
        text-align: center;
    }
    
    .stSelectbox {
        text-align: center;
    }
    
    .stSelectbox > div > div {
        text-align: center;
        background-color: #1f2937;
        border: 1px solid #2d3139;
    }
    
    .stSelectbox > label {
        text-align: center;
        width: 100%;
        color: #6B7280;
    }
    
    div[role="listbox"] {
        background-color: #1f2937;
        border: 1px solid #2d3139;
    }    

    [data-testid="stDataFrame"] td {
        text-align: center !important;
    }
   
    [data-testid="stDataFrame"] th {
        text-align: center !important;
    }
    
    [data-testid="stDataFrame"] div[style*="overflow"] {
        display: flex;
        justify-content: center;
        text-align: center;
    }
    .match-card {
    
        background-color: #0d0c0c;
    
        border-radius: 10px;
    
        padding: 1rem;
    
        margin: .5rem 0;
    
        border: 1px solid #2d3139;
    
        transition: all 0.2s ease;
        
        cursor: pointer;
    
    }
    
    
    .match-card:hover {
    
        background-color: #2ea043;
    
        transform: translateY(-2px);
    
    }
    
    
    .team-name {
    
        font-size: 1.1rem;
    
        font-weight: 500;
    
        color: #ffffff;
    
    }
    
    
    .vs-text {
    
        color: #6B7280;
    
        font-size: 0.9rem;
    
    }
    
    
    .competition-tag {
    
        font-size: 0.9rem;
    
        color: #6B7280;
    
    }
    </style>
""", unsafe_allow_html=True)


def format_number(value, decimal_places=0):
    """Format numbers with commas and no decimal places"""
    return f"{value:,.0f}"


def load_data():
    """Load data from database"""
    try:
        conn = sqlite3.connect('data/routes.db')
        query = """
        SELECT 
            r.home_team as "Home Team",
            r.away_team as "Away Team",
            r.competition as "Competition",
            r.driving_duration/3600.0 as driving_hours,
            r.transit_duration/3600.0 as transit_hours,
            r.driving_distance/1000.0 as driving_km,
            r.transit_distance/1000.0 as transit_km
        FROM routes r
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def calculate_competition_summary(df):
    """Calculate summary statistics by competition"""
    calculator = EmissionsCalculator()
    summary_data = []

    for competition in df['Competition'].unique():
        comp_df = df[df['Competition'] == competition]
        total_matches = len(comp_df)
        total_distance = 0
        total_emissions = 0

        for _, row in comp_df.iterrows():
            home_airport = get_team_airport(row['Home Team'])
            away_airport = get_team_airport(row['Away Team'])

            if home_airport and away_airport:
                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if home_coords and away_coords:
                    distance = calculate_distance(
                        home_coords['lat'], home_coords['lon'],
                        away_coords['lat'], away_coords['lon']
                    )
                    total_distance += distance

                    result = calculator.calculate_flight_emissions(
                        origin_lat=home_coords['lat'],
                        origin_lon=home_coords['lon'],
                        dest_lat=away_coords['lat'],
                        dest_lon=away_coords['lon'],
                        passengers=30,
                        is_round_trip=True
                    )
                    total_emissions += result.total_emissions

        if total_matches > 0:
            summary_data.append({
                'Competition': competition,
                'Matches': total_matches,
                'Total Distance (km)': total_distance,
                'Total Emissions (tons)': total_emissions,
                'Avg Distance (km)': total_distance / total_matches,
                'Avg Emissions (tons)': total_emissions / total_matches
            })

    return pd.DataFrame(summary_data)


def main():
    st.title('⚽ Football Travel Emissions Analysis')

    # Load data
    df = load_data()
    if df is None:
        return

    # Calculate and display competition summary
    summary_df = calculate_competition_summary(df)
    display_summary = summary_df.round(2).sort_values('Total Emissions (tons)', ascending=False)
    # Add this section right after loading the data and calculating summary_df

    # Calculate totals
    total_distance = summary_df['Total Distance (km)'].sum()
    total_emissions = summary_df['Total Emissions (tons)'].sum()
    avg_distance = summary_df['Avg Distance (km)'].mean()
    avg_emissions = summary_df['Avg Emissions (tons)'].mean()

    # Create metric columns
    st.markdown("""
        <div class="section-header">
            <h3>🌍 Global Totals</h3>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Distance",
                  f"{format_number(total_distance)} km",
                  help="Combined distance for all competitions")

    with col2:
        st.metric("Total Emissions",
                  f"{format_number(total_emissions)} tons",
                  help="Total CO₂ emissions from all matches")

    with col3:
        st.metric("Avg Match Distance",
                  f"{format_number(avg_distance)} km",
                  help="Average distance per match across all competitions")

    with col4:
        st.metric("Avg Match Emissions",
                  f"{format_number(avg_emissions)} tons",
                  help="Average emissions per match across all competitions")

    # Format summary data
    for col in display_summary.columns:
        if col != 'Competition' and col != 'Matches':
            display_summary[col] = display_summary[col].apply(format_number)

    # Replace the competition summary section with this:

    st.markdown("""
        <div class="section-header">
            <h3>📊 Competition Summary</h3>
        </div>
    """, unsafe_allow_html=True)

    # Create metric selector
    selected_metric = st.selectbox(
        "Choose Metric to Visualize:",
        options=['Total Emissions (tons)', 'Total Distance (km)',
                 'Avg Emissions (tons)', 'Avg Distance (km)'],
        index=0
    )

    # Create interactive bar chart
    fig = px.bar(
        summary_df.sort_values(selected_metric, ascending=False),
        x='Competition',
        y=selected_metric,
        color='Competition',
        text_auto='.2s',
        template='plotly_dark',
        labels={selected_metric: selected_metric + ' ▼'},
        height=500
    )

    # Customize layout
    fig.update_layout(
        showlegend=False,
        xaxis_title=None,
        yaxis_title=None,
        hovermode='x unified',
        margin=dict(t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickangle=45),
        font=dict(color='white')
    )

    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Show Detailed Table", expanded=False):
        # Create formatted dataframe copy
        formatted_df = display_summary.copy()

        # Clean numeric columns first
        numeric_cols = ['Total Distance (km)', 'Total Emissions (tons)',
                        'Avg Distance (km)', 'Avg Emissions (tons)', 'Matches']

        for col in numeric_cols:
            # Remove commas and convert to float if needed
            if formatted_df[col].dtype == object:
                formatted_df[col] = formatted_df[col].str.replace(',', '', regex=False).astype(float)
            # Convert to integer
            formatted_df[col] = formatted_df[col].round().astype(int)

        # Calculate totals from original numeric data (not formatted_df)
        total_distance = summary_df['Total Distance (km)'].sum()
        total_emissions = summary_df['Total Emissions (tons)'].sum()
        total_matches = summary_df['Matches'].sum()
        avg_distance = total_distance / total_matches
        avg_emissions = total_emissions / total_matches

        # Create total row with original values
        total_row = {
            'Competition': 'Total',
            'Matches': int(total_matches),
            'Total Distance (km)': int(round(total_distance)),
            'Total Emissions (tons)': int(round(total_emissions)),
            'Avg Distance (km)': int(round(avg_distance)),
            'Avg Emissions (tons)': int(round(avg_emissions))
        }

        # Append total row
        formatted_df = pd.concat([
            formatted_df,
            pd.DataFrame([total_row])
        ], ignore_index=True)

        # Create centered styler
        centered_styler = (
            formatted_df.style
            .format({
                'Matches': '{:,}',
                'Total Distance (km)': '{:,}',
                'Total Emissions (tons)': '{:,}',
                'Avg Distance (km)': '{:,}',
                'Avg Emissions (tons)': '{:,}'
            })
            .set_table_styles([{
                'selector': 'th, td',
                'props': [('text-align', 'center')]
            }, {
                'selector': 'tr:last-child',
                'props': [('background-color', '#1f2937'), ('font-weight', 'bold')]
            }])
        )

        # Apply custom styling
        st.markdown("""
            <style>
                [data-testid="stDataFrame"] {
                    width: fit-content !important;
                    margin: 0 auto !important;
                }
                [data-testid="stDataFrame"] table {
                    margin: 0 auto !important;
                    border-collapse: collapse;
                }
                [data-testid="stDataFrame"] th {
                    background-color: #1f2937 !important;
                    color: #6B7280 !important;
                }
                [data-testid="stDataFrame"] td {
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)

        st.dataframe(
            centered_styler,
            hide_index=True,
            use_container_width=True
        )

    # Match Selection filters
    st.markdown("""
        <div class="section-header">
            <h3>🔍 Match Selection</h3>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        competition_filter = st.selectbox(
            "🏆 Select Competition",
            ["All"] + sorted(df['Competition'].unique().tolist())
        )

    with col2:
        filtered_df = df if competition_filter == "All" else df[df['Competition'] == competition_filter]
        home_filter = st.selectbox(
            "🏠 Select Home Team",
            ["All"] + sorted(filtered_df['Home Team'].unique().tolist())
        )

    with col3:
        away_teams = df['Away Team'].unique() if home_filter == "All" else df[df['Home Team'] == home_filter][
            'Away Team'].unique()
        away_filter = st.selectbox(
            "✈️ Select Away Team",
            ["All"] + sorted(away_teams)
        )

    # Apply filters
    filtered_df = df.copy()
    if competition_filter != "All":
        filtered_df = filtered_df[filtered_df['Competition'] == competition_filter]
    if home_filter != "All":
        filtered_df = filtered_df[filtered_df['Home Team'] == home_filter]
    if away_filter != "All":
        filtered_df = filtered_df[filtered_df['Away Team'] == away_filter]

    # Pagination controls
    matches_per_page = st.select_slider(
        "Matches per page",
        options=[10, 20, 50, 100],
        value=20
    )

    total_matches = len(filtered_df)
    total_pages = math.ceil(total_matches / matches_per_page)

    if total_pages > 1:
        current_page = st.number_input(
            f"Page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1
        )
    else:
        current_page = 1

    # Calculate start and end indices for current page
    start_idx = (current_page - 1) * matches_per_page
    end_idx = min(start_idx + matches_per_page, total_matches)

    st.markdown(f"Showing matches {start_idx + 1}-{end_idx} of {total_matches}")

    # Display matches with pagination
    for index, row in filtered_df.iloc[start_idx:end_idx].iterrows():
        match_id = f"match_{index}"

        # Create match card container
        container = st.container()

        with container:
            col1, col2 = st.columns([12, 1])  # Adjust column ratio

            with col1:
                st.markdown(f"""
                    <div class="match-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="team-name" style="flex: 2; text-align: center;">{row['Home Team']}</div>
                            <div style="flex: 1; text-align: center;">
                                <span class="vs-text">VS</span>
                            </div>
                            <div class="team-name" style="flex: 2; text-align: center;">{row['Away Team']}</div>
                            <div style="flex: 1; text-align: right;">
                                <span class="competition-tag">{row['Competition']}</span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Align the button with the match card
            with col2:
                st.markdown("""
                    <style>
                        div.stButton > button {
                            margin-top: 12px;  /* Adjust this value to align with match card */
                            height: 46px;      /* Match the height of the card */
                            padding: 0;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                    </style>
                """, unsafe_allow_html=True)

                if st.button("➡️", key=f"calc_{index}", help="Calculate emissions for this match"):
                    st.session_state.calculator_input = {
                        'home_team': row['Home Team'],
                        'away_team': row['Away Team'],
                        'passengers': 30,
                        'is_round_trip': False,
                        'from_analysis': True,
                        'auto_calculate': True  # Add this flag
                    }
                    st.switch_page("../Home.py")


if __name__ == "__main__":
    main()
