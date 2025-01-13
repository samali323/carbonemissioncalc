import streamlit as st
from src.models.emissions import EmissionsCalculator
from src.data.team_data import get_all_teams, get_team_airport, get_airport_coordinates
from src.utils.calculations import (
    calculate_transport_emissions,
    calculate_equivalencies,
    calculate_flight_time
)
import pandas as pd

# Initialize calculator
calculator = EmissionsCalculator()

# Set page config
st.set_page_config(
    page_title="Football Team Flight Emissions Calculator",
    page_icon="✈️",
    layout="wide"
)

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

is_round_trip = st.checkbox(
    "Round Trip",
    value=st.session_state.form_state['is_round_trip'],
    key='round_trip',
    on_change=lambda: st.session_state.form_state.update({'is_round_trip': st.session_state.round_trip})
)


# Calculate button
calculate_clicked = st.button("Calculate Emissions")

# Determine if we should calculate
should_calculate = calculate_clicked

# Determine if we should calculate
should_calculate = calculate_clicked

if should_calculate:
    try:
        # Get airports and coordinates
        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            st.error("Airport not found for one or both teams")
        else:
            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            if not home_coords or not away_coords:
                st.error("Coordinates not found for one or both airports")
            else:
                # Calculate emissions
                result = calculator.calculate_flight_emissions(
                    origin_lat=home_coords['lat'],
                    origin_lon=home_coords['lon'],
                    dest_lat=away_coords['lat'],
                    dest_lon=away_coords['lon'],
                    passengers=passengers,
                    is_round_trip=is_round_trip
                )

                # Display Results
                st.markdown("---")
                st.markdown("## Results")

                # Flight Details
                st.markdown("### 🛫 Flight Details")
                st.markdown("----------------------------------------")
                st.markdown(f"🏠 **Home Team:** {home_team} ({home_airport})")
                st.markdown(f"🏃 **Away Team:** {away_team} ({away_airport})")
                st.markdown(f"📏 **Distance:** {result.distance_km:,.1f} km")
                st.markdown(f"✈️ **Flight Type:** {result.flight_type}")
                st.markdown(f"🔄 **Round Trip:** {'Yes ↔️' if is_round_trip else 'No →'}")

                # Emissions Results
                st.markdown("### 🌡️ Emissions Results")
                st.markdown("----------------------------------------")
                st.markdown(f"📊 **Total CO₂:** {result.total_emissions:,.2f} metric tons")
                st.markdown(f"👤 **Per Passenger:** {result.per_passenger:,.2f} metric tons")

                # Environmental Impact
                st.markdown("### 🌍 Environmental Impact Equivalencies")
                st.markdown("----------------------------------------")
                impact = calculate_equivalencies(result.total_emissions)

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

                # Waste & Resources
                st.markdown("♻️ **Waste & Resources**")
                st.markdown("------------------------------")
                st.markdown(f"  • {impact['waste_tons_recycled']:.2f} Tons of waste recycled")
                st.markdown(f"  • {impact['garbage_trucks_recycled']:.2f} Garbage trucks of waste recycled")
                st.markdown(f"  • {impact['trash_bags_recycled']:.2f} Trash bags of waste recycled")

                # Fuel Equivalents
                st.markdown("⛽ **Fuel Equivalents**")
                st.markdown("------------------------------")
                st.markdown(f"  • {impact['gasoline_gallons']:.2f} Gallons of gasoline")
                st.markdown(f"  • {impact['diesel_gallons']:.2f} Gallons of diesel")
                st.markdown(f"  • {impact['propane_cylinders']:.2f} Propane cylinders for BBQ")
                st.markdown(f"  • {impact['oil_barrels']:.2f} Barrels of oil")

                # Transport Mode Comparison
                st.markdown("### Transport Mode Comparison")
                st.markdown("=" * 90)

                # Calculate emissions for different modes
                rail_emissions = calculate_transport_emissions('rail', result.distance_km, passengers, is_round_trip)
                bus_emissions = calculate_transport_emissions('bus', result.distance_km, passengers, is_round_trip)

                # Create comparison table
                comparison_data = pd.DataFrame({
                    'Mode': ['Air', 'Rail', 'Bus'],
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

    except Exception as e:
        st.error(f"Error calculating emissions: {str(e)}")

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
