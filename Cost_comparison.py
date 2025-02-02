import sqlite3
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class RouteAnalysis:
    home_team: str
    away_team: str
    distance_km: float
    air_time: int  # minutes
    rail_time: int  # minutes
    bus_time: int  # minutes
    air_emissions: float  # tons CO2
    rail_emissions: float  # tons CO2
    bus_emissions: float  # tons CO2
    salary_cost_air: float  # EUR
    salary_cost_rail: float  # EUR
    salary_cost_bus: float  # EUR

class ModeShiftAnalyzer:
    def __init__(self, db_path: str = 'data/routes.db', min_distance: float = 50.0):
        self.db_path = db_path
        self.min_distance = min_distance  # Minimum distance in kilometers
        self.routes_data = []
        self.salary_data = {}
        self._load_data()

    def _load_data(self):
        """Load route and salary data from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load routes, filtering by minimum distance
            routes_query = """
                SELECT 
                    home_team,
                    away_team,
                    driving_duration,
                    transit_duration,
                    driving_distance/1000.0 as driving_km,
                    transit_distance/1000.0 as transit_km,
                    competition
                FROM routes
                WHERE driving_distance/1000.0 >= ?
            """
            self.routes_df = pd.read_sql_query(routes_query, conn, params=(self.min_distance,))

            # Load salary data
            salary_query = """
                SELECT team, gross_per_minute, competition
                FROM team_salaries
            """
            self.salary_df = pd.read_sql_query(salary_query, conn)

            # Group salary by team with median per-minute rate
            self.salary_data = (
                self.salary_df.groupby('team')['gross_per_minute']
                .median()
                .to_dict()
            )

    def calculate_time_cost(self, minutes: int, team: str) -> float:
        """Calculate salary cost for time duration."""
        per_minute_rate = self.salary_data.get(team, 0)
        return minutes * per_minute_rate

    def analyze_route(self, row) -> RouteAnalysis:
        """Analyze a single route for mode shift potential."""
        # Validate row has sufficient distance
        if row['driving_km'] < self.min_distance:
            return None

        # Calculate approximate times and emissions
        air_time = 30 + (row['driving_km'] / 8)  # Approx 800 km/h + 30 min ground ops
        rail_time = row['transit_duration'] / 60 if pd.notna(row['transit_duration']) else None
        bus_time = row['driving_duration'] / 60 if pd.notna(row['driving_duration']) else None

        # Air emissions (approximate using ICAO formula)
        air_emissions = row['driving_km'] * 0.15  # ~150g CO2 per km
        rail_emissions = row['transit_km'] * 0.04 if pd.notna(row['transit_km']) else None
        bus_emissions = row['driving_km'] * 0.03 if pd.notna(row['driving_km']) else None

        # Calculate combined team salary costs
        combined_rate = (
                self.salary_data.get(row['home_team'], 0) +
                self.salary_data.get(row['away_team'], 0)
        )

        salary_cost_air = air_time * combined_rate
        salary_cost_rail = rail_time * combined_rate if rail_time else None
        salary_cost_bus = bus_time * combined_rate if bus_time else None

        return RouteAnalysis(
            home_team=row['home_team'],
            away_team=row['away_team'],
            distance_km=row['driving_km'],
            air_time=air_time,
            rail_time=rail_time,
            bus_time=bus_time,
            air_emissions=air_emissions,
            rail_emissions=rail_emissions,
            bus_emissions=bus_emissions,
            salary_cost_air=salary_cost_air,
            salary_cost_rail=salary_cost_rail,
            salary_cost_bus=salary_cost_bus
        )

    def analyze_all_routes(self) -> Dict:
        """Analyze all routes and generate summary statistics."""
        results = []
        for _, row in self.routes_df.iterrows():
            analysis = self.analyze_route(row)
            if analysis:
                results.append(analysis)

        summary = {
            'total_routes': len(results),
            'rail_viable': len([r for r in results
                                if (r.rail_time is not None and
                                    r.rail_time < r.air_time and
                                    r.salary_cost_rail is not None and
                                    r.salary_cost_rail < r.salary_cost_air)]),
            'bus_viable': len([r for r in results
                               if (r.bus_time is not None and
                                   r.bus_time < r.air_time and
                                   r.salary_cost_bus is not None and
                                   r.salary_cost_bus < r.salary_cost_air)]),
            'total_air_emissions': sum(r.air_emissions for r in results),
            'potential_rail_savings': sum(
                r.air_emissions - r.rail_emissions
                for r in results if r.rail_emissions is not None
            ),
            'potential_bus_savings': sum(
                r.air_emissions - r.bus_emissions
                for r in results if r.bus_emissions is not None
            ),
            'detailed_routes': results
        }

        return summary

    def generate_report(self):
        """Generate a detailed report of mode shift analysis."""
        summary = self.analyze_all_routes()

        print("\nMode Shift Analysis Report")
        print("=" * 80)
        print(f"Minimum Route Distance: {self.min_distance} km")
        print(f"Total Routes Analyzed: {summary['total_routes']}")
        print(f"Rail-Viable Routes: {summary['rail_viable']} "
              f"({summary['rail_viable']/summary['total_routes']*100:.1f}%)")
        print(f"Bus-Viable Routes: {summary['bus_viable']} "
              f"({summary['bus_viable']/summary['total_routes']*100:.1f}%)")
        print("\nEmissions Impact")
        print("-" * 40)
        print(f"Current Air Emissions: {summary['total_air_emissions']:.1f} tons CO2")
        print(f"Potential Rail Savings: {summary['potential_rail_savings']:.1f} tons CO2")
        print(f"Potential Bus Savings: {summary['potential_bus_savings']:.1f} tons CO2")

        # Export detailed results
        results_list = []
        for r in summary['detailed_routes']:
            data = vars(r)
            data['rail_viable'] = bool(
                r.rail_time is not None and
                r.rail_time < r.air_time and
                r.salary_cost_rail is not None and
                r.salary_cost_rail < r.salary_cost_air
            )
            data['bus_viable'] = bool(
                r.bus_time is not None and
                r.bus_time < r.air_time and
                r.salary_cost_bus is not None and
                r.salary_cost_bus < r.salary_cost_air
            )
            data['time_difference_rail'] = (r.rail_time - r.air_time) if r.rail_time is not None else None
            data['time_difference_bus'] = (r.bus_time - r.air_time) if r.bus_time is not None else None
            results_list.append(data)

        detailed_df = pd.DataFrame(results_list)
        detailed_df.to_csv('mode_shift_analysis.csv', index=False)
        print("\nDetailed analysis exported to mode_shift_analysis.csv")

if __name__ == '__main__':
    # Allow configurable minimum distance via command-line argument or default to 50 km
    import sys
    min_distance = 50.0
    if len(sys.argv) > 1:
        try:
            min_distance = float(sys.argv[1])
        except ValueError:
            print("Invalid distance. Using default 50 km.")

    analyzer = ModeShiftAnalyzer(min_distance=min_distance)
    analyzer.generate_report()
