import pandas as pd

from src.config.constants import EU_ETS_PRICE, SOCIAL_CARBON_COSTS
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.route_reader import RouteViewer


def export_for_power_bi(matches_data, calculator):
    """
    Export comprehensive match data for Power BI analysis

    Args:
        matches_data: List of match dictionaries
        calculator: EmissionsCalculator instance

    Returns:
        DataFrame ready for Power BI import
    """
    try:
        # Get routes data
        route_viewer = RouteViewer()
        routes_df = route_viewer.get_all_routes()

        # Create matches DataFrame
        matches_df = pd.DataFrame(matches_data)

        # Merge matches and routes data
        combined_df = pd.merge(
            matches_df,
            routes_df,
            on=['home_team', 'away_team'],
            how='left'
        )

        # Calculate emissions and analysis for each match
        for index, row in combined_df.iterrows():
            # Get airports and coordinates
            home_airport = get_team_airport(row['home_team'])
            away_airport = get_team_airport(row['away_team'])
            home_coords = get_airport_coordinates(home_airport)
            away_coords = get_airport_coordinates(away_airport)

            # Calculate flight emissions
            result = calculator.calculate_flight_emissions(
                origin_lat=home_coords['lat'],
                origin_lon=home_coords['lon'],
                dest_lat=away_coords['lat'],
                dest_lon=away_coords['lon'],
                passengers=30,
                is_round_trip=False
            )

            # Add emissions data
            combined_df.at[index, 'flight_emissions_mt'] = result.total_emissions
            combined_df.at[index, 'emissions_per_passenger'] = result.per_passenger
            combined_df.at[index, 'flight_distance_km'] = result.distance_km
            combined_df.at[index, 'flight_type'] = result.flight_type

            # Add carbon pricing
            combined_df.at[index, 'carbon_price_eu_ets'] = result.total_emissions * EU_ETS_PRICE

            # Add social costs
            emissions_tons = result.total_emissions
            combined_df.at[index, 'social_cost_low'] = emissions_tons * SOCIAL_CARBON_COSTS['synthetic_iqr_low']
            combined_df.at[index, 'social_cost_medium'] = emissions_tons * SOCIAL_CARBON_COSTS['synthetic_median']
            combined_df.at[index, 'social_cost_high'] = emissions_tons * SOCIAL_CARBON_COSTS['synthetic_iqr_high']

        # Rename columns for clarity
        combined_df = combined_df.rename(columns={
            'driving_km': 'bus_distance_km',
            'transit_km': 'rail_distance_km',
            'driving_time': 'bus_time',
            'transit_time': 'rail_time'
        })

        # Export to CSV
        output_file = 'power_bi_analysis.csv'
        combined_df.to_csv(output_file, index=False)
        print(f"Data exported successfully to {output_file}")

        return combined_df

    except Exception as e:
        print(f"Error exporting data: {str(e)}")
        return None
