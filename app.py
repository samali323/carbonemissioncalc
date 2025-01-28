import sqlite3

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.config.constants import SOCIAL_CARBON_COSTS
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.models.emissions import EmissionsCalculator
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time, format_time_duration
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


def display_results(result, rail_emissions=None, bus_emissions=None,
                    flight_salary_impact=None, rail_salary_impact=None, bus_salary_impact=None):
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

    # Economic Impact Analysis as a separate top-level expander
    with st.expander("💸 Economic Impact Analysis", expanded=False):
        display_economic_impacts(
            result=result,
            home_team=st.session_state.form_state['home_team'],
            away_team=st.session_state.form_state['away_team'],
            flight_salary_impact=flight_salary_impact,
            rail_salary_impact=rail_salary_impact,
            bus_salary_impact=bus_salary_impact
        )

        # Cost Analysis (collapsible)
    with st.expander("💰 Carbon Price Breakdown", expanded=False):
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

    try:
        conn = sqlite3.connect('data/routes.db')
        cursor = conn.cursor()

        # Get route data
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

        # Get salary data
        cursor.execute("""
            SELECT gross_per_minute
            FROM team_salaries
            WHERE team = ?
        """, (home_team,))
        salary_data = cursor.fetchone()
        team_salary = salary_data[0] if salary_data else None

        if route_data:
            multiplier = 2 if result.is_round_trip else 1

            # Rail data handling
            if rail_feasible:
                transit_time_seconds = route_data[0] * multiplier if route_data[0] else 1800
                transit_time_str = format_time_duration(transit_time_seconds)
                transit_time_diff = format_time_diff(transit_time_seconds - flight_time_seconds)
                transit_distance = route_data[1] * multiplier if route_data[1] else (15 if is_derby else result.distance_km)
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
                transit_time_seconds = 0

            # Bus data handling
            if bus_feasible:
                driving_time_seconds = route_data[3] * multiplier if route_data[3] else 2700
                driving_time_str = format_time_duration(driving_time_seconds)
                driving_time_diff = format_time_diff(driving_time_seconds - flight_time_seconds)
                driving_distance = route_data[4] * multiplier if route_data[4] else (15 if is_derby else result.distance_km)
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
                driving_time_seconds = 0

        else:
            # Default values for routes not in database
            if rail_feasible:
                transit_time_str = "30 minutes" if is_derby else "N/A*"
                transit_time_diff = "-"
                transit_distance = 15 if is_derby else result.distance_km
                transit_time_seconds = 1800 if is_derby else 0
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
                transit_time_seconds = 0

            if bus_feasible:
                driving_time_str = "45 minutes" if is_derby else "N/A*"
                driving_time_diff = "-"
                driving_distance = 5 if is_derby else result.distance_km
                driving_time_seconds = 2700 if is_derby else 0
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
                driving_time_seconds = 0

        # Calculate salary impacts
        flight_salary_impact = (flight_time_seconds/60) * team_salary if team_salary else None
        rail_salary_impact = (transit_time_seconds/60) * team_salary if team_salary and rail_feasible else None
        bus_salary_impact = (driving_time_seconds/60) * team_salary if team_salary and bus_feasible else None

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
                        <th>Salary Impact (€)</th>
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
                        <td>{f"€{flight_salary_impact:,.2f}" if flight_salary_impact is not None else "N/A"}</td>
                        <td>{"N/A" if is_derby else f"{result.distance_km:,.1f}"}</td>
                        <td>{flight_emissions:.2f}</td>
                        <td>0.00</td>
                    </tr>
                    <tr>
                        <td>🚂 Rail</td>
                        <td>{transit_time_str}</td>
                        <td>{transit_time_diff}</td>
                        <td>{f"€{rail_salary_impact:,.2f}" if rail_salary_impact is not None else "N/A"}</td>
                        <td>{"N/A" if not rail_feasible else f"{transit_distance:,.1f}" if isinstance(transit_distance, (int, float)) else "N/A"}</td>
                        <td>{"N/A" if not rail_feasible else f"{rail_emissions:.2f}" if rail_emissions is not None else "N/A"}</td>
                        <td>{"N/A" if not rail_feasible else f"{max(0, flight_emissions - rail_emissions):.2f}" if rail_emissions is not None else "N/A"}</td>
                    </tr>
                    <tr>
                        <td>🚌 Bus</td>
                        <td>{driving_time_str}</td>
                        <td>{driving_time_diff}</td>
                        <td>{f"€{bus_salary_impact:,.2f}" if bus_salary_impact is not None else "N/A"}</td>
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

    return rail_emissions, bus_emissions, flight_salary_impact, rail_salary_impact, bus_salary_impact


