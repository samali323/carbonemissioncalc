# First: Imports
import os
import sqlite3
from tkinter import messagebox

import streamlit as st
from PIL._tkinter_finder import tk

from src.config.constants import SOCIAL_CARBON_COSTS
from src.models.emissions import EmissionsCalculator, EmissionsResult
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time, format_time_duration, calculate_transit_time, calculate_driving_time, determine_mileage_type,
    calculate_distance, get_carbon_price
)
import pandas as pd

# Second: Initialize calculator
calculator = EmissionsCalculator()

# Third: Set page config
st.set_page_config(
    page_title="Football Team Flight Emissions Calculator",
    page_icon="✈️",
    layout="wide"
)


# Fourth: Define all functions
def display_results(result, home_airport, away_airport):
    """Display calculation results"""
    st.markdown("---")
    st.markdown("## Results")

    # Flight Details
    st.markdown("### ✈️ Flight Details")
    st.markdown("----------------------------------------")
    st.markdown(f"🏠 **Home Team:** {st.session_state.form_state['home_team']} ({home_airport})")
    st.markdown(f"🏃 **Away Team:** {st.session_state.form_state['away_team']} ({away_airport})")
    st.markdown(f"📏 **Distance:** {result.distance_km:,.1f} km")
    st.markdown(f"✈️ **Flight Type:** {result.flight_type}")
    st.markdown(f"🔄 **Round Trip:** {'Yes ✔️' if st.session_state.form_state['is_round_trip'] else 'No ❌'}")

    # Emissions Results
    st.markdown("### 🌡️ Emissions Results")
    st.markdown("----------------------------------------")
    st.markdown(f"🌍 **Total CO₂:** {result.total_emissions:,.2f} metric tons")
    st.markdown(f"🤝 **Per Passenger:** {result.per_passenger:,.2f} metric tons")

    # Environmental Impact
    impact = calculate_equivalencies(result.total_emissions)
    display_environmental_impact(impact)

    # Transport Mode Comparison
    display_transport_comparison(result)

    # Calculate emissions for different modes
    rail_emissions = calculate_transport_emissions(
        'rail',
        result.distance_km,
        st.session_state.form_state['passengers'],
        st.session_state.form_state['is_round_trip'],
        st.session_state.form_state['home_team'],
        st.session_state.form_state['away_team']
    )

    bus_emissions = calculate_transport_emissions(
        'bus',
        result.distance_km,
        st.session_state.form_state['passengers'],
        st.session_state.form_state['is_round_trip'],
        st.session_state.form_state['home_team'],
        st.session_state.form_state['away_team']
    )

    # Display Carbon Price and Social Cost Analysis
    display_carbon_price_analysis(
        air_emissions=result.total_emissions,
        rail_emissions=rail_emissions,
        bus_emissions=bus_emissions,
        away_team=st.session_state.form_state['away_team'],
        home_team=st.session_state.form_state['home_team']
    )


def display_environmental_impact(impact):
    """Display environmental impact equivalencies"""
    st.markdown("### 🌍 Environmental Impact Equivalencies")
    st.markdown("----------------------------------------")

    # Transportation Impact
    st.markdown("🚗 **Transportation Impact**")
    st.markdown("------------------------------")
    st.markdown(f"  • {impact['gasoline_vehicles_year']:.2f} Gasoline vehicles driven for one year")
    st.markdown(f"  • {impact['electric_vehicles_year']:.2f} Electric vehicles driven for one year")
    st.markdown(f"  • {impact['gasoline_vehicle_miles']:.2f} Miles driven by gasoline vehicle")

    # Energy Usage
    st.markdown("⚡ **Energy Usage**")
    st.markdown("------------------------------")
    st.markdown(f"  • {impact['homes_energy_year']:.2f} Homes' energy use for one year")
    st.markdown(f"  • {impact['homes_electricity_year']:.2f} Homes' electricity use for one year")
    st.markdown(f"  • {impact['smartphones_charged']:.2f} Smartphones charged")

    # Environmental Offset
    st.markdown("🌳 **Environmental Offset**")
    st.markdown("------------------------------")
    st.markdown(f"  • {impact['tree_seedlings_10years']:.2f} Tree seedlings grown for 10 years")
    st.markdown(f"  • {impact['forest_acres_year']:.2f} Acres of U.S. forests in one year")
    st.markdown(f"  • {impact['forest_preserved_acres']:.2f} Acres of U.S. forests preserved")


