import pandas as pd
import sqlite3
import os

def import_matches_to_db():
    """Import matches from CSV to SQLite database"""
    try:
        # Read the CSV file
        matches_df = pd.read_csv('cleaned_matches.csv')

        # Connect to database
        conn = sqlite3.connect('data/routes.db')

        # Create matches table
        matches_df.to_sql(
            'matches',
            conn,
            if_exists='replace',  # This will replace the table if it exists
            index=False
        )

        # Verify the import
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM matches")
        count = cursor.fetchone()[0]
        print(f"Successfully imported {count} matches")

        # Create an index on teams for faster querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_teams 
            ON matches ("Home Team", "Away Team")
        """)

        conn.commit()
        conn.close()
        print("Database update completed successfully")

    except Exception as e:
        print(f"Error importing matches: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import_matches_to_db()