def display_economic_impacts(result, home_team, away_team,flight_salary_impact, rail_salary_impact, bus_salary_impact):
    """Display economic impact analysis with costs summary and all optimization options."""
    calculator = EnhancedCarbonPricingCalculator()
    home_country = TEAM_COUNTRIES.get(home_team, 'EU')
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')

    # Flight time calculation
    flight_time_seconds = calculate_flight_time(
        distance_km=result.distance_km / (2 if result.is_round_trip else 1),
        is_round_trip=result.is_round_trip
    )
    flight_hours = flight_time_seconds / 3600

    # Alternative transport emissions
    rail_emissions = calculate_transport_emissions(
        'rail',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    )
    bus_emissions = calculate_transport_emissions(
        'bus',
        result.distance_km,
        st.session_state.form_state['passengers'],
        result.is_round_trip,
        home_team,
        away_team
    )

    # Fuel costs calculation
    FUEL_PRICE_PER_L = 2.5
    SAF_PRICE_PER_L = 7.5
    conventional_fuel_volume = result.fuel_consumption * 0.98
    saf_fuel_volume = result.fuel_consumption * 0.02
    conventional_fuel_cost = conventional_fuel_volume * FUEL_PRICE_PER_L
    saf_fuel_cost = saf_fuel_volume * SAF_PRICE_PER_L
    total_fuel_cost = conventional_fuel_cost + saf_fuel_cost

    # Carbon costs calculation
    eu_ets_cost = result.total_emissions * calculator.EU_ETS_PRICE
    national_carbon_tax = result.total_emissions * calculator.CARBON_PRICES.get(home_country, 0)
    total_carbon_cost = eu_ets_cost + national_carbon_tax

    # Social costs calculation
    social_costs = {
        'iwg': result.total_emissions * SOCIAL_CARBON_COSTS['iwg_75th'],
        'epa': result.total_emissions * SOCIAL_CARBON_COSTS['epa_median'],
        'synthetic': result.total_emissions * SOCIAL_CARBON_COSTS['synthetic_median'],
        'nber': result.total_emissions * SOCIAL_CARBON_COSTS['nber_research']
    }
    avg_social_cost = sum(social_costs.values()) / len(social_costs)

    # Operational costs calculation
    operational_costs = {
        'base_charter': flight_hours * 25000,
        'landing_fees': 10000,
        'catering': 3500,
        'ground_transport': 2250,
    }

    if result.is_round_trip:
        operational_costs = {k: v * 2 for k, v in operational_costs.items()}
        total_fuel_cost *= 2
        total_carbon_cost *= 2

    # Total costs calculation
    total_charter = sum(operational_costs.values())
    total_operational = total_charter + total_fuel_cost
    total_environmental = total_carbon_cost + avg_social_cost
    total_flight_salary_impact = flight_salary_impact
    total_cost = total_operational + total_environmental + total_flight_salary_impact

    # Alternative costs and savings
    alternatives = {
        'empty_leg': {
            'operational': total_operational * 0.25,
            'carbon': total_carbon_cost,
            'social': avg_social_cost,
            'salary': flight_salary_impact
        },
        'regional_airport': {
            'operational': total_operational - (operational_costs['landing_fees'] * 0.3),
            'carbon': total_carbon_cost,
            'social': avg_social_cost,
            'salary': flight_salary_impact
        },
        'bulk_rate': {
            'operational': total_operational * 0.85,
            'carbon': total_carbon_cost,
            'social': avg_social_cost,
            'salary': flight_salary_impact
        },
        'split_charter': {
            'operational': total_operational * 2,
            'carbon': total_carbon_cost * 2,
            'social': avg_social_cost * 2,
            'salary': flight_salary_impact/2
        }
    }

    # Add transport alternatives
    if rail_emissions:
        alternatives['rail'] = {
            'operational': total_operational * 0.1,
            'carbon': rail_emissions * calculator.EU_ETS_PRICE,
            'social': rail_emissions * (sum(SOCIAL_CARBON_COSTS.values()) / len(SOCIAL_CARBON_COSTS)),
            'salary': rail_salary_impact

        }

    if bus_emissions:
        alternatives['bus'] = {
            'operational': total_operational * 0.2,
            'carbon': bus_emissions * calculator.EU_ETS_PRICE,
            'social': bus_emissions * (sum(SOCIAL_CARBON_COSTS.values()) / len(SOCIAL_CARBON_COSTS)),
            'salary': bus_salary_impact
        }

    # Store cost components
    cost_data = {
        'operational_costs': operational_costs,
        'fuel': {
            'conventional': {
                'volume': conventional_fuel_volume,
                'cost': conventional_fuel_cost
            },
            'saf': {
                'volume': saf_fuel_volume,
                'cost': saf_fuel_cost
            },
            'total': total_fuel_cost
        },
        'carbon': {
            'eu_ets': eu_ets_cost,
            'national': national_carbon_tax,
            'total': total_carbon_cost
        },
        'social': social_costs,
        'totals': {
            'operational': total_operational,
            'environmental': total_environmental,
            'total': total_cost
        }
    }

    # Create tabs
    summary_tab, ops_tab, carbon_tab, viz_tab,advanced_tab = st.tabs(["Summary", "Operational Costs", "Carbon Costs", "Visualizations", "Advanced Analysis"])

    # Custom CSS for centered tables
    st.markdown("""
    <style>
    .centered-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: Arial, sans-serif;
    }
    .centered-table th, .centered-table td {
        padding: 12px;
        text-align: center;
        border-bottom: 1px solid #ddd;
    }
    .centered-table th {
        background-color: #f8f9fa;
        font-weight: 600;
        color: #2c3e50;
    }
    .centered-table tr:hover {
        background-color: #04470a;
    }
    .currency {
        font-family: 'Arial', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    def format_currency(value):
        return f"€{value:,.2f}"

    def create_centered_table(headers, data):
        table_html = """
        <table class='centered-table'>
            <thead><tr>%s</tr></thead>
            <tbody>%s</tbody>
        </table>
        """
        header_cols = "".join(f"<th>{h}</th>" for h in headers)
        data_rows = "".join(
            f"<tr>{''.join(f'<td class=\'currency\'>{d}</td>' for d in row)}</tr>"
            for row in data
        )
        return table_html % (header_cols, data_rows)

    with summary_tab:
        with st.markdown("Flight Impact Summary", ):
            # Economic Impact Table
            headers = ["Cost Category", "Amount (€)"]
            data = [
                ["Operational Costs", format_currency(total_operational)],
                ["Environmental Impact", format_currency(total_environmental)],
                ["Salary Impact", format_currency(total_flight_salary_impact)],
                ["Total Cost", format_currency(total_cost)]
            ]
            st.markdown(create_centered_table(headers, data), unsafe_allow_html=True)

        # Potential Cost Savings
        with st.markdown("### Potential Cost Savings"):
            savings_data = []
            for option, costs in alternatives.items():
                total_alt_operational = costs['operational']
                total_alt_carbon = costs['carbon']
                total_alt_social = costs['social']
                alt_salary_impact = costs['salary'] if costs['salary'] is not None else 0

                total_alt_cost = total_alt_operational + total_alt_carbon + total_alt_social + alt_salary_impact
                savings = total_cost - total_alt_cost
                savings_percent = (savings / total_cost) * 100

                savings_display = f"Savings: {format_currency(savings)}" if savings >= 0 else f"Additional Cost: {format_currency(abs(savings))}"
                savings_percent_display = f"{savings_percent:.1f}%" if savings >= 0 else f"{abs(savings_percent):.1f}%"

                savings_data.append([
                    option.replace('_', ' ').title(),
                    format_currency(total_alt_cost),
                    savings_display,
                    savings_percent_display
                ])

            headers = ["Option", "Total Cost", "Financial Impact", "Impact %"]
            st.markdown(create_centered_table(headers, savings_data), unsafe_allow_html=True)


        # Environmental Impact Table
        if rail_emissions and bus_emissions:
            with st.markdown("### Environmental Impact Reduction"):
                headers = ["Transport Mode", "CO₂ Emissions (tons)", "Reduction %"]
                data = [
                    ["Air", f"{result.total_emissions:,.2f}", "0.0%"],
                    ["Rail", f"{rail_emissions:,.2f}", f"{((result.total_emissions - rail_emissions)/result.total_emissions*100):.1f}%"],
                    ["Bus", f"{bus_emissions:,.2f}", f"{((result.total_emissions - bus_emissions)/result.total_emissions*100):.1f}%"]
                ]
                st.markdown(create_centered_table(headers, data), unsafe_allow_html=True)

        with st.markdown("Cost Breakdown for Alternative Methods"):
            # Create headers and data for detailed breakdown
            breakdown_headers = ["Option", "Operational Cost", "Carbon Cost", "Social Cost", "Salary Impact", "Total Cost"]
            breakdown_data = []

            for option, costs in alternatives.items():
                total_alt_operational = costs['operational']
                total_alt_carbon = costs['carbon']
                total_alt_social = costs['social']
                alt_salary_impact = costs['salary'] if costs['salary'] is not None else 0
                total_alt_cost = total_alt_operational + total_alt_carbon + total_alt_social + alt_salary_impact

                breakdown_data.append([
                    option.replace('_', ' ').title(),
                    format_currency(total_alt_operational),
                    format_currency(total_alt_carbon),
                    format_currency(total_alt_social),
                    format_currency(alt_salary_impact),
                    format_currency(total_alt_cost)
                ])

            # Render the table
            st.markdown(create_centered_table(breakdown_headers, breakdown_data), unsafe_allow_html=True)


        # Footnotes
        st.markdown("---")
        st.markdown("""
        **Footnotes:**
         **Cost Reduction Options:**
        1. **Empty Leg Flight (Discounted Return)** 
           - Book a private aircraft that needs to return to its base
           - Significant discount but limited schedule flexibility
           - Same comfort and speed as regular charter
        
        2. **Regional Airport Option**
           - Use smaller airports with lower landing fees
           - 30% reduction in airport costs
           - May require longer ground transport time
        
        3. **Bulk Booking Discount**
           - Pre-book multiple flights for the season
           - 15% discount on total costs
           - Requires advance planning
        
        4. **Split Charter (Shared Flight)**
           - Share aircraft with another team
           - Split total costs 50/50
           - Requires schedule coordination
        
        **Alternative Transport Options:**
        - **Rail Transport**: Lower emissions but longer journey time
        - **Bus Transport**: Most economical but longest travel time
        
        💡 **Recommendation:** Consider your priorities (cost vs. time vs. flexibility) when choosing an option.
        """, unsafe_allow_html=True)

    with ops_tab:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Base Charter Costs")
            st.markdown(f"""
            <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
                Flight Duration: {flight_hours:.1f} hours<br>
                Charter Rate: €25,000/hour<br>
                Base Charter Cost: {format_currency(operational_costs['base_charter'])}<br>
                Landing Fees: {format_currency(operational_costs['landing_fees'])}<br>
                Catering: {format_currency(operational_costs['catering'])}<br>
                Ground Transport: {format_currency(operational_costs['ground_transport'])}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("#### Fuel Mix Configuration")

            # Add slider for SAF percentage
            saf_percentage = st.slider(
                "SAF Percentage in Fuel Mix",
                min_value=0,
                max_value=100,
                value=2,
                help="Percentage of Sustainable Aviation Fuel in the total fuel mix"
            )

            # Add price adjustments
            col_conv, col_saf = st.columns(2)
            with col_conv:
                conventional_price = st.number_input(
                    "Conventional Fuel Price (€/L)",
                    min_value=1.0,
                    max_value=10.0,
                    value=2.5,
                    step=0.1
                )

            with col_saf:
                saf_price = st.number_input(
                    "SAF Price (€/L)",
                    min_value=1.0,
                    max_value=20.0,
                    value=7.5,
                    step=0.1
                )

            # Calculate volumes and costs based on user inputs
            conventional_percentage = 100 - saf_percentage
            total_fuel = result.fuel_consumption  # Total fuel volume in liters

            conventional_volume = total_fuel * (conventional_percentage/100)
            saf_volume = total_fuel * (saf_percentage/100)

            conventional_cost = conventional_volume * conventional_price
            saf_cost = saf_volume * saf_price
            total_cost = conventional_cost + saf_cost

            # Display fuel breakdown
            st.markdown("#### Fuel Breakdown")
            st.markdown(f"""
            <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
                <b>Conventional Jet A-1 ({conventional_percentage}%)</b><br>
                Volume: {conventional_volume:.0f}L<br>
                Cost: {format_currency(conventional_cost)}<br><br>
                <b>SAF ({saf_percentage}%)</b><br>
                Volume: {saf_volume:.0f}L<br>
                Cost: {format_currency(saf_cost)}<br><br>
                <b>Total Fuel Cost: {format_currency(total_cost)}</b>
            </div>
            """, unsafe_allow_html=True)

            # Calculate and display emissions impact
            conventional_emissions = conventional_volume * 3.16  # kg CO2/L
            saf_emissions = saf_volume * 0.80  # kg CO2/L (approximately 80% reduction)
            total_emissions = conventional_emissions + saf_emissions
            baseline_emissions = total_fuel * 3.16  # If using 100% conventional fuel

            emissions_saved = baseline_emissions - total_emissions
            emissions_saved_percentage = (emissions_saved / baseline_emissions) * 100

            st.markdown("#### Emissions Impact")
            st.markdown(f"""
            <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
                <b>Emissions Savings:</b><br>
                {emissions_saved/1000:.2f} tons CO₂ ({emissions_saved_percentage:.1f}% reduction)<br>
                Equivalent to {(emissions_saved/1000 * 2.47):.1f} trees planted
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Total Operational Costs")
        total_operational = total_charter + total_cost
        st.markdown(f"""
        <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
            Charter Costs: {format_currency(total_charter)}<br>
            Fuel Costs: {format_currency(total_cost)}<br>
            <strong>Total: {format_currency(total_operational)}</strong>
        </div>
        """, unsafe_allow_html=True)

    with carbon_tab:
        st.markdown("### Carbon Price Analysis")
        st.markdown("#### Carbon Price Components")
        st.markdown(f"""
        <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
            EU ETS Cost (€{calculator.EU_ETS_PRICE:.2f}/ton): {format_currency(cost_data['carbon']['eu_ets'])}<br>
            National Carbon Tax (€{calculator.CARBON_PRICES.get(home_country, 0):.2f}/ton): {format_currency(cost_data['carbon']['national'])}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Calculation Details")
        st.markdown(f"""
        <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
            Emissions: {result.total_emissions:.2f} tons CO₂<br>
            Total Carbon Cost: {format_currency(cost_data['carbon']['total'])}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Social Cost of Carbon")
        st.markdown(f"""
        <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
            IWG (95th percentile): {format_currency(social_costs['iwg'])}<br>
            EPA Median: {format_currency(social_costs['epa'])}<br>
            Synthetic Median: {format_currency(social_costs['synthetic'])}<br>
            NBER Research: {format_currency(social_costs['nber'])}<br>
            <strong>Average Social Cost: {format_currency(avg_social_cost)}</strong>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Total Environmental Impact Cost")
        st.markdown(f"""
        <div style='padding: 15px; background-color: transparent; border-radius: 5px;'>
            Carbon Market Cost: {format_currency(cost_data['carbon']['total'])}<br>
            Social Cost: {format_currency(avg_social_cost)}<br>
            <strong>Total Environmental Cost: {format_currency(cost_data['totals']['environmental'])}</strong>
        </div>
        """, unsafe_allow_html=True)


    with viz_tab:
        st.markdown("### 📈 Future Cost Projections")

        # Generate projection data
        projection_years = 10
        base_year = 2024
        years = list(range(base_year, base_year + projection_years))

        # Combined fuel and carbon price projections
        combined_df = pd.DataFrame({
            'Year': years,
            'Conventional Fuel': [round(2.5 * (1.05)**i, 2) for i in range(projection_years)],
            'Sustainable Aviation Fuel': [round(7.5 * (0.97)**i, 2) for i in range(projection_years)],
            'EU ETS': [round(calculator.EU_ETS_PRICE * (1.08)**i, 2) for i in range(projection_years)],
            'National Carbon Tax': [round(calculator.CARBON_PRICES.get(home_country, 0) * (1.06)**i, 2) for i in range(projection_years)]
        })

        # Check if national carbon tax is 0
        if calculator.CARBON_PRICES.get(home_country, 0) == 0:
            st.info(f"""
            📝 **Note on National Carbon Tax:**  
            {home_team} is based in {home_country}, which currently does not have a national carbon tax 
            or has not implemented specific aviation carbon pricing beyond the EU ETS scheme.
            """)

        # Create figure with adjusted y-axis range
        fig = px.line(combined_df, x='Year',
                      y=['Conventional Fuel', 'Sustainable Aviation Fuel', 'EU ETS', 'National Carbon Tax'],
                      title='Combined Price Projections')

        # Update layout with adjusted y-axis range
        max_fuel_price = max(max(combined_df['Conventional Fuel']), max(combined_df['Sustainable Aviation Fuel']))
        max_carbon_price = max(max(combined_df['EU ETS']), max(combined_df['National Carbon Tax']))

        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            xaxis=dict(tickmode='array', tickvals=years),
            yaxis=dict(
                title='Price (€)',
                range=[0, max(max_fuel_price, max_carbon_price) * 1.1]  # Set range with 10% padding
            ),
            legend_title='Price Component',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Update line styles
        for i in range(len(fig.data)):
            if i >= 2:  # Make carbon price lines dashed
                fig.data[i].line.dash = 'dash'

        st.plotly_chart(fig, use_container_width=True)
        # Cumulative Cost Impact
        st.markdown("### 📊 Cumulative Cost Impact")

        # Calculate cumulative costs with rounded values
        operational_costs = [round(total_operational * (1.04)**i) for i in range(projection_years)]
        carbon_costs = [round(total_carbon_cost * (1.08)**i) for i in range(projection_years)]
        fuel_costs = [round(total_fuel_cost * (1.05)**i) for i in range(projection_years)]

        cumulative_df = pd.DataFrame({
            'Year': years,
            'Operational Costs': operational_costs,
            'Carbon Costs': carbon_costs,
            'Fuel Costs': fuel_costs
        })

        fig_cumulative = px.area(
            cumulative_df,
            x='Year',
            y=['Operational Costs', 'Carbon Costs', 'Fuel Costs'],
            title='Projected Cumulative Costs',
            template='plotly_dark'
        )
        fig_cumulative.update_layout(
            yaxis_title='Cost (€)',
            hovermode='x unified',
            showlegend=True,
            legend_title_text='Cost Component',
            xaxis=dict(tickmode='array', tickvals=years)
        )
        st.plotly_chart(fig_cumulative, use_container_width=True)

        # Add Total Cost Projection
        total_costs = [round(sum(x)) for x in zip(operational_costs, carbon_costs, fuel_costs)]
        total_df = pd.DataFrame({
            'Year': years,
            'Total Cost': total_costs
        })

        fig_total = px.line(
            total_df,
            x='Year',
            y='Total Cost',
            title='Total Cost Projection',
            template='plotly_dark'
        )
        fig_total.update_layout(
            yaxis_title='Total Cost (€)',
            hovermode='x unified',
            xaxis=dict(tickmode='array', tickvals=years)
        )
        st.plotly_chart(fig_total, use_container_width=True)

        # Key Assumptions
        st.markdown("""
        #### Key Assumptions (10-Year Outlook):
        - Conventional fuel prices increase by 5% annually
        - SAF prices decrease by 3% annually due to scaling effects
        - EU ETS carbon prices increase by 8% annually
        - National carbon prices increase by 6% annually
        - Operational costs increase by 4% annually
        
        These long-term projections help visualize the potential future cost impacts and can assist in strategic planning and sustainability initiatives over the next decade.
        """)

        # Enhanced scenario analysis section
        st.markdown("### 🔄 Scenario Analysis")

        st.markdown("""
        This analysis explores three possible future scenarios to help understand potential cost variations:
        
        ##### 🎯 Base Case Scenario
        - Follows current market trends
        - Conventional fuel: 5% annual increase
        - Carbon prices: 8% annual increase
        - Operational costs: 4% annual increase
        
        ##### 📈 High Growth Scenario
        - Assumes accelerated price increases due to:
            - Stricter environmental regulations
            - Higher energy demand
            - Increased operational costs
        - Conventional fuel: 8% annual increase
        - Carbon prices: 12% annual increase
        - Operational costs: 6% annual increase
        
        ##### 📉 Low Growth Scenario
        - Assumes slower price increases due to:
            - Technological improvements
            - Market efficiency gains
            - Stabilized energy prices
        - Conventional fuel: 3% annual increase
        - Carbon prices: 5% annual increase
        - Operational costs: 2% annual increase
        """)

        scenarios = {
            'Base Case': {
                'fuel_increase': 0.05,
                'carbon_increase': 0.08,
                'operational_increase': 0.04
            },
            'High Growth': {
                'fuel_increase': 0.08,
                'carbon_increase': 0.12,
                'operational_increase': 0.06
            },
            'Low Growth': {
                'fuel_increase': 0.03,
                'carbon_increase': 0.05,
                'operational_increase': 0.02
            }
        }

        scenario_data = []
        for scenario, rates in scenarios.items():
            for year in range(projection_years):
                total_cost = round(
                    total_operational * (1 + rates['operational_increase'])**year +
                    total_carbon_cost * (1 + rates['carbon_increase'])**year +
                    total_fuel_cost * (1 + rates['fuel_increase'])**year
                )
                scenario_data.append({
                    'Year': base_year + year,
                    'Scenario': scenario,
                    'Total Cost': total_cost
                })

        scenario_df = pd.DataFrame(scenario_data)

        fig_scenarios = px.line(
            scenario_df,
            x='Year',
            y='Total Cost',
            color='Scenario',
            title='Cost Scenarios Comparison',
            template='plotly_dark'
        )
        fig_scenarios.update_layout(
            yaxis_title='Total Cost (€)',
            hovermode='x unified',
            xaxis=dict(tickmode='array', tickvals=years)
        )
        st.plotly_chart(fig_scenarios, use_container_width=True)

        # Add impact analysis after scenarios
        st.markdown("""
        #### 💡 Strategic Implications
        
        The scenario analysis reveals several key insights:
        1. **Cost Exposure**: The gap between high and low growth scenarios widens significantly over time, 
           highlighting the importance of long-term cost management strategies.
        2. **Risk Management**: The different scenarios can help in developing hedging strategies for fuel 
           and carbon prices.
        3. **Investment Planning**: Understanding potential cost ranges aids in making decisions about 
           fleet modernization and sustainable aviation fuel adoption.
        """)
    with advanced_tab:
        st.markdown("### 📊 Advanced Economic Analysis")
        # Add explanation at the top
        st.info("""
        This section provides advanced financial analysis of your selected flight's costs over time. 
        It helps understand the true cost implications considering factors like:
        - Time value of money (future costs in today's terms)
        - Different growth scenarios
        - Risk and uncertainty in cost projections
        """)

        # Time Value of Money Section
        st.markdown("#### 💰 Cost Projection Analysis")
        st.markdown("""
        **Key Financial Concepts:**
        - Future costs discounted to present value
        - Operational cost growth projections
        - Carbon pricing escalations
        - Salary impact escalations
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Cost Drivers")
            discount_rate = st.number_input("Annual Discount Rate (%)",
                                    0.0,
                                    15.0,
                                    5.0,
                                    0.5,
                                    help="Used to calculate present value of future costs") / 100

            projection_years = st.number_input("Analysis Timeframe (Years)",
                                         1,
                                         30,
                                         10,
                                         help="Duration for cost projections")

        # Scenario Analysis - Flight Costs Only
        with col2:
            st.markdown("### Growth Scenarios")
            scenario_config = {
                'Base Case': {'operational': 0.03, 'carbon': 0.05, 'salary': 0.02},
                'High Growth': {'operational': 0.05, 'carbon': 0.08, 'salary': 0.04},
                'Low Growth': {'operational': 0.01, 'carbon': 0.03, 'salary': 0.01}
            }

            selected_scenario = st.radio("Select Cost Growth Scenario",
                                         list(scenario_config.keys()),
                                         index=0)

        # NPV Calculation (Flight Costs Only)
        scenario = scenario_config[selected_scenario]
        npv = 0
        cost_breakdown = []


        for year in range(projection_years):
            year_cost = (
                    total_operational * (1 + scenario['operational'])**year +
                    total_carbon_cost * (1 + scenario['carbon'])**year +
                    total_flight_salary_impact * (1 + scenario['salary'])**year
            )
            present_value = year_cost / (1 + discount_rate)**year
            npv += present_value
            cost_breakdown.append((year+1, present_value))

        # Display Results
        st.markdown(f"## Projected NPV: €{npv:,.0f}")
        st.subheader(f"Average Annual NPV: €{npv/projection_years:,.0f}")

        # Cost Breakdown Chart
        years = [f"Year {y}" for y, _ in cost_breakdown]
        values = [v for _, v in cost_breakdown]

        fig = px.area(
            x=years,
            y=values,
            labels={'x': 'Year', 'y': 'Annual Cost (€)'},
            title=f"Cost Projection - {selected_scenario} Scenario"
        )
        st.plotly_chart(fig)

        st.markdown("""
        **Key Insights:**
        - Operational costs (including fuel) typically account for 80-85% of total flight expenses
        - Carbon costs show highest volatility due to regulatory uncertainty
        - Salary impacts grow steadily based on organizational policies
        """)
        st.markdown("---")
        # In the advanced_tab section, update the break-even analysis:
        st.markdown("#### 🎯 Break-Even Analysis")
        st.markdown("""
            **Understanding Break-Even Analysis:**
            This shows when Sustainable Aviation Fuel (SAF) becomes cost-competitive with conventional fuel, 
            considering both direct fuel costs and carbon pricing impacts.
        """)

        # Extended break-even calculation (up to 30 years)
        extended_years = 30
        years_extended = list(range(base_year, base_year + extended_years))

        # Calculate prices with carbon costs included
        saf_prices = [7.5*(0.97**i) + combined_df['EU ETS'][min(i, projection_years-1)] for i in range(extended_years)]
        conv_prices = [2.5*(1.05**i) + combined_df['EU ETS'][min(i, projection_years-1)] for i in range(extended_years)]

        # Find break-even point
        try:
            break_even_year = next(i for i in range(extended_years) if saf_prices[i] < conv_prices[i])
            years_to_breakeven = break_even_year
            break_even_price = saf_prices[break_even_year]

            # Create price convergence visualization
            convergence_df = pd.DataFrame({
                'Year': years_extended,
                'SAF Total Cost': saf_prices,
                'Conventional Total Cost': conv_prices
            })

            fig_breakeven = px.line(
                convergence_df,
                x='Year',
                y=['SAF Total Cost', 'Conventional Total Cost'],
                title='Fuel Price Convergence Projection',
                template='plotly_dark'
            )

            # Add break-even point marker
            fig_breakeven.add_scatter(
                x=[base_year + break_even_year],
                y=[break_even_price],
                mode='markers',
                marker=dict(size=12, symbol='star', color='yellow'),
                name='Break-even Point',
                hovertemplate=f'Break-even Year: {base_year + break_even_year}<br>Price: €{break_even_price:.2f}/L'
            )

            fig_breakeven.update_layout(
                yaxis_title='Price per Liter (€)',
                hovermode='x unified'
            )

            # Display break-even metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Years to Break-even",
                    f"{years_to_breakeven}",
                    help="Number of years until SAF becomes cost-competitive"
                )
            with col2:
                st.metric(
                    "Break-even Year",
                    f"{base_year + break_even_year}",
                    help="Calendar year when SAF becomes cost-competitive"
                )
            with col3:
                st.metric(
                    "Break-even Price",
                    f"€{break_even_price:.2f}/L",
                    help="Price point where SAF matches conventional fuel cost"
                )

            st.plotly_chart(fig_breakeven, use_container_width=True)

            # Add price trajectory explanation
            st.markdown(f"""
            **Price Convergence Analysis:**
            - SAF starts at €7.50/L and decreases by 3% annually
            - Conventional fuel starts at €2.50/L and increases by 5% annually
            - Carbon costs are included in both trajectories
            - Break-even occurs in {base_year + break_even_year} at €{break_even_price:.2f}/L
            - Factors accelerating break-even:
                - Higher carbon prices
                - Faster SAF price reduction
                - Slower conventional fuel price increase
            """)

        except StopIteration:
            st.warning("""
            **No Break-even Point Found:**
            Even with a 30-year projection, SAF does not become cost-competitive under current assumptions.
            
            Factors that could change this:
            - Higher carbon prices
            - Faster SAF price reduction (currently 3% per year)
            - Faster conventional fuel price increase (currently 5% per year)
            - Government subsidies or incentives
            """)

            # Show closest approach
            min_difference_year = min(range(extended_years),
                                      key=lambda i: saf_prices[i] - conv_prices[i])
            min_difference = saf_prices[min_difference_year] - conv_prices[min_difference_year]

            st.markdown(f"""
            **Closest Approach to Break-even:**
            - Year: {base_year + min_difference_year}
            - Price gap: €{min_difference:.2f}/L
            - SAF price: €{saf_prices[min_difference_year]:.2f}/L
            - Conventional price: €{conv_prices[min_difference_year]:.2f}/L
            """)
        st.markdown("---")
        # Monte Carlo Simulation
        st.markdown("#### 🎲 Monte Carlo Simulation")

        n_simulations = 1000

        @st.cache_data
        def run_monte_carlo(n_sims, base_cost, mean_growth, std_dev):
            np.random.seed(42)  # For reproducibility
            fuel_growth_dist = np.random.normal(loc=mean_growth, scale=std_dev, size=n_sims)
            results = []
            for growth_rate in fuel_growth_dist:
                final_year_cost = base_cost * (1 + growth_rate)**projection_years
                results.append(final_year_cost)
            return results

        # Run simulation for total costs
        simulation_results = run_monte_carlo(
            n_simulations,
            total_cost,
            0.05,  # mean growth rate
            0.02   # standard deviation
        )

        # Create histogram using plotly
        fig_monte_carlo = px.histogram(
            simulation_results,
            nbins=30,
            title='Cost Distribution (Monte Carlo Simulation)',
            labels={'value': 'Total Cost (€)', 'count': 'Frequency'},
            template='plotly_dark'
        )
        st.plotly_chart(fig_monte_carlo, use_container_width=True)
        # Monte Carlo Simulation with explanation
        st.markdown("""
        **What is Monte Carlo Simulation?**
        - Simulates thousands of possible cost scenarios
        - Accounts for uncertainty in future prices
        - Shows the range of likely total costs
        - Helps understand the risk profile of different choices
        """)
        st.markdown("---")

        # Strategic Recommendations
        st.markdown("### 🚀 Strategic Recommendations")

        # Calculate some metrics for recommendations
        avg_carbon_cost = np.mean([total_carbon_cost * (1.08**i) for i in range(projection_years)])
        efficiency_gain = 0.15  # 15% better fuel efficiency for new aircraft

        st.markdown(f"""
        1. **Fuel Hedging Strategy**
           - Implement hedging for 40-60% of fuel needs based on volatility analysis
           - Consider fixed-price contracts for SAF supply
           
        2. **SAF Adoption Roadmap**
           - {"Target " + str(base_year + break_even_year) + " for price parity" if 'break_even_year' in locals() else "Continue monitoring SAF price trends"}
           - Explore partnerships with SAF producers for secure supply
           
        3. **Carbon Market Strategy**
           - Allocate approximately €{avg_carbon_cost:,.0f} for annual carbon credit purchases
           - Develop internal carbon pricing mechanism
           
        4. **Fleet Modernization**
           - Potential {efficiency_gain*100:.0f}% fuel efficiency improvement with next-generation aircraft
           - ROI analysis suggests prioritizing fleet renewal where possible
        """)

def display_carbon_price_analysis(air_emissions, rail_emissions, bus_emissions, away_team, home_team):
    """Display carbon price analysis with proper formatting"""
    st.markdown("### 💰 Carbon Price Analysis")

    # Get carbon prices
    calculator = EnhancedCarbonPricingCalculator()
    home_country = TEAM_COUNTRIES.get(home_team, 'EU')
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')
    flight_type = calculator.classify_flight(home_country, away_country)

    # Calculate EU ETS and national carbon costs
    eu_ets_cost = 0
    national_cost = 0

    # For air transport
    if flight_type in ['intra_eea', 'eea_outbound']:
        eu_ets_cost = air_emissions * calculator.EU_ETS_PRICE

    origin_tax = calculator.CARBON_PRICES.get(home_country, 0)
    if origin_tax > 0:
        national_cost = air_emissions * origin_tax

    # Total carbon cost for air
    total_air_cost = eu_ets_cost + national_cost

    # Calculate costs for rail and bus (using EU ETS price for intra-EU journeys)
    rail_cost = rail_emissions * calculator.EU_ETS_PRICE if rail_emissions else None
    bus_cost = bus_emissions * calculator.EU_ETS_PRICE if bus_emissions else None

    # Display total and breakdown
    st.markdown(f"**Total Carbon Price for Air Transport: €{total_air_cost:.2f}**")
    st.markdown("#### Carbon Price Components")

    if eu_ets_cost > 0:
        st.markdown(f"• EU ETS Cost (€{calculator.EU_ETS_PRICE}/ton): €{eu_ets_cost:.2f}")
    if national_cost > 0:
        st.markdown(f"• National Carbon Tax (€{origin_tax}/ton): €{national_cost:.2f}")

    # Detailed explanation
    st.markdown("#### Carbon Price Calculation Details")
    st.markdown(f"""
    Air transport calculation:
    - Emissions: {air_emissions:.2f} tons CO₂
    - Applicable carbon price: €{origin_tax}/ton
    - Total cost: {air_emissions:.2f} × €{origin_tax} = €{total_air_cost:.2f}
    """)

    # Carbon Price Costs Table
    st.markdown("#### Carbon Price Costs by Transport Mode")
    carbon_data = {
        "Mode": ["Air", "Rail", "Bus"],
        "Emissions (tons CO₂)": [air_emissions, rail_emissions, bus_emissions],
        "Applicable Price (€/ton)": [
            origin_tax if national_cost > 0 else calculator.EU_ETS_PRICE,
            calculator.EU_ETS_PRICE,
            calculator.EU_ETS_PRICE
        ],
        "Carbon Cost (€)": [
            total_air_cost,
            rail_cost,
            bus_cost
        ]
    }

    carbon_df = pd.DataFrame(carbon_data)
    st.markdown(carbon_df.style.format({
        "Emissions (tons CO₂)": "{:.2f}",
        "Applicable Price (€/ton)": "€{:.2f}",
        "Carbon Cost (€)": lambda x: f"€{x:,.2f}" if pd.notnull(x) else "N/A"
    }).hide().to_html(), unsafe_allow_html=True)
    # 2. Social Cost of Carbon Table
    st.markdown("#### Social Cost of Carbon")

    cost_sources = [
        ('IWG', 'iwg_75th', "Interagency Working Group 95th percentile estimate"),
        ('EPA', 'epa_median', "U.S. Environmental Protection Agency estimate"),
        ('Synthetic', 'synthetic_median', "Meta-analysis combining multiple studies"),
        ('NBER', 'nber_research', "National Bureau of Economic Research estimate")
    ]

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
    result = st.session_state.last_calculation['result']
    transport_comparison_results = display_transport_comparison(result)

    # Unpack the return values
    rail_emissions, bus_emissions, flight_salary_impact, rail_salary_impact, bus_salary_impact = transport_comparison_results

    # Pass all return values to display_results
    display_results(
        result,
        rail_emissions,
        bus_emissions,
        flight_salary_impact,
        rail_salary_impact,
        bus_salary_impact
    )
