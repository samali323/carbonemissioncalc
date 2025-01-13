import sqlite3
import pandas as pd

def update_database_with_competitions():
    """Add competition data to routes database from CSV"""
    try:
        # Read the cleaned_matches CSV
        matches_df = pd.read_csv('cleaned_matches.csv')

        # Connect to database
        conn = sqlite3.connect('data/routes.db')

        # Add Competition column if it doesn't exist
        conn.execute("""
        ALTER TABLE routes ADD COLUMN Competition TEXT DEFAULT 'Unknown';
        """)

        # Update routes table with competition data
        for _, row in matches_df.iterrows():
            conn.execute("""
            UPDATE routes 
            SET Competition = ? 
            WHERE home_team = ? AND away_team = ?
            """, (row['Competition'], row['Home Team'], row['Away Team']))

        conn.commit()
        conn.close()
        print("Successfully updated database with competition data")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Competition column already exists")
        else:
            print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error updating database: {str(e)}")

if __name__ == "__main__":
    update_database_with_competitions()
