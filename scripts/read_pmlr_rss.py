# PMLR Multi-Volume RSS to JSONL Extractor
# This script fetches RSS feeds for a range of PMLR volumes,
# parses them, and saves each paper entry as a JSON line in an output file.

# Prerequisites:
# You need to install the 'requests' and 'feedparser' libraries if you haven't already.
# You can install them using pip:
# pip install requests feedparser

import requests
import feedparser
import json
import time
import argparse
import os # For checking if file exists
import re

# --- Configuration ---
REQUEST_TIMEOUT = 15  # second
DELAY_BETWEEN_VOLUMES = 2  # seconds, to be polite to the server
FIELDS_TO_DROP = ["title_detail", "summary_detail", "published_parsed", "updated_parsed"] # Added updated_parsed as it's similar

# --- Helper Function for JSON Serialization ---
def json_converter(o):
    """
    Converts objects that are not directly JSON serializable.
    Specifically handles time.struct_time from feedparser.
    """
    if isinstance(o, time.struct_time):
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", o)
        except TypeError: 
            return str(o) 
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable and not handled by json_converter")

# --- Core Processing Function ---
def process_volume_to_jsonl(volume_number, output_file_handle):
    """
    Fetches, parses, extracts conference metadata, and writes entries 
    from a single volume's RSS feed to the output file.

    Args:
        volume_number (int): The PMLR volume number.
        output_file_handle: An open file handle for writing JSON lines.
    Returns:
        int: Number of entries processed for this volume.
    """
    feed_url = f"https://proceedings.mlr.press/v{volume_number}/assets/rss/feed.xml"
    print(f"\nProcessing Volume {volume_number} from: {feed_url}")

    try:
        headers = {
            'User-Agent': f'PMLRMultiVolumeExtractor/1.1 (Volume {volume_number})' # Updated version
        }
        response = requests.get(feed_url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 404:
            print(f"  WARNING: Volume {volume_number} RSS feed not found (404 Error). Skipping.")
            return 0
        
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching RSS feed for Volume {volume_number}: {e}")
        return 0

    feed = feedparser.parse(response.content)

    # Extract conference metadata from the feed itself
    conference_short_name = "N/A"
    conference_year = "N/A"
    conference_title_from_feed = "N/A"

    if hasattr(feed, 'feed'):
        feed_meta = feed.feed
        conference_title_from_feed = feed_meta.get("title", "N/A")
        conf_desc = feed_meta.get("description", "N/A")

        # 1. Attempt to get year from published_parsed (of the feed itself)
        if feed_meta.get("published_parsed"):
            try:
                conference_year = str(feed_meta.published_parsed.tm_year)
            except AttributeError: 
                pass # Handled by later fallbacks

        # 2. Attempt to get short name and potentially year from managingEditor
        managing_editor_str = feed_meta.get("managingEditor", "")
        if managing_editor_str:
            # Regex to find patterns like "(CoLLAs 2023)" or "(AISTATS 2023)"
            match = re.search(r'\(([^)]+?)\s+(19\d{2}|20\d{2})\)$', managing_editor_str.strip())
            if match:
                conference_short_name = match.group(1).strip()
                # Prefer year from managingEditor if available and matches a year format
                conference_year = match.group(2).strip() 
        
        # 3. Fallbacks for year if still "N/A" (after trying managingEditor and feed's published_parsed)
        if conference_year == "N/A": # Check if year is still not found
            description_text = feed_meta.get("description", "")
            if description_text:
                year_match_desc = re.search(r'\b(19\d{2}|20\d{2})\b', description_text)
                if year_match_desc:
                    conference_year = year_match_desc.group(1)
        
        if conference_year == "N/A" and conference_title_from_feed != "N/A":
            # Try from feed title as last resort for year
            year_match_title = re.search(r'\b(19\d{2}|20\d{2})\b', conference_title_from_feed)
            if year_match_title:
                conference_year = year_match_title.group(1)

        # 4. Fallback for conference_short_name: if still "N/A", use the full feed title
        if conference_short_name == "N/A" and conference_title_from_feed != "N/A":
            conference_short_name = re.sub(r"^Proceedings of\s*", "",conf_desc.split("\n")[0])
    
    
    print(f"  Extracted Conference Info: Name='{conference_short_name}', Year='{conference_year}', FeedTitle='{conference_title_from_feed[:60]}...'")

    if not feed.entries:
        print(f"  No entries found in the feed for Volume {volume_number}.")
        return 0

    entries_processed_count = 0
    for i, entry in enumerate(feed.entries):
        try:
            # Create a dictionary from the FeedParserDict to add custom fields
            entry_data = dict(entry) 
            
            # Add extracted conference metadata to each paper entry
            entry_data['conference_short_name'] = conference_short_name
            entry_data['conference_year'] = conference_year
            # Optionally, add the full title from the feed's metadata for context
            entry_data['conference_title_from_feed'] = conference_title_from_feed

            # Drop specified fields before writing
            for field_to_drop in FIELDS_TO_DROP:
                if field_to_drop in entry_data:
                    del entry_data[field_to_drop]

            json_string = json.dumps(entry_data, default=json_converter)
            output_file_handle.write(json_string + "\n")
            entries_processed_count += 1
        except Exception as e:
            print(f"    Error serializing entry {i+1} for Volume {volume_number}: {e}")
            # print(f"      Problematic entry keys: {list(entry.keys())}") # For debugging

    print(f"  Successfully processed {entries_processed_count} entries for Volume {volume_number}.")
    return entries_processed_count

# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PMLR Multi-Volume RSS to JSONL Extractor (with Conference Metadata & Field Dropping)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
    )
    parser.add_argument(
        "-s", "--start-volume",
        type=int,
        default=230,
        help="The first PMLR volume number to process.",
    )
    parser.add_argument(
        "-e", "--end-volume",
        type=int,
        default=232,
        help=f"The last PMLR volume number to process",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true", # Becomes True if flag is present
        help="Overwrite the output file if it exists, otherwise append (or create if new)."
    )

    args = parser.parse_args()

    start_volume = args.start_volume
    end_volume = args.end_volume
    TRIAL = 0
    print("PMLR Multi-Volume RSS to JSONL Extractor (with Conference Metadata)")
    print("-" * 70)

    # drotherm/repos/dr_util/scripts/read_rss.py
    # drotherm/data/rss_paper_data/
    OUTPUT_FILENAME = f"../../../data/rss_paper_data/pmlr_papers.v{start_volume}.v{end_volume}.t{TRIAL}.jsonl"

    print(f"Will process volumes from {start_volume} to {end_volume}.")
    print(f"Output will be saved to: {OUTPUT_FILENAME}")
    print(f"Fields to be dropped from each entry: {', '.join(FIELDS_TO_DROP)}")


    file_mode = 'a' 
    if os.path.exists(OUTPUT_FILENAME):
        while True:
            choice = input(f"File '{OUTPUT_FILENAME}' already exists. (A)ppend, (O)verwrite, or (Q)uit? [A/O/Q]: ").strip().lower()
            if choice == 'o':
                file_mode = 'w'
                print(f"Output file '{OUTPUT_FILENAME}' will be overwritten.")
                break
            elif choice == 'q':
                print("Exiting.")
                exit()
            elif choice == 'a':
                print(f"Appending to existing file '{OUTPUT_FILENAME}'.")
                break
            else:
                print("Invalid choice. Please enter A, O, or Q.")
    else:
        file_mode = 'w' 
        print(f"Creating new output file '{OUTPUT_FILENAME}'.")

    total_entries_overall = 0
    with open(OUTPUT_FILENAME, file_mode, encoding='utf-8') as outfile:
        for volume in range(start_volume, end_volume + 1):
            entries_from_volume = process_volume_to_jsonl(volume, outfile)
            total_entries_overall += entries_from_volume
            if volume < end_volume: 
                print(f"  Waiting for {DELAY_BETWEEN_VOLUMES} seconds before next volume...")
                time.sleep(DELAY_BETWEEN_VOLUMES)
    
    print("-" * 70)
    print(f"Processing complete. Total entries written: {total_entries_overall}")
    print(f"Data saved to {OUTPUT_FILENAME}")
