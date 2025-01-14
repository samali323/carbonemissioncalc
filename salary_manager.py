import sqlite3
import os
from typing import List, Dict
import pandas as pd
import re

class SalaryDatabaseManager:
    def __init__(self):
        """Initialize the database manager with correct paths."""
        # Get the directory where this script is located
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Set up data directory
        self.project_root = os.path.abspath(os.path.join(self.script_dir, "..", ".."))
        self.data_dir = os.path.join(self.project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Database path
        self.db_path = os.path.join(self.data_dir, "routes.db")

        # Excel file path - look in multiple locations
        self.excel_file = self.find_excel_file()

        # Initialize database
        self.setup_database()

    def setup_database(self):
        """Create the salary tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create player_salaries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS player_salaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT NOT NULL,
                        team TEXT NOT NULL,
                        weekly_wage_gbp DECIMAL(15,2),
                        weekly_wage_usd DECIMAL(15,2),
                        yearly_wage_gbp DECIMAL(15,2),
                        yearly_wage_usd DECIMAL(15,2),
                        wage_per_minute_usd DECIMAL(15,2),
                        remaining_contract_value_usd DECIMAL(15,2),
                        status TEXT,
                        position TEXT,
                        position_specific TEXT,
                        age INTEGER,
                        nationality TEXT,
                        competition TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(player_name, team)
                    )
                """)

                # Create team_salary_summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS team_salary_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team TEXT UNIQUE NOT NULL,
                        total_yearly_wage_gbp DECIMAL(15,2),
                        average_yearly_wage_gbp DECIMAL(15,2),
                        total_weekly_wage_gbp DECIMAL(15,2),
                        average_weekly_wage_gbp DECIMAL(15,2),
                        player_count INTEGER,
                        competition TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
        except Exception as e:
            print(f"Error setting up database: {str(e)}")
            raise

    def find_excel_file(self) -> str:
        """Find the salary Excel file in various possible locations."""
        possible_locations = [
            os.path.join(self.script_dir, "All Salaries_Footy.xlsx"),
            os.path.join(self.project_root, "All Salaries_Footy.xlsx"),
            os.path.join(self.data_dir, "All Salaries_Footy.xlsx")
        ]

        for location in possible_locations:
            if os.path.exists(location):
                print(f"Found Excel file at: {location}")
                return location

        print("Searching in current directory...")
        for file in os.listdir(self.script_dir):
            if file.endswith('.xlsx') and 'salaries' in file.lower():
                full_path = os.path.join(self.script_dir, file)
                print(f"Found Excel file at: {full_path}")
                return full_path

        return None

    def clean_currency_value(self, value: str) -> str:
        """Clean currency values by removing symbols and commas."""
        if isinstance(value, (int, float)):
            return str(value)
        return re.sub(r'[$£€,\s]', '', str(value))

    def process_salary_data(self, excel_file: str = None):
        """Process salary data from Excel file and store in database."""
        try:
            # Use provided file path or default to found file
            file_to_use = excel_file or self.excel_file

            if not file_to_use or not os.path.exists(file_to_use):
                print("\nSearching for Excel file...")
                file_to_use = self.find_excel_file()
                if not file_to_use:
                    return False, "Could not find salary Excel file"

            print(f"\nReading Excel file: {file_to_use}")
            df = pd.read_excel(file_to_use)

            # Print original columns
            print("\nOriginal columns in Excel file:")
            print(df.columns.tolist())

            # Define exact column mappings based on your Excel structure
            column_mapping = {
                'Player': 'player_name',
                'Gross P/W (GBP/EUR)': 'weekly_wage_gbp',
                'Gross P/W (USD)': 'weekly_wage_usd',
                'Gross P/Min(USD)': 'wage_per_minute_usd',
                'Gross P/Y  (GBP/EUR)': 'yearly_wage_gbp',
                'Gross P/Y (USD)': 'yearly_wage_usd',
                'Gross P/Y  (GBP/EUR) BONUS': 'yearly_bonus_gbp',
                'Gross Remaining (USD)': 'remaining_contract_value_usd',
                'Status': 'status',
                'Pos.': 'position',
                'Pos..1': 'position_specific',
                'Age': 'age',
                'Country': 'nationality',
                'Club': 'team',
                'Competition': 'competition',
                'Signed': 'contract_start',
                'Expiration': 'contract_end',
                'Years Remaining': 'years_remaining'
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            print("\nMapped columns:")
            print(df.columns.tolist())

            # Clean numeric columns
            numeric_columns = [
                'weekly_wage_gbp', 'weekly_wage_usd', 'wage_per_minute_usd',
                'yearly_wage_gbp', 'yearly_wage_usd', 'yearly_bonus_gbp',
                'remaining_contract_value_usd', 'years_remaining'
            ]

            for col in numeric_columns:
                if col in df.columns:
                    # Convert to numeric, removing currency symbols and commas
                    df[col] = df[col].astype(str).replace(r'[\$£€,]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Convert date columns
            date_columns = ['contract_start', 'contract_end']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            print("\nSample of processed data:")
            print(df.head())
            print("\nData types:")
            print(df.dtypes)

            with sqlite3.connect(self.db_path) as conn:
                # Store individual player data
                columns_to_save = [
                    'player_name', 'team', 'weekly_wage_gbp', 'weekly_wage_usd',
                    'yearly_wage_gbp', 'yearly_wage_usd', 'yearly_bonus_gbp',
                    'wage_per_minute_usd', 'remaining_contract_value_usd',
                    'status', 'position', 'position_specific', 'age',
                    'nationality', 'competition', 'contract_start', 'contract_end'
                ]

                # Only save columns that exist in the DataFrame
                existing_columns = [col for col in columns_to_save if col in df.columns]
                df[existing_columns].to_sql('player_salaries', conn, if_exists='replace', index=False)

                # Calculate and store team summaries
                summary_data = []
                for (team, comp), group in df.groupby(['team', 'competition']):
                    summary = {
                        'team': team,
                        'competition': comp,
                        'total_yearly_wage_gbp': group['yearly_wage_gbp'].sum(),
                        'average_yearly_wage_gbp': group['yearly_wage_gbp'].mean(),
                        'total_weekly_wage_gbp': group['weekly_wage_gbp'].sum(),
                        'average_weekly_wage_gbp': group['weekly_wage_gbp'].mean(),
                        'player_count': len(group)
                    }
                    summary_data.append(summary)

                # Convert summary data to DataFrame and save
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_sql('team_salary_summary', conn, if_exists='replace', index=False)

            return True, "Salary data processed successfully"

        except Exception as e:
            import traceback
            return False, f"Error processing salary data: {str(e)}\n{traceback.format_exc()}"

    def get_salary_statistics(self) -> Dict:
        """Get overall salary statistics from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT team) as total_teams,
                        COUNT(*) as total_players,
                        AVG(yearly_wage_gbp) as average_yearly_wage,
                        MAX(yearly_wage_gbp) as max_yearly_wage,
                        MIN(yearly_wage_gbp) as min_yearly_wage,
                        AVG(weekly_wage_gbp) as average_weekly_wage,
                        MAX(weekly_wage_gbp) as max_weekly_wage,
                        MIN(weekly_wage_gbp) as min_weekly_wage
                    FROM player_salaries
                    WHERE yearly_wage_gbp > 0
                """)

                result = cursor.fetchone()
                if result:
                    return {
                        'total_teams': result[0],
                        'total_players': result[1],
                        'average_yearly_wage': result[2],
                        'max_yearly_wage': result[3],
                        'min_yearly_wage': result[4],
                        'average_weekly_wage': result[5],
                        'max_weekly_wage': result[6],
                        'min_weekly_wage': result[7]
                    }
                return None
        except Exception as e:
            print(f"Error getting salary statistics: {str(e)}")
            return None

    def get_team_salary_info(self, team: str) -> Dict:
        """Get salary information for a specific team."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        total_yearly_wage_gbp, 
                        average_yearly_wage_gbp,
                        total_weekly_wage_gbp,
                        average_weekly_wage_gbp,
                        player_count,
                        competition
                    FROM team_salary_summary
                    WHERE team = ?
                    ORDER BY last_updated DESC
                    LIMIT 1
                """, (team,))

                result = cursor.fetchone()
                if result:
                    return {
                        'total_yearly_wage_gbp': result[0],
                        'average_yearly_wage_gbp': result[1],
                        'total_weekly_wage_gbp': result[2],
                        'average_weekly_wage_gbp': result[3],
                        'player_count': result[4],
                        'competition': result[5]
                    }
                return None
        except Exception as e:
            print(f"Error getting team salary info: {str(e)}")
            return None

if __name__ == "__main__":
    try:
        print("Initializing SalaryDatabaseManager...")
        manager = SalaryDatabaseManager()

        print("\nProcessing salary data...")
        success, message = manager.process_salary_data()
        print(message)

        if success:
            print("\nRetrieving salary statistics...")
            stats = manager.get_salary_statistics()
            if stats:
                print("\nSalary Statistics:")
                print(f"Total Teams: {stats['total_teams']}")
                print(f"Total Players: {stats['total_players']}")
                print(f"Average Yearly Wage: £{stats['average_yearly_wage']:,.2f}")
                print(f"Maximum Yearly Wage: £{stats['max_yearly_wage']:,.2f}")
                print(f"Minimum Yearly Wage: £{stats['min_yearly_wage']:,.2f}")
                print(f"\nAverage Weekly Wage: £{stats['average_weekly_wage']:,.2f}")
                print(f"Maximum Weekly Wage: £{stats['max_weekly_wage']:,.2f}")
                print(f"Minimum Weekly Wage: £{stats['min_weekly_wage']:,.2f}")
    except Exception as e:
        print(f"Error running salary manager: {str(e)}")
