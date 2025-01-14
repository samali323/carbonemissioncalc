import sqlite3

import streamlit as st

from src.config.constants import SOCIAL_CARBON_COSTS
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time, format_time_duration, get_carbon_price
)
from src.utils.logo_manager import FootballLogoManager

# Initialize calculator
calculator = EmissionsCalculator()
logo_manager = FootballLogoManager()
# Set page config
st.set_page_config(
    page_title="Football Team Flight Emissions Calculator",
    page_icon="✈️",
    layout="wide"
)

# Custom CSS
# Add custom CSS for table styling
st.markdown("""
    <style>
    /* Dark theme for the entire app */
    .main {
        background-color: #0e1117;
        color: #ffffff;
        padding: 2rem;
    }
    
    /* Table styling */
    .dataframe {
        width: 100%;
        margin: 1rem 0;
        background-color: transparent !important;
        color: #ffffff;
        border-collapse: collapse;
    }
    
    /* Hide index column */
    .dataframe th:first-child,
    .dataframe td:first-child {
        display: none !important;
    }
    
    /* Header cells */
    .dataframe thead th {
        background-color: transparent !important;
        color: #909090 !important;
        font-weight: 400 !important;
        text-align: center !important;
        padding: 12px 8px !important;
        border: none !important;
        border-bottom: 1px solid #1f2937 !important;
    }
    
    /* Data cells */
    .dataframe tbody td {
        background-color: transparent !important;
        color: #ffffff !important;
        text-align: center !important;
        padding: 12px 8px !important;
        border: none !important;
        border-bottom: 1px solid #1f2937 !important;
    }
    
    /* Row hover */
    .dataframe tbody tr:hover td {
        background-color: #1f2937 !important;
    }
    
    /* Remove last row border */
    .dataframe tbody tr:last-child td {
        border-bottom: none !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background-color: #2ea043 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #3fb950 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
    }
    
    /* Remove default table styling */
    table {
        border: none !important;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background-color: transparent;
        border-radius: 4px;
        color: #ffffff;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f2937;
    }
    </style>
""", unsafe_allow_html=True)


