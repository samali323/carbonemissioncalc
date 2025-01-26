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

    # Economic Impact Analysis as a separate top-level expander
    with st.expander("💸 Economic Impact Analysis", expanded=False):
        display_economic_impacts(
            result=result,
            home_team=st.session_state.form_state['home_team'],
            away_team=st.session_state.form_state['away_team']
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


def display_economic_impacts(result, home_team, away_team):
    """Display economic impact analysis with costs summary and all optimization options."""
    calculator = EnhancedCarbonPricingCalculator()
    home_country = TEAM_COUNTRIES.get(home_team, 'EU')
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')

    # Get flight time from transport comparison
    flight_time_seconds = calculate_flight_time(
        distance_km=result.distance_km / (2 if result.is_round_trip else 1),
        is_round_trip=result.is_round_trip
    )
    flight_hours = flight_time_seconds / 3600

    # Get alternative transport emissions
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

    # Calculate fuel costs (assuming €2.5/L for jet fuel and €7.5/L for SAF)
    FUEL_PRICE_PER_L = 2.5
    SAF_PRICE_PER_L = 7.5
    conventional_fuel_volume = result.fuel_consumption * 0.98
    saf_fuel_volume = result.fuel_consumption * 0.02
    conventional_fuel_cost = conventional_fuel_volume * FUEL_PRICE_PER_L
    saf_fuel_cost = saf_fuel_volume * SAF_PRICE_PER_L
    total_fuel_cost = conventional_fuel_cost + saf_fuel_cost

    # Calculate carbon costs
    eu_ets_cost = result.total_emissions * calculator.EU_ETS_PRICE
    national_carbon_tax = result.total_emissions * calculator.CARBON_PRICES.get(home_country, 0)
    total_carbon_cost = eu_ets_cost + national_carbon_tax

    # Calculate social costs
    social_costs = {
        'iwg': result.total_emissions * SOCIAL_CARBON_COSTS['iwg_75th'],
        'epa': result.total_emissions * SOCIAL_CARBON_COSTS['epa_median'],
        'synthetic': result.total_emissions * SOCIAL_CARBON_COSTS['synthetic_median'],
        'nber': result.total_emissions * SOCIAL_CARBON_COSTS['nber_research']
    }
    avg_social_cost = sum(social_costs.values()) / len(social_costs)

    # Calculate operational costs
    operational_costs = {
        'base_charter': flight_hours * 32500,  # Base charter rate per hour
        'landing_fees': 10000,
        'catering': 3500,
        'ground_transport': 2250,
    }

    if result.is_round_trip:
        operational_costs = {k: v * 2 for k, v in operational_costs.items()}
        total_fuel_cost *= 2
        total_carbon_cost *= 2

    # Calculate total costs
    total_charter = sum(operational_costs.values())
    total_operational = total_charter + total_fuel_cost
    total_environmental = total_carbon_cost + avg_social_cost
    total_cost = total_operational + total_environmental

    # Calculate alternative costs and savings
    alternatives = {
        'empty_leg': {
            'operational': total_operational * 0.25,
            'carbon': total_carbon_cost,
            'social': avg_social_cost
        },
        'regional_airport': {
            'operational': total_operational - (operational_costs['landing_fees'] * 0.3),
            'carbon': total_carbon_cost,
            'social': avg_social_cost
        },
        'bulk_rate': {
            'operational': total_operational * 0.85,
            'carbon': total_carbon_cost,
            'social': avg_social_cost
        },
        'split_charter': {
            'operational': total_operational * 1.1,
            'carbon': total_carbon_cost * 1.2,
            'social': avg_social_cost * 1.2
        }
    }

    # Add rail and bus alternatives if available
    if rail_emissions:
        alternatives['rail'] = {
            'operational': total_operational * 0.3,  # Estimated rail operational cost
            'carbon': rail_emissions * calculator.EU_ETS_PRICE,
            'social': rail_emissions * (sum(SOCIAL_CARBON_COSTS.values()) / len(SOCIAL_CARBON_COSTS))
        }

    if bus_emissions:
        alternatives['bus'] = {
            'operational': total_operational * 0.2,  # Estimated bus operational cost
            'carbon': bus_emissions * calculator.EU_ETS_PRICE,
            'social': bus_emissions * (sum(SOCIAL_CARBON_COSTS.values()) / len(SOCIAL_CARBON_COSTS))
        }

    # Store all cost components for use in tabs
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
    summary_tab, ops_tab, carbon_tab, opt_tab = st.tabs(["Summary", "Operational Costs", "Carbon Costs", "Cost Optimization"])

    with summary_tab:
        st.markdown("### Economic Impact Summary")

        # Create summary table
        summary_data = {
            "Cost Category": ["Operational Costs", "Environmental Impact", "Total Cost"],
            "Amount (€)": [
                f"{total_operational:,.2f}",
                f"{total_environmental:,.2f}",
                f"{total_cost:,.2f}"
            ]
        }
        st.table(pd.DataFrame(summary_data))

        # Show potential savings
        st.markdown("### Potential Cost Savings")

        savings_data = []
        for option, costs in alternatives.items():
            total_alt_cost = costs['operational'] + costs['carbon'] + costs['social']
            savings = total_cost - total_alt_cost
            savings_percent = (savings / total_cost) * 100

            savings_data.append({
                "Option": option.replace('_', ' ').title(),
                "Total Cost (€)": f"{total_alt_cost:,.2f}",
                "Savings (€)": f"{savings:,.2f}",
                "Savings (%)": f"{savings_percent:,.1f}%"
            })

        st.table(pd.DataFrame(savings_data))

        # Display recommendations
        st.markdown("### Recommendations")
        best_option = max(alternatives.items(),
                          key=lambda x: total_cost - (x[1]['operational'] + x[1]['carbon'] + x[1]['social']))
        st.write(f"**Most Cost-Effective Option:** {best_option[0].replace('_', ' ').title()}")

        # Show environmental impact reduction
        st.markdown("### Environmental Impact Reduction")
        if rail_emissions and bus_emissions:
            env_data = {
                "Transport Mode": ["Air", "Rail", "Bus"],
                "CO₂ Emissions (tons)": [
                    f"{result.total_emissions:,.2f}",
                    f"{rail_emissions:,.2f}",
                    f"{bus_emissions:,.2f}"
                ],
                "Reduction (%)": [
                    "0%",
                    f"{((result.total_emissions - rail_emissions) / result.total_emissions * 100):,.1f}%",
                    f"{((result.total_emissions - bus_emissions) / result.total_emissions * 100):,.1f}%"
                ]
            }
            st.table(pd.DataFrame(env_data))

    #--------------------------------------------------------------------------------------------------------------------------------------------

    with ops_tab:
        # Create two columns for the layout
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Base Charter Costs")
            st.write(f"Flight Duration: {flight_hours:.1f} hours")
            st.write(f"Charter Rate: €32,500/hour")
            st.write(f"Base Charter Cost: €{operational_costs['base_charter']:,.2f}")
            st.write(f"Landing Fees: €{operational_costs['landing_fees']:,.2f}")
            st.write(f"Catering: €{operational_costs['catering']:,.2f}")
            st.write(f"Ground Transport: €{operational_costs['ground_transport']:,.2f}")

        with col2:
            st.markdown("#### Fuel Breakdown")
            st.write("Conventional Jet A-1 (98%)")
            st.write(f"Volume: {cost_data['fuel']['conventional']['volume']:.0f}L")
            st.write(f"Cost: €{cost_data['fuel']['conventional']['cost']:,.2f}")
            st.write("SAF (2%)")
            st.write(f"Volume: {cost_data['fuel']['saf']['volume']:.0f}L")
            st.write(f"Cost: €{cost_data['fuel']['saf']['cost']:,.2f}")

        # Total costs section
        st.markdown("---")
        st.markdown("#### Total Operational Costs")
        st.write(f"Charter Costs: €{total_charter:,.2f}")
        st.write(f"Fuel Costs: €{cost_data['fuel']['total']:,.2f}")
        st.markdown(f"**Total: €{cost_data['totals']['operational']:,.2f}**")

    with carbon_tab:
        st.markdown("### Carbon Price Analysis")

        # Carbon Price Components
        st.markdown("#### Carbon Price Components")
        st.write(f"EU ETS Cost (€{calculator.EU_ETS_PRICE:.2f}/ton): €{cost_data['carbon']['eu_ets']:,.2f}")
        st.write(f"National Carbon Tax (€{calculator.CARBON_PRICES.get(home_country, 0):.2f}/ton): €{cost_data['carbon']['national']:,.2f}")

        # Calculation Details
        st.markdown("#### Calculation Details")
        st.write(f"Emissions: {result.total_emissions:.2f} tons CO₂")
        st.write(f"Total Carbon Cost: €{cost_data['carbon']['total']:,.2f}")

        # Social Cost of Carbon
        st.markdown("#### Social Cost of Carbon")
        st.write(f"IWG (95th percentile): €{social_costs['iwg']:,.2f}")
        st.write(f"EPA Median: €{social_costs['epa']:,.2f}")
        st.write(f"Synthetic Median: €{social_costs['synthetic']:,.2f}")
        st.write(f"NBER Research: €{social_costs['nber']:,.2f}")
        st.markdown(f"**Average Social Cost: €{avg_social_cost:,.2f}**")

        # Total Environmental Impact
        st.markdown("---")
        st.markdown("#### Total Environmental Impact Cost")
        st.write(f"Carbon Market Cost: €{cost_data['carbon']['total']:,.2f}")
        st.write(f"Social Cost: €{avg_social_cost:,.2f}")
        st.markdown(f"**Total Environmental Cost: €{cost_data['totals']['environmental']:,.2f}**")
    #--------------------------------------------------------------------------------------------------------------------------------------------
    with opt_tab:
        st.markdown("### Cost Optimization Options")

        # Empty Leg Flight
        st.markdown("#### Empty Leg Flight")
        empty_op_cost = alternatives['empty_leg']['operational']
        empty_carbon_cost = alternatives['empty_leg']['carbon']
        empty_social_cost = alternatives['empty_leg']['social']
        empty_total = empty_op_cost + empty_carbon_cost + empty_social_cost
        savings = total_cost - empty_total

        st.write(f"Operational Cost: €{empty_op_cost:,.2f}")
        st.write(f"Carbon Cost: €{empty_carbon_cost:,.2f}")
        st.write(f"Social Cost: €{empty_social_cost:,.2f}")
        st.write(f"Total Cost: €{empty_total:,.2f}")
        st.write(f"**Potential Savings: €{savings:,.2f} ({(savings/total_cost)*100:.1f}%)**")
        st.write("*75% discount on operational costs as aircraft would fly empty otherwise.*")

        st.markdown("---")

        # Regional Airport Option
        st.markdown("#### Regional Airport Option")
        regional_op_cost = alternatives['regional_airport']['operational']
        regional_carbon_cost = alternatives['regional_airport']['carbon']
        regional_social_cost = alternatives['regional_airport']['social']
        regional_total = regional_op_cost + regional_carbon_cost + regional_social_cost
        savings = total_cost - regional_total

        st.write(f"Operational Cost: €{regional_op_cost:,.2f}")
        st.write(f"Carbon Cost: €{regional_carbon_cost:,.2f}")
        st.write(f"Social Cost: €{regional_social_cost:,.2f}")
        st.write(f"Total Cost: €{regional_total:,.2f}")
        st.write(f"**Potential Savings: €{savings:,.2f} ({(savings/total_cost)*100:.1f}%)**")
        st.write("*30% reduction in landing fees using smaller airports.*")

        st.markdown("---")

        # Bulk Rate Booking
        st.markdown("#### Bulk Rate Booking")
        bulk_op_cost = alternatives['bulk_rate']['operational']
        bulk_carbon_cost = alternatives['bulk_rate']['carbon']
        bulk_social_cost = alternatives['bulk_rate']['social']
        bulk_total = bulk_op_cost + bulk_carbon_cost + bulk_social_cost
        savings = total_cost - bulk_total

        st.write(f"Operational Cost: €{bulk_op_cost:,.2f}")
        st.write(f"Carbon Cost: €{bulk_carbon_cost:,.2f}")
        st.write(f"Social Cost: €{bulk_social_cost:,.2f}")
        st.write(f"Total Cost: €{bulk_total:,.2f}")
        st.write(f"**Potential Savings: €{savings:,.2f} ({(savings/total_cost)*100:.1f}%)**")
        st.write("*15% discount through seasonal booking arrangements.*")

        st.markdown("---")

        # Alternative Transport Options
        if rail_emissions or bus_emissions:
            st.markdown("#### Alternative Transport Options")

            if rail_emissions:
                st.markdown("##### Rail Transport")
                rail_op_cost = alternatives['rail']['operational']
                rail_carbon_cost = alternatives['rail']['carbon']
                rail_social_cost = alternatives['rail']['social']
                rail_total = rail_op_cost + rail_carbon_cost + rail_social_cost
                savings = total_cost - rail_total

                st.write(f"Operational Cost: €{rail_op_cost:,.2f}")
                st.write(f"Carbon Cost: €{rail_carbon_cost:,.2f}")
                st.write(f"Social Cost: €{rail_social_cost:,.2f}")
                st.write(f"Total Cost: €{rail_total:,.2f}")
                st.write(f"**Potential Savings: €{savings:,.2f} ({(savings/total_cost)*100:.1f}%)**")
                st.write(f"*Reduces emissions by {((result.total_emissions - rail_emissions) / result.total_emissions * 100):,.1f}%*")

                st.markdown("---")

            if bus_emissions:
                st.markdown("##### Bus Transport")
                bus_op_cost = alternatives['bus']['operational']
                bus_carbon_cost = alternatives['bus']['carbon']
                bus_social_cost = alternatives['bus']['social']
                bus_total = bus_op_cost + bus_carbon_cost + bus_social_cost
                savings = total_cost - bus_total

                st.write(f"Operational Cost: €{bus_op_cost:,.2f}")
                st.write(f"Carbon Cost: €{bus_carbon_cost:,.2f}")
                st.write(f"Social Cost: €{bus_social_cost:,.2f}")
                st.write(f"Total Cost: €{bus_total:,.2f}")
                st.write(f"**Potential Savings: €{savings:,.2f} ({(savings/total_cost)*100:.1f}%)**")
                st.write(f"*Reduces emissions by {((result.total_emissions - bus_emissions) / result.total_emissions * 100):,.1f}%*")

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
    display_results(
        st.session_state.last_calculation['result']
    )
