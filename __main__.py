import json
import csv
from playwright.sync_api import sync_playwright

# Load config from JSON file
with open("config.json", "r") as f:
    config = json.load(f)

# Config values
url = config["url"]
u_name = config["login"]["username"]
p_word = config["login"]["password"]
filename = config["output"]["filename"]
weeks = config["output"]["weeks"]
calendar_name = config["calendar"]["name"]
default_colours = config["calendar"]["default_colours"]
event_defaults = config["event_defaults"]
subject_format = config["subject_format"]

# Get events for each week
def get_week_events(page):
    return page.evaluate("""() => {
        const fcEvents = $('#calendar').fullCalendar('clientEvents');
        const domEvents = Array.from(document.querySelectorAll("a.fc-time-grid-event"));
        const merged = [];

        for (let i = 0; i < fcEvents.length; i++) {
            const fc = fcEvents[i];
            const dom = domEvents[i];

            const location = dom?.querySelector(".list-location")?.innerText?.trim() || "";
            
            // Now, extract the title from the <span class="list-title">
            const title = dom?.querySelector(".list-title")?.innerText?.trim() || "";
            const start = fc.start.format("YYYY-MM-DD HH:mm");
            const end = fc.end ? fc.end.format("YYYY-MM-DD HH:mm") : "";

            // DEBUG: Log the raw event title being processed
            console.log("Raw Event Title: ", title);

            // Check if there are square brackets in the title
            const hasBrackets = title.includes("[");
            if (!hasBrackets) {
                console.log("No brackets found in title.");
            }

            // Extract event description from the title, from square brackets (e.g., [ON CAMPUS LECTURE])
            let description = "";
            const match = title.match(/\[(.*?)\]/);  // Look for text inside square brackets

            // DEBUG: Log if we found something inside the brackets
            if (match && match[1]) {
                console.log("Found description in brackets: ", match[1]);
                description = match[1];
            } else {
                console.log("No description found in brackets.");
            }

            merged.push({
                title: title,
                start: start,
                end: end,
                location: location,
                description: description || ""  // If no description found, leave blank
            });
        }

        return merged;
    }""")

def get_subject_from_title(title):
    """Function to extract subject based on the chosen format."""
    # Remove the description part from title (anything inside square brackets)
    cleaned_title = title.split('[')[0].strip()
    if subject_format == "code":
        # Extract module code (e.g., "COMP208" before the first space)
        subject_code = cleaned_title.split(' ')[0]  # Grab the first word (module code)
        return subject_code
    elif subject_format == "code-title":
        # Return the full title without the brackets
        return cleaned_title
    elif subject_format == "title":
        # Return the full title without the brackets or code
        return cleaned_title.replace(cleaned_title.split(' ')[0],"")[2:]
    else:
        # Default case if not specified
        return cleaned_title

with sync_playwright() as p:
    # Start browser and go to login page
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Load website
    page.goto(url)
    # Log in
    page.fill("input[name='UserName']", u_name)
    page.fill("input[name='Password']", p_word)
    page.click("#submitButton")

    # Wait for the calendar to load
    page.wait_for_selector("#calendar", timeout=180000)
    all_events = []

    # Collect all events for number of weeks from config file
    for _ in range(weeks):
        page.wait_for_timeout(1200)  # Wait for 1.2 seconds before scraping events
        events = get_week_events(page)
        all_events.extend(events)
        # Click the next week button
        page.click("button.fc-next-button")

    # Save events in CSV - format for Google Calendar
    with open(filename, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["Subject", "Start Date", "Start Time", "End Date", "End Time", "Location", "Description"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for event in all_events:
            # Get the subject based on the JSON config (either code or full title)
            subject = get_subject_from_title(event["title"])

            # Add colours (not properly utilised)
            module_colour = default_colours.pop(0) if default_colours else 1
            event_data = {
                "Subject": subject,
                "Start Date": event["start"].split(" ")[0],  # Date (YYYY-MM-DD)
                "Start Time": event["start"].split(" ")[1],  # Time (HH:mm)
                "End Date": event["end"].split(" ")[0] if event["end"] else event["start"].split(" ")[0],
                "End Time": event["end"].split(" ")[1] if event["end"] else event["start"].split(" ")[1],
                "Location": event["location"],
                "Description": event["description"]  # Set description
            }
            writer.writerow(event_data)

    print(f"Saved {weeks} weeks of events to {filename}!")
    browser.close()