def display_transport_comparison(result):
    """Display transport mode comparison"""
    st.markdown("### 🚊 Transport Mode Comparison")
    st.markdown("=" * 90)

    # Calculate flight time
    flight_time_seconds = calculate_flight_time(
        distance_km=result.distance_km / (2 if result.is_round_trip else 1),
        is_round_trip=result.is_round_trip
    )
    flight_time_str = format_time_duration(flight_time_seconds)

    try:
        conn = sqlite3.connect('data/routes.db')
        cursor = conn.cursor()

        # Query to get rail and bus data for the current match
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
                result.is_round_trip,
                st.session_state.form_state['home_team'],
                st.session_state.form_state['away_team']
            )

            driving_time_str = "N/A"
            driving_distance = result.distance_km
            bus_emissions = calculate_transport_emissions(
                'bus',
                result.distance_km,
                st.session_state.form_state['passengers'],
                result.is_round_trip,
                st.session_state.form_state['home_team'],
                st.session_state.form_state['away_team']
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

    # Get carbon price based on away team's country
    carbon_price = get_carbon_price(
        st.session_state.form_state['away_team'],
        st.session_state.form_state['home_team']
    )

    # Create comparison table
    comparison_data = pd.DataFrame({
        'Mode': ['Air', 'Rail', 'Bus'],
        'Est. Travel Time': [
            flight_time_str,
            transit_time_str,
            driving_time_str
        ],
        'Distance (km)': [
            result.distance_km,
            transit_distance,
            driving_distance
        ],
        'CO₂ (tons)': [
            result.total_emissions,
            rail_emissions,
            bus_emissions
        ],
        'CO₂ Saved (tons)': [
            0,
            result.total_emissions - rail_emissions,
            result.total_emissions - bus_emissions
        ]
    })

    st.table(comparison_data.round(2))


def display_carbon_price_analysis(air_emissions, rail_emissions, bus_emissions, away_team, home_team):
    """Display carbon price analysis"""
    st.markdown("### 💰 Carbon Price Analysis")
    st.markdown("=" * 90)

    # Get carbon price based on away team's country
    carbon_price = get_carbon_price(away_team, home_team)
    away_country = TEAM_COUNTRIES.get(away_team, 'EU')

    st.markdown(f"Carbon Price Analysis ({away_country}):")
    st.markdown(f"Carbon Price: €{carbon_price:.2f}/tCO₂")

    # Create carbon costs table
    carbon_costs_data = pd.DataFrame({
        'Mode': ['Air', 'Rail', 'Bus'],
        'Carbon Cost (€)': [
            air_emissions * carbon_price,
            rail_emissions * carbon_price,
            bus_emissions * carbon_price
        ]
    })

    st.table(carbon_costs_data.round(2))

    # Display social cost analysis using constants from SOCIAL_CARBON_COSTS
    st.markdown("\nSocial Cost Analysis:")
    st.markdown("=" * 90)

    # Create social costs table
    social_cost_data = []
    modes = [('Air', air_emissions), ('Rail', rail_emissions), ('Bus', bus_emissions)]

    for mode, emissions in modes:
        social_cost_data.extend([
            [mode, 'Synthetic',
             f"€ {emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low']:.0f}",
             f"€ {emissions * SOCIAL_CARBON_COSTS['synthetic_median']:.0f}",
             f"€ {emissions * SOCIAL_CARBON_COSTS['synthetic_mean']:.0f}",
             f"€ {emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']:.0f}"],
            ['', 'EPA', '', f"€ {emissions * SOCIAL_CARBON_COSTS['epa_median']:.0f}", '', ''],
            ['', 'IWG', '', f"€ {emissions * SOCIAL_CARBON_COSTS['iwg_75th']:.0f}", '', '']
        ])

    social_costs_df = pd.DataFrame(
        social_cost_data,
        columns=['Mode', 'Cost Type', 'Low', 'Median', 'Mean', 'High']
    )

    st.table(social_costs_df)


def calculate_and_display_results(home_team, away_team, passengers, is_round_trip):
    """Calculate and display emissions results"""

    try:

        # Initialize calculator

        calculator = EmissionsCalculator()

        # Get airports and coordinates

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

        # Calculate distance

        distance = calculate_distance(

            home_coords['lat'],

            home_coords['lon'],

            away_coords['lat'],

            away_coords['lon']

        )

        # Calculate emissions using ICAO calculator

        result_dict = calculator.icao_calculator.calculate_emissions(

            distance_km=distance,

            aircraft_type="A320",

            cabin_class="business",

            passengers=passengers,

            cargo_tons=2.0,

            is_international=True

        )

        # Adjust for round trip if needed

        if is_round_trip:
            result_dict["emissions_total_kg"] *= 2

            result_dict["emissions_per_pax_kg"] *= 2

            distance *= 2

        # Create result object

        result = EmissionsResult(

            total_emissions=result_dict['emissions_total_kg'] / 1000,

            per_passenger=result_dict['emissions_per_pax_kg'] / 1000,

            distance_km=distance,

            corrected_distance_km=result_dict['corrected_distance_km'],

            fuel_consumption=result_dict['fuel_consumption_kg'],

            flight_type=determine_mileage_type(distance),

            is_round_trip=is_round_trip,

            additional_data=result_dict['factors_applied']

        )

        # Display transport comparison

        display_transport_comparison(result, home_team, away_team, passengers, is_round_trip)

        return result



    except Exception as e:

        st.error(f"Error in calculation: {str(e)}")

        return None


def calculate_and_display():
    """Calculate and display emissions results"""
    try:
        # Get airports and coordinates
        home_airport = get_team_airport(st.session_state.form_state['home_team'])
        away_airport = get_team_airport(st.session_state.form_state['away_team'])

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

        # Store calculation in session state
        st.session_state.last_calculation = {
            'result': result,  # Make sure this is stored
            'home_airport': home_airport,
            'away_airport': away_airport
        }

    except Exception as e:
        st.error(f"Error calculating emissions: {str(e)}")


# Fifth: Rest of  code
# Title and description
st.title("⚽ Football Team Flight Emissions Calculator")
st.write("Calculate carbon emissions for football team travel")

# Initialize session state if not exists
if 'form_state' not in st.session_state:
    st.session_state.form_state = {
        'home_team': get_all_teams()[0],
        'away_team': get_all_teams()[0],
        'passengers': 30,
        'is_round_trip': False
    }

# Check for match selection from analysis page
if 'calculator_input' in st.session_state:
    st.session_state.form_state.update(st.session_state.calculator_input)
    del st.session_state['calculator_input']

# Input section
st.markdown("### Input Details")

# Team selection using session state
all_teams = get_all_teams()
home_team = st.selectbox(
    "Home Team",
    options=all_teams,
    index=all_teams.index(st.session_state.form_state['home_team']),
    key='home_team',
    on_change=lambda: st.session_state.form_state.update({'home_team': st.session_state.home_team})
)

away_team = st.selectbox(
    "Away Team",
    options=all_teams,
    index=all_teams.index(st.session_state.form_state['away_team']),
    key='away_team',
    on_change=lambda: st.session_state.form_state.update({'away_team': st.session_state.away_team})
)

passengers = st.number_input(
    "Number of Passengers",
    min_value=1,
    value=st.session_state.form_state['passengers'],
    key='passengers',
    on_change=lambda: st.session_state.form_state.update({'passengers': st.session_state.passengers})
)

# Round trip checkbox with auto-calculation
is_round_trip = st.checkbox(
    "Round Trip",
    value=st.session_state.form_state['is_round_trip'],
    key='round_trip_checkbox',
    on_change=lambda: (
        st.session_state.form_state.update({'is_round_trip': st.session_state.round_trip_checkbox}),
        calculate_and_display() if 'last_calculation' in st.session_state else None
    )
)

# Calculate button
calculate_clicked = st.button(
    "Calculate Emissions",
    key='calculate_emissions_button'
)

if calculate_clicked:
    calculate_and_display()

# Display results if they exist in session state
if 'last_calculation' in st.session_state:
    display_results(
        st.session_state.last_calculation['result'],
        st.session_state.last_calculation['home_airport'],
        st.session_state.last_calculation['away_airport']
    )

# Add helpful information in sidebar
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
