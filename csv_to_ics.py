import csv
import json
from datetime import datetime

# Function to read the output filename from the config.json
def get_output_filename(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config.get("output", "default_output.ics")  # Default filename if key is not found

# Function to convert CSV event to ICS format
def csv_to_ics(csv_file, ics_file):
    # Read the CSV file
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        events = list(reader)

    # Open the ICS file for writing
    with open(ics_file, 'w') as ics:
        # Write the ICS file header
        ics.write("BEGIN:VCALENDAR\n")
        ics.write("VERSION:2.0\n")
        ics.write("PRODID:-//Apple Inc.//NONSGML iCal 2.0//EN\n")
        
        # Process each event in the CSV
        for event in events:
            # Get the event details from the CSV
            subject = event['Subject']
            start_date = event['Start Date']
            start_time = event['Start Time']
            end_date = event['End Date']
            end_time = event['End Time']
            location = event['Location'] if event['Location'] else 'TBD'
            description = event['Description'] if event['Description'] else ''
            
            # Combine the date and time into a single datetime string
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

            # Convert to the ICS format (UTC for consistency)
            start_utc = start_datetime.strftime('%Y%m%dT%H%M%S')
            end_utc = end_datetime.strftime('%Y%m%dT%H%M%S')

            # Write the event in ICS format
            ics.write("BEGIN:VEVENT\n")
            ics.write(f"SUMMARY:{subject}\n")
            ics.write(f"DTSTART:{start_utc}\n")
            ics.write(f"DTEND:{end_utc}\n")
            ics.write(f"LOCATION:{location}\n")
            ics.write(f"DESCRIPTION:{description}\n")
            ics.write("END:VEVENT\n")

        # Write the ICS file footer
        ics.write("END:VCALENDAR\n")

# Define file paths
csv_file = 'timetable.csv'  # Path to your CSV file
config_file = 'config.json'  # Path to your config.json

# Get the output filename from the config file
ics_file = get_output_filename(config_file)

# Convert CSV to ICS using the output filename from config
csv_to_ics(csv_file, ics_file)
print(f"ICS file created: {ics_file}")
