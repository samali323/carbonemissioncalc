import os
import shutil

def collect_python_files(source_dir: str, output_dir: str) -> None:
    """
    Simply collect all Python files and copy them to the output directory.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    files_copied = 0

    print(f"Collecting Python files from: {source_dir}")
    print(f"Output directory: {output_dir}")

    # Walk through all directories
    for root, dirs, files in os.walk(source_dir):
        # Skip __pycache__ directories
        if '__pycache__' in root or '.git' in root:
            continue

        # Filter for Python files
        python_files = [f for f in files if f.endswith('.py')]

        for py_file in python_files:
            try:
                # Get the full source path
                source_path = os.path.join(root, py_file)

                # Set the destination path
                dest_path = os.path.join(output_dir, py_file)

                # Copy the file
                shutil.copy2(source_path, dest_path)
                files_copied += 1

                print(f"Copied: {py_file}")

            except Exception as e:
                print(f"Error copying {py_file}: {str(e)}")

    print(f"\nCompleted! {files_copied} Python files collected to: {output_dir}")

if __name__ == "__main__":
    # Source directory - CarbonEmissionCalc project
    source_dir = r"C:\Users\samal\PycharmProjects\FlightEmissions\CarbonEmissionCalc"

    # Output directory - Code-Backup
    output_dir = r"C:\Users\samal\Documents\Code-Backup"

    # Execute collection
    collect_python_files(source_dir, output_dir)
