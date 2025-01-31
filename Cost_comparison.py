import sqlite3
import pandas as pd
from src.utils.calculations import calculate_transport_emissions, calculate_flight_time
from src.data.team_data import get_team_airport, get_airport_coordinates, TEAM_COUNTRIES
from src.utils.carbon_pricing.enhanced_calculator import EnhancedCarbonPricingCalculator
from src.models.emissions import EmissionsCalculator

def get_salary_info(conn, team, competition):
    cursor = conn.cursor()
    cursor.execute("""
       SELECT gross_per_minute
       FROM team_salaries 
       WHERE team = ? AND competition = ?
       ORDER BY last_updated DESC 
       LIMIT 1
   """, (team, competition))
    result = cursor.fetchone()
    return result[0] if result else 0

def analyze_transport_costs(db_path='data/routes.db'):
    conn = sqlite3.connect(db_path)
    calculator = EmissionsCalculator()
    carbon_calc = EnhancedCarbonPricingCalculator()

    savings_found = []
    time_savings_found = []

    # Get routes with competition data
    cursor = conn.cursor()
    cursor.execute("""
       SELECT r.home_team, r.away_team, m.Competition,
              r.driving_duration, r.transit_duration,
              r.driving_distance/1000.0 as driving_km,
              r.transit_distance/1000.0 as transit_km
       FROM routes r
       JOIN matches m ON r.home_team = m."Home Team" 
                     AND r.away_team = m."Away Team"
   """)
    routes = cursor.fetchall()

    print("Analyzing transport costs and times for all routes...")
    print("-" * 80)

    for route in routes:
        home_team = route[0]
        away_team = route[1]
        competition = route[2]
        driving_duration = route[3]
        transit_duration = route[4]
        driving_km = route[5]
        transit_km = route[6]

        # Get airports and coordinates
        home_airport = get_team_airport(home_team)
        away_airport = get_team_airport(away_team)

        if not home_airport or not away_airport:
            continue

        home_coords = get_airport_coordinates(home_airport)
        away_coords = get_airport_coordinates(away_airport)

        if not home_coords or not away_coords:
            continue

        # Calculate base flight costs
        result = calculator.calculate_flight_emissions(
            home_coords['lat'], home_coords['lon'],
            away_coords['lat'], away_coords['lon'],
            passengers=30,
            is_round_trip=False
        )

        # Calculate travel times
        flight_time = calculate_flight_time(result.distance_km) # in seconds

        # Calculate time differences
        rail_time_saved = (flight_time - transit_duration) / 3600 if transit_duration else None
        bus_time_saved = (flight_time - driving_duration) / 3600 if driving_duration else None

        # Get salary costs per minute
        salary_per_minute = get_salary_info(conn, home_team, competition)

        # Calculate salary impacts
        flight_salary = (flight_time / 60) * salary_per_minute * 30  # 30 players
        rail_salary = (transit_duration / 60) * salary_per_minute * 30 if transit_duration else None
        bus_salary = (driving_duration / 60) * salary_per_minute * 30 if driving_duration else None

        # Calculate alternative transport emissions
        rail_emissions = calculate_transport_emissions('rail', transit_km, 30, False)
        bus_emissions = calculate_transport_emissions('bus', driving_km, 30, False)

        # Operational costs
        flight_operational = 25000 * (result.distance_km/800)  # €25k per hour at 800km/h
        rail_operational = flight_operational * 0.3  # 30% of flight cost
        bus_operational = flight_operational * 0.2  # 20% of flight cost

        # Carbon costs
        carbon_price = carbon_calc.EU_ETS_PRICE
        flight_carbon = result.total_emissions * carbon_price
        rail_carbon = rail_emissions * carbon_price if rail_emissions else 0
        bus_carbon = bus_emissions * carbon_price if bus_emissions else 0

        # Total costs including salary impact
        flight_total = flight_operational + flight_carbon + flight_salary
        rail_total = rail_operational + rail_carbon + rail_salary if rail_salary else float('inf')
        bus_total = bus_operational + bus_carbon + bus_salary if bus_salary else float('inf')

        # Check for cost or time savings
        if (rail_total < flight_total or bus_total < flight_total or
                (rail_time_saved and rail_time_saved > 0) or
                (bus_time_saved and bus_time_saved > 0)):

            savings_found.append({
                'route': f"{home_team} vs {away_team}",
                'competition': competition,
                'distance_km': result.distance_km,
                'flight_cost': {
                    'operational': flight_operational,
                    'carbon': flight_carbon,
                    'salary': flight_salary,
                    'total': flight_total
                },
                'rail_cost': {
                    'operational': rail_operational,
                    'carbon': rail_carbon,
                    'salary': rail_salary,
                    'total': rail_total
                },
                'bus_cost': {
                    'operational': bus_operational,
                    'carbon': bus_carbon,
                    'salary': bus_salary,
                    'total': bus_total
                },
                'rail_savings': flight_total - rail_total if rail_total < flight_total else 0,
                'bus_savings': flight_total - bus_total if bus_total < flight_total else 0,
                'time_savings': {
                    'flight_time': flight_time / 3600,  # Convert to hours
                    'rail_time': transit_duration / 3600 if transit_duration else None,
                    'bus_time': driving_duration / 3600 if driving_duration else None,
                    'rail_time_saved': rail_time_saved,
                    'bus_time_saved': bus_time_saved
                }
            })

    if savings_found:
        print(f"\nFound {len(savings_found)} routes with potential savings or time benefits:\n")
        for route in savings_found:
            print(f"Route: {route['route']}")
            print(f"Competition: {route['competition']}")
            print(f"Distance: {route['distance_km']:.1f} km")

            print("\nTravel Times:")
            times = route['time_savings']
            print(f"  Flight: {times['flight_time']:.1f} hours")

            if times['rail_time']:
                time_diff = times['rail_time_saved']
                print(f"  Rail: {times['rail_time']:.1f} hours")
                print(f"  Time Impact: {abs(time_diff):.1f} hours {'saved' if time_diff > 0 else 'longer'}")

            if times['bus_time']:
                time_diff = times['bus_time_saved']
                print(f"  Bus: {times['bus_time']:.1f} hours")
                print(f"  Time Impact: {abs(time_diff):.1f} hours {'saved' if time_diff > 0 else 'longer'}")

            print("\nFlight Costs:")
            print(f"  Operational: €{route['flight_cost']['operational']:,.2f}")
            print(f"  Carbon: €{route['flight_cost']['carbon']:,.2f}")
            print(f"  Salary Impact: €{route['flight_cost']['salary']:,.2f}")
            print(f"  Total: €{route['flight_cost']['total']:,.2f}")

            if route['rail_savings'] > 0:
                print("\nRail Costs:")
                print(f"  Operational: €{route['rail_cost']['operational']:,.2f}")
                print(f"  Carbon: €{route['rail_cost']['carbon']:,.2f}")
                print(f"  Salary Impact: €{route['rail_cost']['salary']:,.2f}")
                print(f"  Total: €{route['rail_cost']['total']:,.2f}")
                print(f"  Potential Savings: €{route['rail_savings']:,.2f}")

            if route['bus_savings'] > 0:
                print("\nBus Costs:")
                print(f"  Operational: €{route['bus_cost']['operational']:,.2f}")
                print(f"  Carbon: €{route['bus_cost']['carbon']:,.2f}")
                print(f"  Salary Impact: €{route['bus_cost']['salary']:,.2f}")
                print(f"  Total: €{route['bus_cost']['total']:,.2f}")
                print(f"  Potential Savings: €{route['bus_savings']:,.2f}")

            print("-" * 80)

        # Summary statistics
        print("\nSummary Statistics:")
        print(f"Total Routes Analyzed: {len(routes)}")
        print(f"Routes with Cost/Time Benefits: {len(savings_found)}")

        total_rail_savings = sum(route['rail_savings'] for route in savings_found)
        total_bus_savings = sum(route['bus_savings'] for route in savings_found)

        print(f"Total Potential Rail Cost Savings: €{total_rail_savings:,.2f}")
        print(f"Total Potential Bus Cost Savings: €{total_bus_savings:,.2f}")

        rail_time_savings = [r['time_savings']['rail_time_saved'] for r in savings_found
                             if r['time_savings']['rail_time_saved'] and r['time_savings']['rail_time_saved'] > 0]
        bus_time_savings = [r['time_savings']['bus_time_saved'] for r in savings_found
                            if r['time_savings']['bus_time_saved'] and r['time_savings']['bus_time_saved'] > 0]

        if rail_time_savings:
            print(f"Routes with Rail Time Savings: {len(rail_time_savings)}")
            print(f"Average Rail Time Saved: {sum(rail_time_savings)/len(rail_time_savings):.1f} hours")

        if bus_time_savings:
            print(f"Routes with Bus Time Savings: {len(bus_time_savings)}")
            print(f"Average Bus Time Saved: {sum(bus_time_savings)/len(bus_time_savings):.1f} hours")

    else:
        print("\nNo routes found where rail or bus transport shows cost or time benefits.")

    conn.close()

if __name__ == "__main__":
    analyze_transport_costs()