def display_results(result, home_airport, away_airport):
    """Display calculation results with collapsible sections"""
    if not st.session_state.get('last_calculation', {}).get('calculated'):
        return

    home_team = st.session_state.last_calculation.get('home_team')
    away_team = st.session_state.last_calculation.get('away_team')

    if not home_team or not away_team:
        return

    st.markdown("---")

    # Display match title and logos
    col1, col2, col3 = st.columns([1.5, 1, 1])

    with col1:
        st.container()
        home_logo = logo_manager.get_logo(home_team, width=90)
        if home_logo:
            col_logo, col_name = st.columns([1, 2])
            with col_logo:
                st.image(home_logo, width=80)
            with col_name:
                st.markdown(
                    f"<h3 style='margin: 0; font-size: 24px; height: 80px; line-height: 80px;'>{home_team}</h3>",
                    unsafe_allow_html=True)

    with col2:
        # Adjusted VS alignment and height to match team sections
        st.markdown("""
            <div style='display: flex; height: 80px; align-items: left; justify-content: left;'>
                <h3 style='margin: 0; font-size: 24px;'>VS</h3>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.container()
        away_logo = logo_manager.get_logo(away_team, width=90)
        if away_logo:
            col_logo, col_name = st.columns([1, 2])
            with col_logo:
                st.image(away_logo, width=90)
            with col_name:
                st.markdown(
                    f"<h3 style='margin: 0; font-size: 24px; height: 80px; line-height: 80px;'>{away_team}</h3>",
                    unsafe_allow_html=True)

    # Summary metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Distance", f"{result.distance_km:,.1f} km")
    with col2:
        st.metric("Total CO₂", f"{result.total_emissions:,.2f} tons")
    with col3:
        st.metric("Per Person", f"{result.per_passenger:,.2f} tons")
    with col4:
        st.metric("Flight Type", result.flight_type)

    # Transport Mode Comparison (always expanded)
    with st.expander("🚊 Transport Mode Comparison", expanded=True):
        display_transport_comparison(result)

    # Environmental Impact (always expanded)
    with st.expander("🌍 Environmental Impact", expanded=False):
        impact = calculate_equivalencies(result.total_emissions)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("🚗 **Transportation Impact**")
            st.markdown(f"• {impact['gasoline_vehicles_year']:.2f} Gasoline vehicles driven for one year")
            st.markdown(f"• {impact['electric_vehicles_year']:.2f} Electric vehicles driven for one year")
            st.markdown(f"• {impact['gasoline_vehicle_miles']:,.0f} Miles driven by gasoline vehicle")

            st.markdown("⚡ **Energy Usage**")
            st.markdown(f"• {impact['homes_energy_year']:.2f} Homes' energy use for one year")
            st.markdown(f"• {impact['homes_electricity_year']:.2f} Homes' electricity use for one year")
            st.markdown(f"• {impact['smartphones_charged']:,.0f} Smartphones charged")

            st.markdown("🌳 **Environmental Offset**")
            st.markdown(f"• {impact['tree_seedlings_10years']:.2f} Tree seedlings grown for 10 years")
            st.markdown(f"• {impact['forest_acres_year']:.2f} Acres of U.S. forests in one year")
            st.markdown(f"• {impact['forest_preserved_acres']:.2f} Acres of U.S. forests preserved")

        with col2:
            st.markdown("♻️ **Waste & Resources**")
            st.markdown(f"• {impact['waste_tons_recycled']:.2f} Tons of waste recycled")
            st.markdown(f"• {impact['garbage_trucks_recycled']:.2f} Garbage trucks of waste recycled")
            st.markdown(f"• {impact['trash_bags_recycled']:.0f} Trash bags of waste recycled")

            st.markdown("⛽ **Fuel Equivalents**")
            st.markdown(f"• {impact['gasoline_gallons']:,.0f} Gallons of gasoline")
            st.markdown(f"• {impact['diesel_gallons']:,.0f} Gallons of diesel")
            st.markdown(f"• {impact['propane_cylinders']:,.0f} Propane cylinders for BBQ")
            st.markdown(f"• {impact['oil_barrels']:.2f} Barrels of oil")

    # Cost Analysis (collapsible)
    with st.expander("💰 Cost Analysis", expanded=False):
        rail_emissions = calculate_transport_emissions(
            'rail',
            result.distance_km,
            st.session_state.form_state['passengers'],
            st.session_state.form_state['is_round_trip']
        )

        bus_emissions = calculate_transport_emissions(
            'bus',
            result.distance_km,
            st.session_state.form_state['passengers'],
            st.session_state.form_state['is_round_trip']
        )

        display_carbon_price_analysis(
            air_emissions=result.total_emissions,
            rail_emissions=rail_emissions,
            bus_emissions=bus_emissions,
            away_team=st.session_state.form_state['away_team'],
            home_team=st.session_state.form_state['home_team']
        )


def display_environmental_impact(impact):
    """Display environmental impact with consistent formatting"""
    st.markdown("### 🌍 Environmental Impact")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        # Transportation Impact
        st.markdown("🚗 **Transportation Impact**")
        st.markdown(f"• {impact['gasoline_vehicles_year']:.2f} Gasoline vehicles driven for one year")
        st.markdown(f"• {impact['electric_vehicles_year']:.2f} Electric vehicles driven for one year")
        st.markdown(f"• {impact['gasoline_vehicle_miles']:,.0f} Miles driven by gasoline vehicle")

        # Energy Usage
        st.markdown("\n⚡ **Energy Usage**")
        st.markdown(f"• {impact['homes_energy_year']:.2f} Homes' energy use for one year")
        st.markdown(f"• {impact['homes_electricity_year']:.2f} Homes' electricity use for one year")
        st.markdown(f"• {impact['smartphones_charged']:,.0f} Smartphones charged")

        # Environmental Offset
        st.markdown("\n🌳 **Environmental Offset**")
        st.markdown(f"• {impact['tree_seedlings_10years']:.2f} Tree seedlings grown for 10 years")
        st.markdown(f"• {impact['forest_acres_year']:.2f} Acres of U.S. forests in one year")
        st.markdown(f"• {impact['forest_preserved_acres']:.2f} Acres of U.S. forests preserved")

    with col2:
        # Waste & Resources
        st.markdown("♻️ **Waste & Resources**")
        st.markdown(f"• {impact['waste_tons_recycled']:.2f} Metric tons of waste recycled")
        st.markdown(f"• {impact['garbage_trucks_recycled']:.2f} Garbage trucks of waste recycled")
        st.markdown(f"• {impact['trash_bags_recycled']:,.0f} Trash bags of waste recycled")

        # Fuel Equivalents
        st.markdown("\n⛽ **Fuel Equivalents**")
        st.markdown(f"• {impact['gasoline_gallons']:,.0f} Gallons of gasoline")
        st.markdown(f"• {impact['diesel_gallons']:,.0f} Gallons of diesel")
        st.markdown(f"• {impact['propane_cylinders']:,.0f} Propane cylinders for BBQ")
        st.markdown(f"• {impact['oil_barrels']:.2f} Barrels of oil")


# Add custom CSS for consistent spacing and alignment
st.markdown("""
    <style>
    .environmental-impact {
        margin-bottom: 1rem;
    }
    .environmental-impact p {
        margin: 0.5rem 0;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)


def display_transport_comparison(result):
    """Display transport mode comparison"""

    # Calculate flight time
    flight_time_seconds = calculate_flight_time(
        distance_km=result.distance_km / (2 if result.is_round_trip else 1),
        is_round_trip=result.is_round_trip
    )
    flight_time_str = format_time_duration(flight_time_seconds)

    try:
        conn = sqlite3.connect('data/routes.db')
        cursor = conn.cursor()

        # Original query preserved
        query = """
        SELECT 
            transit_duration,
            transit_distance,
            rail_emissions,
            driving_duration,
            driving_distance,
            bus_emissions
        FROM match_emissions
        WHERE distance_km = ? 
        ORDER BY last_updated DESC
        LIMIT 1
        """

        cursor.execute(query, (result.distance_km / (2 if result.is_round_trip else 1),))
        route_data = cursor.fetchone()

        if route_data:
            # For round trips, double the duration and distance
            multiplier = 2 if result.is_round_trip else 1

            transit_time_str = format_time_duration(route_data[0] * multiplier) if route_data[0] else "N/A"
            transit_distance = route_data[1] * multiplier if route_data[1] else result.distance_km
            rail_emissions = route_data[2] * multiplier if route_data[2] else 0

            driving_time_str = format_time_duration(route_data[3] * multiplier) if route_data[3] else "N/A"
            driving_distance = route_data[4] * multiplier if route_data[4] else result.distance_km
            bus_emissions = route_data[5] * multiplier if route_data[5] else 0
        else:
            # Fallback to calculated values
            transit_time_str = "N/A"
            transit_distance = result.distance_km
            rail_emissions = calculate_transport_emissions(
                'rail',
                result.distance_km,
                st.session_state.form_state['passengers'],
                result.is_round_trip
            )

            driving_time_str = "N/A"
            driving_distance = result.distance_km
            bus_emissions = calculate_transport_emissions(
                'bus',
                result.distance_km,
                st.session_state.form_state['passengers'],
                result.is_round_trip
            )

    except Exception as e:
        st.error(f"Error retrieving transport data: {str(e)}")
        transit_time_str = "N/A"
        transit_distance = result.distance_km
        rail_emissions = 0
        driving_time_str = "N/A"
        driving_distance = result.distance_km
        bus_emissions = 0

    finally:
        if 'conn' in locals():
            conn.close()

    # Apply styling and create table
    st.markdown("""
        <style>
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            background-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        }
        .styled-table thead tr {
            background-color: transparent;
            color: #6B7280;
            text-align: center;
            font-weight: normal;
        }
        .styled-table th,
        .styled-table td {
            padding: 12px 15px;
            text-align: center;
            border-bottom: 1px solid #1f2937;
        }
        .styled-table tbody tr {
            color: white;
        }
        .styled-table tbody tr:last-of-type {
            border-bottom: none;
        }
        .styled-table tbody tr:hover {
            background-color: #1f2937;
        }
        </style>
    """ + f"""
    <table class="styled-table">
        <thead>
            <tr>
                <th>Mode</th>
                <th>Est. Travel Time</th>
                <th>Distance (km)</th>
                <th>CO₂ (tons)</th>
                <th>CO₂ Saved (tons)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>✈️ Air</td>
                <td>{flight_time_str}</td>
                <td>{result.distance_km:,.1f}</td>
                <td>{result.total_emissions:.2f}</td>
                <td>0.00</td>
            </tr>
            <tr>
                <td>🚂 Rail</td>
                <td>{transit_time_str}</td>
                <td>{transit_distance:,.1f}</td>
                <td>{rail_emissions:.2f}</td>
                <td>{result.total_emissions - rail_emissions:.2f}</td>
            </tr>
            <tr>
                <td>🚌 Bus</td>
                <td>{driving_time_str}</td>
                <td>{driving_distance:,.1f}</td>
                <td>{bus_emissions:.2f}</td>
                <td>{result.total_emissions - bus_emissions:.2f}</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)


def display_carbon_price_analysis(air_emissions, rail_emissions, bus_emissions, away_team, home_team):
    """Display carbon price analysis with proper formatting"""
    st.markdown("### 💰 Carbon Price Analysis")

    carbon_price = get_carbon_price(away_team, home_team)
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')

    st.markdown(f"Carbon Price ({away_country}): €{carbon_price:.2f}/tCO₂")

    # CSS for consistent table styling
    st.markdown("""
        <style>
        .cost-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background-color: #0e1117;
            color: #ffffff;
        }
        .cost-table th {
            color: #6B7280;
            font-weight: normal;
            text-align: center !important;
            padding: 12px;
            border-bottom: 1px solid #1f2937;
            background-color: #0e1117;
        }
        .cost-table td {
            padding: 12px;
            text-align: center !important;
            border-bottom: 1px solid #1f2937;
            background-color: transparent;
        }
        .cost-table tr:hover td {
            background-color: #1f2937;
        }
        </style>
    """, unsafe_allow_html=True)

    # Carbon Cost Table
    carbon_html = f"""
    <table class="cost-table">
        <thead>
            <tr>
                <th>Mode</th>
                <th>Carbon Cost (€)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Air</td>
                <td>{(air_emissions * carbon_price):.2f}</td>
            </tr>
            <tr>
                <td>Rail</td>
                <td>{(rail_emissions * carbon_price):.2f}</td>
            </tr>
            <tr>
                <td>Bus</td>
                <td>{(bus_emissions * carbon_price):.2f}</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(carbon_html, unsafe_allow_html=True)

    # Social Cost Analysis
    st.markdown("Social Cost Analysis")

    # Social Cost Table with updated formatting
    social_html = f"""
    <table class="cost-table">
        <thead>
            <tr>
                <th>Mode</th>
                <th>Cost Type</th>
                <th>Low</th>
                <th>Median</th>
                <th>Mean</th>
                <th>High</th>
            </tr>
        </thead>
        <tbody>
            <!-- Air -->
            <tr>
                <td>Air</td>
                <td>Synthetic</td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low']:,.2f}</td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['synthetic_median']:,.2f}</td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['synthetic_mean']:,.2f}</td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']:,.2f}</td>
            </tr>
            <tr>
                <td></td>
                <td>EPA</td>
                <td></td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['epa_median']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td>IWG</td>
                <td></td>
                <td>€{air_emissions * SOCIAL_CARBON_COSTS['iwg_75th']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <!-- Rail -->
            <tr>
                <td>Rail</td>
                <td>Synthetic</td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low']:,.2f}</td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['synthetic_median']:,.2f}</td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['synthetic_mean']:,.2f}</td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']:,.2f}</td>
            </tr>
            <tr>
                <td></td>
                <td>EPA</td>
                <td></td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['epa_median']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td>IWG</td>
                <td></td>
                <td>€{rail_emissions * SOCIAL_CARBON_COSTS['iwg_75th']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <!-- Bus -->
            <tr>
                <td>Bus</td>
                <td>Synthetic</td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low']:,.2f}</td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['synthetic_median']:,.2f}</td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['synthetic_mean']:,.2f}</td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']:,.2f}</td>
            </tr>
            <tr>
                <td></td>
                <td>EPA</td>
                <td></td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['epa_median']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td>IWG</td>
                <td></td>
                <td>€{bus_emissions * SOCIAL_CARBON_COSTS['iwg_75th']:,.2f}</td>
                <td></td>
                <td></td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(social_html, unsafe_allow_html=True)


def calculate_and_display():
    """Calculate and display emissions results"""
    try:
        # Reset previous results first
        if 'last_calculation' in st.session_state:
            del st.session_state.last_calculation

        # Get teams and verify they're selected
        home_team = st.session_state.form_state['home_team']
        away_team = st.session_state.form_state['away_team']

        if not home_team or not away_team:
            return

        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            st.error("Airport not found for one or both teams")
            return

        home_coords = get_airport_coordinates(home_airport)
        away_coords = get_airport_coordinates(away_airport)

        if not home_coords or not away_coords:
            st.error("Coordinates not found for one or both airports")
            return

        # Calculate emissions
        result = calculator.calculate_flight_emissions(
            origin_lat=home_coords['lat'],
            origin_lon=home_coords['lon'],
            dest_lat=away_coords['lat'],
            dest_lon=away_coords['lon'],
            passengers=st.session_state.form_state['passengers'],
            is_round_trip=st.session_state.form_state['is_round_trip']
        )

        # Store all necessary information in session state
        st.session_state.last_calculation = {
            'result': result,
            'home_airport': home_airport,
            'away_airport': away_airport,
            'home_team': home_team,
            'away_team': away_team,
            'calculated': True  # Add a flag to indicate calculation is complete
        }

    except Exception as e:
        st.error(f"Error calculating emissions: {str(e)}")


# Main layout
st.title("⚽ Football Team Flight Emissions Calculator")
st.write("Calculate carbon emissions for football team travel")

# Sidebar content
with st.sidebar:
    st.header("About")
    st.write("""
    This calculator helps estimate the carbon emissions from football team travel.
    
    **Features:**
    - Calculate flight emissions
    - Compare different transport modes
    - View environmental impact
    - Round trip calculations
    """)

    st.header("Instructions")
    st.write("""
    1. Select home and away teams
    2. Enter number of passengers
    3. Choose round trip if applicable
    4. Click Calculate Emissions
    """)

try:
    all_teams = sorted(get_all_teams())  # Sort teams alphabetically
except Exception as e:
    st.error(f"Error loading team data: {str(e)}")
    all_teams = []  # Fallback to empty list

# Initialize session state if not exists
if 'form_state' not in st.session_state:
    st.session_state.form_state = {
        'home_team': all_teams[0] if all_teams else "",
        'away_team': all_teams[0] if all_teams else "",
        'passengers': 30,
        'is_round_trip': False
    }

# Check for match selection from analysis page
if 'calculator_input' in st.session_state:
    st.session_state.form_state.update(st.session_state.calculator_input)
    del st.session_state['calculator_input']

# Create two columns for input
st.markdown("### 🏟️ Team Selection")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Home Team")
    home_team = st.selectbox(
        "Select Home Team",
        options=all_teams,
        index=all_teams.index(st.session_state.form_state['home_team']) if all_teams else 0,
        key='home_team',
        help="Select the home team"
    )

with col2:
    st.markdown("#### Away Team")
    away_team = st.selectbox(
        "Select Away Team",
        options=all_teams,
        index=all_teams.index(st.session_state.form_state['away_team']) if all_teams else 0,
        key='away_team',
        help="Select the away team"
    )

    # Make number of passengers input smaller
    st.markdown("### ✈️ Travel Details")
    col_pass1, col_pass2 = st.columns([2, 1])  # Create sub-columns for passenger input
    with col_pass1:
        passengers = st.number_input(
            "Number of Passengers",
            min_value=1,
            value=st.session_state.form_state['passengers'],
            help="Enter the total number of passengers traveling",
            key='passengers',
            label_visibility="collapsed"  # Hide label to save space
        )

    is_round_trip = st.checkbox(
        "Round Trip",
        value=st.session_state.form_state['is_round_trip'],
        help="Check if this is a round trip journey",
        key='round_trip_checkbox',
        on_change=lambda: (
            st.session_state.form_state.update({'is_round_trip': st.session_state.round_trip_checkbox}),
            calculate_and_display() if st.session_state.get('last_calculation') else None
        )
    )

    # Update session state
    st.session_state.form_state.update({
        'home_team': home_team,
        'away_team': away_team,
        'passengers': passengers,
        'is_round_trip': is_round_trip
    })

# Calculate button in its own container
st.markdown("---")
calculate_col1, calculate_col2, calculate_col3 = st.columns([1, 2, 1])
with calculate_col2:
    if st.button("📊 Calculate Emissions", type="primary", use_container_width=True):
        with st.spinner("Calculating emissions..."):
            calculate_and_display()

# Display results if they exist in session state
if 'last_calculation' in st.session_state:
    display_results(
        st.session_state.last_calculation['result'],
        st.session_state.last_calculation['home_airport'],
        st.session_state.last_calculation['away_airport']
    )
