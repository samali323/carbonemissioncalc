import pandas as pd
import logging
from typing import Optional, Dict

from src.config.constants import EU_ETS_PRICE, SOCIAL_CARBON_COSTS
from src.data.team_data import get_team_airport, get_airport_coordinates
from src.utils.route_reader import RouteViewer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_for_power_bi(matches_data: list, calculator) -> Optional[Dict]:
    """
    Export comprehensive match data for Power BI analysis
    
    Args:
        matches_data: List of match dictionaries from cleaned_matches.csv
        calculator: EmissionsCalculator instance
    
    Returns:
        Dictionary containing export status and data
    """
    try:
        logger.info(f"Starting export process for {len(matches_data)} matches")

        # Get routes data
        route_viewer = RouteViewer()
        routes_df = route_viewer.get_all_routes()

        # Create matches DataFrame and rename columns if needed
        matches_df = pd.DataFrame(matches_data)

        # Rename columns to match expected format
        column_mapping = {
            'Home Team': 'home_team',
            'Away Team': 'away_team',
            'Competition': 'competition',
            'Date': 'date'
        }
        matches_df = matches_df.rename(columns=column_mapping)

        # Initialize results list to store processed matches
        processed_matches = []

        # Process each match
        for index, match in matches_df.iterrows():
            try:
                # Get airports and coordinates
                home_airport = get_team_airport(match['home_team'])
                away_airport = get_team_airport(match['away_team'])

                if not home_airport or not away_airport:
                    logger.warning(f"Skipping match {match['home_team']} vs {match['away_team']}: Missing airport data")
                    continue

                home_coords = get_airport_coordinates(home_airport)
                away_coords = get_airport_coordinates(away_airport)

                if not home_coords or not away_coords:
                    logger.warning(f"Skipping match {match['home_team']} vs {match['away_team']}: Missing coordinates")
                    continue

                # Calculate flight emissions
                result = calculator.calculate_flight_emissions(
                    origin_lat=home_coords['lat'],
                    origin_lon=home_coords['lon'],
                    dest_lat=away_coords['lat'],
                    dest_lon=away_coords['lon'],
                    passengers=30,
                    is_round_trip=False
                )

                # Create match result dictionary
                match_result = {
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'competition': match.get('competition', ''),
                    'date': match.get('date', ''),
                    'flight_emissions_mt': result.total_emissions,
                    'emissions_per_passenger': result.per_passenger,
                    'flight_distance_km': result.distance_km,
                    'flight_type': result.flight_type,
                    'carbon_price_eu_ets': result.total_emissions * EU_ETS_PRICE,
                    'social_cost_low': result.total_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_low'],
                    'social_cost_medium': result.total_emissions * SOCIAL_CARBON_COSTS['synthetic_median'],
                    'social_cost_high': result.total_emissions * SOCIAL_CARBON_COSTS['synthetic_iqr_high']
                }

                # Add route information if available
                route_info = routes_df[
                    (routes_df['home_team'] == match['home_team']) &
                    (routes_df['away_team'] == match['away_team'])
                    ].iloc[0] if len(routes_df) > 0 else None

                if route_info is not None:
                    match_result.update({
                        'bus_distance_km': route_info.get('driving_km', 0),
                        'rail_distance_km': route_info.get('transit_km', 0),
                        'bus_time': route_info.get('driving_time', ''),
                        'rail_time': route_info.get('transit_time', '')
                    })

                processed_matches.append(match_result)

                if index % 100 == 0:
                    logger.info(f"Processed {index + 1}/{len(matches_df)} matches")

            except Exception as e:
                logger.error(f"Error processing match {match['home_team']} vs {match['away_team']}: {str(e)}")
                continue

        # Create final DataFrame
        final_df = pd.DataFrame(processed_matches)

        # Export to CSV
        output_file = 'power_bi_analysis.csv'
        final_df.to_csv(output_file, index=False)

        return {
            'status': 'success',
            'file_path': output_file,
            'rows_processed': len(final_df),
            'total_matches': len(matches_df),
            'data': final_df
        }

    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'rows_processed': 0,
            'total_matches': len(matches_data) if matches_data else 0
        }


def load_matches_from_csv(file_path: str = 'cleaned_matches.csv') -> list:
    """Load matches from cleaned_matches.csv"""
    try:
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Error loading matches from CSV: {str(e)}")
        return []


if __name__ == "__main__":
    from src.models.emissions import EmissionsCalculator

    # Initialize calculator
    calculator = EmissionsCalculator()

    # Load matches from CSV
    matches = load_matches_from_csv()

    if matches:
        # Export to Power BI format
        result = export_for_power_bi(matches, calculator)

        if result['status'] == 'success':
            print(f"Export successful!")
            print(f"Processed {result['rows_processed']} out of {result['total_matches']} matches")
            print(f"Output file: {result['file_path']}")
        else:
            print(f"Export failed: {result['error_message']}")
    else:
        print("No matches loaded from CSV")
