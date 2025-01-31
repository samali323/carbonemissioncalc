import pandas as pd
import sqlite3
import os
from datetime import datetime


class SalaryDatabaseIntegrator:
    def __init__(self, db_path='data/routes.db'):
        """Initialize with path to existing routes database."""
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Add salary table to existing database if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create team_salaries table with the new 'competition' column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_salaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competition TEXT NOT NULL,  -- New column
                    team TEXT NOT NULL,
                    gross_weekly_wage DECIMAL(15,2),
                    gross_per_minute DECIMAL(15,2),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(competition, team)  -- Ensure unique combination of competition and team
                )
            """)
            conn.commit()

    def clean_currency_value(self, value: str) -> float:
        """Clean currency values by removing symbols and converting to float."""
        try:
            # Check if the value is already a number
            if isinstance(value, (int, float)):
                return float(value)

            # Convert the value to string and clean it
            cleaned_value = str(value).replace('€', '').replace(',', '').strip()

            # Handle special cases like '############'
            if cleaned_value == '############' or cleaned_value == '':
                return 0.0  # Replace invalid values with 0.0

            # Convert the cleaned string to a float
            return float(cleaned_value)
        except Exception as e:
            print(f"Error cleaning currency value '{value}': {str(e)}")
            return 0.0  # Default to 0.0 if conversion fails
    def import_salary_data(self, excel_file: str):
        """Import salary data from Excel file."""
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)

            # Clean column names
            df.columns = ['competition', 'team', 'gross_weekly_wage', 'gross_per_minute']

            # Clean currency values
            df['gross_weekly_wage'] = df['gross_weekly_wage'].apply(self.clean_currency_value)
            df['gross_per_minute'] = df['gross_per_minute'].apply(self.clean_currency_value)

            # Calculate gross_weekly_wage if it's 0.0
            df['gross_weekly_wage'] = df.apply(
                lambda row: row['gross_per_minute'] * 1800 if row['gross_weekly_wage'] == 0.0 else row['gross_weekly_wage'],
                axis=1
            )

            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                # Add current timestamp
                df['last_updated'] = datetime.now()

                # Save to team_salaries table
                df.to_sql('team_salaries', conn, if_exists='replace', index=False)
                print(f"Processed {len(df)} teams")
                return True, "Salary data imported successfully"
        except Exception as e:
            return False, f"Error importing salary data: {str(e)}"
    def get_team_salary_info(self, team: str, competition: str) -> dict:
        """Get salary information for a specific team and competition."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        gross_weekly_wage,
                        gross_per_minute
                    FROM team_salaries
                    WHERE team = ? AND competition = ?
                """, (team, competition))
                result = cursor.fetchone()
                if result:
                    return {
                        'weekly_wage': result[0],
                        'per_minute': result[1]
                    }
                return None
        except Exception as e:
            print(f"Error getting team salary info: {str(e)}")
            return None

    def calculate_travel_cost(self,
                              team: str,
                              competition: str,
                              travel_time_minutes: float,
                              operational_cost: float) -> dict:
        """Calculate total travel cost including salary costs."""
        team_info = self.get_team_salary_info(team, competition)
        if not team_info:
            return None
        wage_cost = travel_time_minutes * team_info['per_minute']
        total_cost = wage_cost + operational_cost
        return {
            'operational_cost': operational_cost,
            'wage_cost': wage_cost,
            'total_cost': total_cost,
            'travel_time_minutes': travel_time_minutes,
            'per_minute_rate': team_info['per_minute']
        }

    def print_database_summary(self):
        """Print summary of salary data in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_teams,
                        AVG(gross_weekly_wage) as avg_weekly,
                        AVG(gross_per_minute) as avg_minute,
                        MAX(gross_weekly_wage) as max_weekly,
                        MIN(gross_weekly_wage) as min_weekly
                    FROM team_salaries
                """)
                result = cursor.fetchone()
                if result:
                    print("\nDatabase Summary:")
                    print(f"Total teams: {result[0]}")
                    print(f"Average weekly wage: €{result[1]:,.2f}")
                    print(f"Average per minute: €{result[2]:,.2f}")
                    print(f"Highest weekly wage: €{result[3]:,.2f}")
                    print(f"Lowest weekly wage: €{result[4]:,.2f}")
        except Exception as e:
            print(f"Error getting database summary: {str(e)}")


def main():
    # Initialize integrator
    integrator = SalaryDatabaseIntegrator()

    # Import salary data
    success, message = integrator.import_salary_data('Player_Salaries.xlsx')
    print(message)

    if success:
        # Print database summary
        integrator.print_database_summary()

        # Test with a sample team and competition
        test_team = "AC Milan"
        test_competition = "Serie A"
        team_info = integrator.get_team_salary_info(test_team, test_competition)
        if team_info:
            print(f"\nTest Team ({test_team}, {test_competition}) Information:")
            print(f"Weekly wage: €{team_info['weekly_wage']:,.2f}")
            print(f"Per minute rate: €{team_info['per_minute']:,.2f}")

            # Calculate sample travel cost
            travel_cost = integrator.calculate_travel_cost(
                test_team,
                test_competition,
                travel_time_minutes=180,  # 3 hours
                operational_cost=5000
            )
            if travel_cost:
                print("\nSample Travel Cost Analysis:")
                print(f"Operational Cost: €{travel_cost['operational_cost']:,.2f}")
                print(f"Wage Cost: €{travel_cost['wage_cost']:,.2f}")
                print(f"Total Cost: €{travel_cost['total_cost']:,.2f}")


if __name__ == "__main__":
    main()
