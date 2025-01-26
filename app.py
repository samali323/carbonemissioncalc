import sqlite3

import pandas as pd
import streamlit as st

from src.config.constants import SOCIAL_CARBON_COSTS
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time, format_time_duration, get_carbon_price
)
from src.utils.carbon_pricing.enhanced_calculator import EnhancedCarbonPricingCalculator
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


def display_results(result):
    """Display calculation results with collapsible sections"""
    if not st.session_state.get('last_calculation', {}).get('calculated'):
        return

    home_team = st.session_state.last_calculation.get('home_team')
    away_team = st.session_state.last_calculation.get('away_team')

    if not home_team or not away_team:
        return

    st.markdown("---")

    # Display match title and logos
    col1, col2, col3 = st.columns([.5, .5, .5])

    with col1:
        st.container()
        home_logo = logo_manager.get_logo(home_team, width=80)
        if home_logo:
            col_logo, col_name = st.columns([1, 2])
            with col_logo:
                st.image(home_logo, width=80)
            with col_name:
                st.markdown(
                    f"<h3 style='margin: 0; font-size: 24px; height: 80px; line-height: 80px;'>{home_team}</h3>",
                    unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div style='display: flex; height: 80px; align-items: center; justify-content: center;'>
                <span style='margin: 0; font-size: 24px;'>VS</span>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.container()
        away_logo = logo_manager.get_logo(away_team, width=80)
        if away_logo:
            col_logo, col_name = st.columns([1, 2])
            with col_logo:
                st.image(away_logo, width=80)
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
        rail_emissions, bus_emissions = display_transport_comparison(result)

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
        display_carbon_price_analysis(
            air_emissions=result.total_emissions,
            rail_emissions=rail_emissions,
            bus_emissions=bus_emissions,
            away_team=st.session_state.form_state['away_team'],
            home_team=st.session_state.form_state['home_team']
        )

    # Economic Impact Analysis as a separate top-level expander
    with st.expander("💸 Economic Impact Analysis", expanded=False):
        display_economic_impacts(
            result=result,
            home_team=st.session_state.form_state['home_team'],
            away_team=st.session_state.form_state['away_team']
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


def parse_time_duration(time_str):
    """Convert time string (e.g. '2 hours 30 minutes') to seconds"""
    total_seconds = 0
    parts = time_str.split()

    for i in range(0, len(parts) - 1, 2):
        value = int(parts[i])
        unit = parts[i + 1]

        if 'hour' in unit:
            total_seconds += value * 3600
        elif 'minute' in unit:
            total_seconds += value * 60

    return total_seconds


def format_time_diff(seconds_diff):
    """Format time difference (in seconds) to +/- string"""
    if seconds_diff == 0:
        return "-"

    sign = "+" if seconds_diff > 0 else "-"
    abs_diff = abs(seconds_diff)

    hours = abs_diff // 3600
    minutes = (abs_diff % 3600) // 60

    if hours > 0:
        return f"{sign}{hours}h {minutes}m"
    return f"{sign}{minutes}m"


def display_transport_comparison(result):
    """Display transport mode comparison"""
    is_derby = result.distance_km == 0
    home_team = st.session_state.form_state['home_team']
    away_team = st.session_state.form_state['away_team']
    rail_feasible = calculate_transport_emissions(
        'rail',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    ) is not None

    bus_feasible = calculate_transport_emissions(
        'bus',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    ) is not None
    # Add explanatory notes
    rail_note = "* No direct rail connection available" if not rail_feasible else ""
    bus_note = "* Route exceeds feasible bus distance" if not bus_feasible else ""

    if is_derby:
        flight_time_str = "N/A (Derby Match)"
        flight_emissions = 0
        flight_time_seconds = 0
    else:
        flight_time_seconds = calculate_flight_time(
            distance_km=result.distance_km / (2 if result.is_round_trip else 1),
            is_round_trip=result.is_round_trip
        )
        flight_time_str = format_time_duration(flight_time_seconds)
        flight_emissions = result.total_emissions

    # Check route feasibility
    rail_feasible = calculate_transport_emissions(
        'rail',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    ) is not None

    bus_feasible = calculate_transport_emissions(
        'bus',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    ) is not None

    try:
        conn = sqlite3.connect('data/routes.db')
        cursor = conn.cursor()

        cursor.execute("""
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
      """, (result.distance_km / (2 if result.is_round_trip else 1),))

        route_data = cursor.fetchone()
        if route_data:
            multiplier = 2 if result.is_round_trip else 1

            # Rail data handling
            if rail_feasible:
                transit_time_seconds = route_data[0] * multiplier if route_data[0] else 1800
                transit_time_str = format_time_duration(transit_time_seconds)
                transit_time_diff = format_time_diff(transit_time_seconds - flight_time_seconds)
                transit_distance = route_data[1] * multiplier if route_data[1] else (
                    15 if is_derby else result.distance_km)
                rail_emissions = route_data[2] * multiplier if route_data[2] else calculate_transport_emissions(
                    'rail',
                    15 if is_derby else result.distance_km,
                    st.session_state.form_state['passengers'],
                    result.is_round_trip
                )
            else:
                transit_time_str = "N/A*"
                transit_time_diff = "N/A"
                transit_distance = "N/A"
                rail_emissions = None

            # Bus data handling
            if bus_feasible:
                driving_time_seconds = route_data[3] * multiplier if route_data[3] else 2700
                driving_time_str = format_time_duration(driving_time_seconds)
                driving_time_diff = format_time_diff(driving_time_seconds - flight_time_seconds)
                driving_distance = route_data[4] * multiplier if route_data[4] else (
                    15 if is_derby else result.distance_km)
                bus_emissions = route_data[5] * multiplier if route_data[5] else calculate_transport_emissions(
                    'bus',
                    15 if is_derby else result.distance_km,
                    st.session_state.form_state['passengers'],
                    result.is_round_trip
                )
            else:
                driving_time_str = "N/A*"
                driving_time_diff = "N/A"
                driving_distance = "N/A"
                bus_emissions = None

        else:
            # Default values for routes not in database
            if rail_feasible:
                transit_time_str = "30 minutes" if is_derby else "N/A*"
                transit_time_diff = "-"
                transit_distance = 15 if is_derby else result.distance_km
                rail_emissions = calculate_transport_emissions(
                    'rail',
                    5 if is_derby else result.distance_km,
                    st.session_state.form_state['passengers'],
                    result.is_round_trip
                )
            else:
                transit_time_str = "N/A*"
                transit_time_diff = "N/A"
                transit_distance = "N/A"
                rail_emissions = None

            if bus_feasible:
                driving_time_str = "45 minutes" if is_derby else "N/A*"
                driving_time_diff = "-"
                driving_distance = 5 if is_derby else result.distance_km
                bus_emissions = calculate_transport_emissions(
                    'bus',
                    5 if is_derby else result.distance_km,
                    st.session_state.form_state['passengers'],
                    result.is_round_trip
                )
            else:
                driving_time_str = "N/A*"
                driving_time_diff = "N/A"
                driving_distance = "N/A"
                bus_emissions = None

    except Exception as e:
        st.error(f"Error retrieving transport data: {str(e)}")
        return

    finally:
        if 'conn' in locals():
            conn.close()
        st.markdown("""
      <style>
      .styled-table {
          width: 100%;
          border-collapse: collapse;
          margin: 25px 0;
          background-color: transparent;
          font-family: -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 14px;
      }
      .styled-table thead tr {
          background-color: transparent;
          color: #6B7280;
          text-align: center;
          font-weight: normal;
          height: 50px;
      }
      .styled-table th,
      .styled-table td {
          padding: 16px 24px;
          text-align: center;
          border-bottom: 1px solid #1f2937;
          white-space: nowrap;
      }
      .styled-table tbody tr {
          color: white;
          height: 50px;
      }
      .styled-table tbody tr:last-of-type {
          border-bottom: none;
      }
      .styled-table tbody tr:hover {
          background-color: #1f2937;
      }
      [data-testid="stExpander"] {
          min-width: 100%;
          padding: 16px;
      }
      .footnotes {
          font-size: 12px;
          color: #6B7280;
          margin-top: 8px;
          padding-left: 16px;
      }
      </style>
  """, unsafe_allow_html=True)
        st.markdown(f"""
           <table class="styled-table">
               <thead>
                   <tr>
                       <th>Mode</th>
                       <th>Est. Travel Time</th>
                       <th>Time Impact</th>
                       <th>Distance (km)</th>
                       <th>CO₂ (tons)</th>
                       <th>CO₂ Saved (tons)</th>
                   </tr>
               </thead>
               <tbody>
                   <tr>
                       <td>✈️ Air</td>
                       <td>{flight_time_str}</td>
                       <td>-</td>
                       <td>{"N/A" if is_derby else f"{result.distance_km:,.1f}"}</td>
                       <td>{flight_emissions:.2f}</td>
                       <td>0.00</td>
                   </tr>
                   <tr>
                       <td>🚂 Rail</td>
                       <td>{transit_time_str}</td>
                       <td>{transit_time_diff}</td>
                       <td>{"N/A" if not rail_feasible else f"{transit_distance:,.1f}" if isinstance(transit_distance, (int, float)) else "N/A"}</td>
                       <td>{"N/A" if not rail_feasible else f"{rail_emissions:.2f}" if rail_emissions is not None else "N/A"}</td>
                       <td>{"N/A" if not rail_feasible else f"{max(0, flight_emissions - rail_emissions):.2f}" if rail_emissions is not None else "N/A"}</td>
                   </tr>
                   <tr>
                       <td>🚌 Bus</td>
                       <td>{driving_time_str}</td>
                       <td>{driving_time_diff}</td>
                       <td>{"N/A" if not bus_feasible else f"{driving_distance:,.1f}" if isinstance(driving_distance, (int, float)) else "N/A"}</td>
                       <td>{"N/A" if not bus_feasible else f"{bus_emissions:.2f}" if bus_emissions is not None else "N/A"}</td>
                       <td>{"N/A" if not bus_feasible else f"{max(0, flight_emissions - bus_emissions):.2f}" if bus_emissions is not None else "N/A"}</td>
                   </tr>
               </tbody>
           </table>
           <div class="footnotes">
               {rail_note}<br/>
               {bus_note}
           </div>
           """, unsafe_allow_html=True)
    return rail_emissions, bus_emissions


def display_carbon_price_analysis(air_emissions, rail_emissions, bus_emissions, away_team, home_team):
    """Display carbon price analysis with proper formatting"""
    st.markdown("### 💰 Carbon Price Analysis")

    # Get carbon price and display header
    carbon_price = get_carbon_price(away_team, home_team)
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')
    st.markdown(f"**Carbon Price ({away_country}): €{carbon_price:.2f}/tCO₂**")

    # 1. Carbon Price Costs Table
    st.markdown("#### Carbon Price Costs")

    carbon_data = {
        "Mode": ["Air", "Rail", "Bus"],
        "Carbon Cost (€)": [
            air_emissions * carbon_price,
            rail_emissions * carbon_price if rail_emissions else None,
            bus_emissions * carbon_price if bus_emissions else None
        ]
    }

    carbon_df = pd.DataFrame(carbon_data)
    st.markdown(carbon_df.style.format({
        "Carbon Cost (€)": lambda x: f"€{x:,.2f}" if pd.notnull(x) else "N/A"
    }).hide().to_html(), unsafe_allow_html=True)

    # 2. Social Cost of Carbon Table
    st.markdown("#### Social Cost of Carbon")

    # Define cost sources with their metadata
    cost_sources = [
        ('IWG', 'iwg_75th', "Interagency Working Group 95th percentile estimate"),
        ('EPA', 'epa_median', "U.S. Environmental Protection Agency estimate"),
        ('Synthetic', 'synthetic_median', "Meta-analysis combining multiple studies"),
        ('NBER', 'nber_research', "National Bureau of Economic Research estimate")
    ]

    # Sort by median value (using pre-sorted order from definitions)
    social_data = []
    for source, key, description in cost_sources:
        social_data.append({
            "Cost Source": source,
            "Air": air_emissions * SOCIAL_CARBON_COSTS[key],
            "Rail": rail_emissions * SOCIAL_CARBON_COSTS[key] if rail_emissions else None,
            "Bus": bus_emissions * SOCIAL_CARBON_COSTS[key] if bus_emissions else None
        })

    social_df = pd.DataFrame(social_data)
    st.markdown(social_df.style.format({
        "Air": "€{:,.2f}",
        "Rail": lambda x: f"€{x:,.2f}" if pd.notnull(x) else "N/A",
        "Bus": lambda x: f"€{x:,.2f}" if pd.notnull(x) else "N/A"
    }).hide().to_html(index=False), unsafe_allow_html=True)

    # 3. Cost Type Definitions (now matches social cost order)
    st.markdown("#### Cost Type Definitions")

    definitions_data = {
        "Cost Source": [f"{source} ({desc})" for source, _, desc in cost_sources],
        "Median Values (€/tCO₂)": [f"€{SOCIAL_CARBON_COSTS[key]:.0f}" for _, key, _ in cost_sources]
    }

    definitions_df = pd.DataFrame(definitions_data)
    st.markdown(definitions_df.style.hide(axis="index").to_html(), unsafe_allow_html=True)

    # Table styling
    st.markdown("""
    <style>
    table {
        width: 100% !important;
        margin: 1rem 0;
        border-collapse: collapse;
    }
    th {
        text-align: center !important;
        background-color: #1f2937;
        color: white;
        padding: 8px;
        border: 1px solid #2d3748;
    }
    td {
        text-align: center !important;
        padding: 8px;
        border: 1px solid #2d3748;
    }
    tr:nth-child(even) {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)


def display_economic_impacts(result, home_team, away_team):
    """Display economic impact analysis for the flight."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Flight Details")
        st.metric("Distance", f"{result.distance_km:,.0f} km")
        st.metric("Total Emissions", f"{result.total_emissions:,.2f} tons CO2")
        st.metric("Fuel Consumption", f"{result.fuel_consumption:,.0f} L")

    with col2:
        st.markdown("### Carbon Pricing Schemes")
        calculator = EnhancedCarbonPricingCalculator()
        home_country = TEAM_COUNTRIES.get(home_team, 'EU')
        away_country = TEAM_COUNTRIES.get(away_team, 'EU')

        pricing_explanation = calculator.get_pricing_explanation(home_country, away_country)
        st.markdown(pricing_explanation)

    # Calculate costs
    costs = calculator.calculate_carbon_costs(
        origin=home_country,
        destination=away_country,
        emissions=result.total_emissions,  # Using ICAO emissions
        fuel_usage=result.fuel_consumption,
        include_forecast=True
    )

    # Create tabs for different analyses
    costs_tab, fuel_tab, forecast_tab = st.tabs(["Current Costs", "Fuel Analysis", "Cost Forecast"])

    with costs_tab:
        st.markdown("### Current Costs")
        cost_cols = st.columns(4)
        with cost_cols[0]:
            st.metric("EU ETS Cost", f"€{costs['current_costs']['eu_ets']:,.2f}")
        with cost_cols[1]:
            st.metric("National Tax", f"€{costs['current_costs']['national']:,.2f}")
        with cost_cols[2]:
            st.metric("Fuel Cost", f"€{costs['current_costs']['fuel']:,.2f}")
        with cost_cols[3]:
            st.metric("Total Cost", f"€{costs['current_costs']['total']:,.2f}")

    with fuel_tab:
        st.markdown("### Fuel Cost Analysis")
        st.markdown("""
        Emissions are distributed proportionally between conventional fuel and SAF 
        based on the fuel mix ratio (98% conventional, 2% SAF)
        """)

        fuel_cols = st.columns(2)
        with fuel_cols[0]:
            st.markdown("#### Conventional Jet A-1 (98%)")
            conv = costs['fuel_breakdown']['conventional']
            st.metric("Volume", f"{conv['volume']:,.0f} L")
            st.metric("Cost", f"€{conv['cost']:,.2f}")
            st.metric("Proportional Emissions", f"{conv['emissions']:,.2f} tons")

        with fuel_cols[1]:
            st.markdown("#### Sustainable Aviation Fuel (2%)")
            saf = costs['fuel_breakdown']['saf']
            st.metric("Volume", f"{saf['volume']:,.0f} L")
            st.metric("Cost", f"€{saf['cost']:,.2f}")
            st.metric("Proportional Emissions", f"{saf['emissions']:,.2f} tons")

        # Calculate and display cost differences
        cost_difference = saf['cost'] - conv['cost']
        emissions_saved = conv['emissions'] * (0.75)  # SAF reduces emissions by ~75%
        st.markdown("#### Cost-Benefit Analysis")
        diff_cols = st.columns(2)
        with diff_cols[0]:
            st.metric("Current SAF Premium", f"€{cost_difference:,.2f}",
                      delta=f"{(cost_difference/conv['cost'])*100:.1f}%")
        with diff_cols[1]:
            st.metric("Potential Emissions Saved (with 100% SAF)",
                      f"{emissions_saved:,.2f} tons",
                      delta=f"-{75:.0f}%")

        st.markdown("""
        *Note: The 'Potential Emissions Saved' shows the theoretical reduction if using 100% SAF,
        which typically reduces emissions by ~75% compared to conventional fuel.*
        """)

    with forecast_tab:
        if costs['forecast']:
            st.markdown("### Cost Forecast")
            forecast_data = pd.DataFrame(costs['forecast']).T

            st.markdown("#### Total Cost Trend")
            st.line_chart(forecast_data[['total_cost']])

            st.markdown("#### Cost Components")
            components = ['eu_ets_price', 'conventional_fuel_cost', 'saf_fuel_cost', 'carbon_cost']
            component_data = forecast_data[components]
            st.line_chart(component_data)

            display_cols = {
                'eu_ets_price': 'EU ETS Price',
                'saf_requirement': 'SAF Requirement',
                'conventional_fuel_cost': 'Conventional Fuel Cost',
                'saf_fuel_cost': 'SAF Cost',
                'carbon_cost': 'Carbon Cost',
                'total_cost': 'Total Cost'
            }
            formatted_df = forecast_data[display_cols.keys()].rename(columns=display_cols)
            st.dataframe(formatted_df.style.format("€{:,.2f}"))

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

    st.header("Copyright")
    st.write("""
    
    
    © 2024 Football Emissions Calculator
    All rights reserved
            
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

    # If auto_calculate flag is set, trigger calculation immediately

    if st.session_state.calculator_input.get('auto_calculate', False):
        with st.spinner("Calculating emissions..."):
            calculate_and_display()

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
        st.session_state.last_calculation['result']
    )
