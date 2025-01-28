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

            # Create team_salaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_salaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team TEXT UNIQUE NOT NULL,
                    gross_weekly_wage DECIMAL(15,2),
                    gross_per_minute DECIMAL(15,2),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def clean_currency_value(self, value: str) -> float:
        """Clean currency values by removing symbols and converting to float."""
        if isinstance(value, (int, float)):
            return float(value)
        return float(str(value).replace('€', '').replace(',', '').strip())

    def import_salary_data(self, excel_file: str):
        """Import salary data from Excel file."""
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)

            # Clean column names
            df.columns = ['team', 'gross_weekly_wage', 'gross_per_minute']

            # Clean currency values
            df['gross_weekly_wage'] = df['gross_weekly_wage'].apply(self.clean_currency_value)
            df['gross_per_minute'] = df['gross_per_minute'].apply(self.clean_currency_value)

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

    def get_team_salary_info(self, team: str) -> dict:
        """Get salary information for a specific team."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        gross_weekly_wage,
                        gross_per_minute
                    FROM team_salaries
                    WHERE team = ?
                """, (team,))

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
                              travel_time_minutes: float,
                              operational_cost: float) -> dict:
        """Calculate total travel cost including salary costs."""
        team_info = self.get_team_salary_info(team)

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

        # Test with a sample team
        test_team = "AC Milan"
        team_info = integrator.get_team_salary_info(test_team)
        if team_info:
            print(f"\nTest Team ({test_team}) Information:")
            print(f"Weekly wage: €{team_info['weekly_wage']:,.2f}")
            print(f"Per minute rate: €{team_info['per_minute']:,.2f}")

            # Calculate sample travel cost
            travel_cost = integrator.calculate_travel_cost(
                test_team,
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
