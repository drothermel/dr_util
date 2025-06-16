# PMLR Multi-Volume RSS to JSONL Extractor
# This script fetches RSS feeds for a range of PMLR volumes,
# parses them, and saves each paper entry as a JSON line in an output file.

# Prerequisites:
# You need to install the 'requests' and 'feedparser' libraries if you haven't already.
# You can install them using pip:
# pip install requests feedparser

import argparse
import json
import re
import sys
import time
from pathlib import Path

import feedparser
import requests

# --- Configuration ---
REQUEST_TIMEOUT = 15  # second
DELAY_BETWEEN_VOLUMES = 2  # seconds, to be polite to the server
HTTP_NOT_FOUND = 404  # HTTP status code for not found
FIELDS_TO_DROP = [
    "title_detail",
    "summary_detail",
    "published_parsed",
    "updated_parsed",
]  # Added updated_parsed as it's similar


# --- Helper Function for JSON Serialization ---
def json_converter(o):
    """Converts objects that are not directly JSON serializable.

    Specifically handles time.struct_time from feedparser.
    """
    if isinstance(o, time.struct_time):
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", o)
        except TypeError:
            return str(o)
    msg = f"Object of type {o.__class__.__name__} is not JSON serializable"
    raise TypeError(msg)


# --- Helper Functions for Conference Metadata Extraction ---


def fetch_rss_feed(volume_number):
    """Fetch RSS feed for a given volume number.

    Args:
        volume_number (int): The PMLR volume number.

    Returns:
        feedparser.FeedParserDict or None: Parsed feed or None if failed.
    """
    feed_url = f"https://proceedings.mlr.press/v{volume_number}/assets/rss/feed.xml"
    print(f"\nProcessing Volume {volume_number} from: {feed_url}")

    try:
        headers = {
            "User-Agent": (f"PMLRMultiVolumeExtractor/1.1 (Volume {volume_number})")
        }
        response = requests.get(feed_url, headers=headers, timeout=REQUEST_TIMEOUT)

        if response.status_code == HTTP_NOT_FOUND:
            print(
                f"  WARNING: Volume {volume_number} RSS feed not found "
                f"({HTTP_NOT_FOUND} Error). Skipping."
            )
            return None

        response.raise_for_status()
        return feedparser.parse(response.content)

    except requests.exceptions.RequestException as e:
        print(f"  Error fetching RSS feed for Volume {volume_number}: {e}")
        return None


def extract_year_from_published(feed_meta):
    """Extract year from feed's published_parsed field.

    Args:
        feed_meta: Feed metadata object.

    Returns:
        str: Year as string or "N/A" if not found.
    """
    if not feed_meta.get("published_parsed"):
        return "N/A"

    import contextlib

    with contextlib.suppress(AttributeError):
        return str(feed_meta.published_parsed.tm_year)
    return "N/A"


def extract_from_managing_editor(managing_editor_str):
    """Extract conference short name and year from managingEditor field.

    Args:
        managing_editor_str (str): Managing editor string.

    Returns:
        tuple: (conference_short_name, conference_year) or ("N/A", "N/A").
    """
    if not managing_editor_str:
        return "N/A", "N/A"

    # Regex to find patterns like "(CoLLAs 2023)" or "(AISTATS 2023)"
    pattern = r"\(([^)]+?)\s+(19\d{2}|20\d{2})\)$"
    match = re.search(pattern, managing_editor_str.strip())

    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "N/A", "N/A"


def extract_year_fallbacks(feed_meta, conference_title_from_feed, current_year):
    """Extract year using fallback methods.

    Args:
        feed_meta: Feed metadata object.
        conference_title_from_feed (str): Conference title from feed.
        current_year (str): Current year value.

    Returns:
        str: Year as string or current_year if not found.
    """
    if current_year != "N/A":
        return current_year

    # Try from description
    description_text = feed_meta.get("description", "")
    if description_text:
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", description_text)
        if year_match:
            return year_match.group(1)

    # Try from feed title as last resort
    if conference_title_from_feed != "N/A":
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", conference_title_from_feed)
        if year_match:
            return year_match.group(1)

    return current_year


def extract_conference_metadata(feed):
    """Extract conference metadata from RSS feed.

    Args:
        feed: Parsed RSS feed object.

    Returns:
        tuple: (conference_short_name, conference_year, conference_title_from_feed).
    """
    conference_short_name = "N/A"
    conference_year = "N/A"
    conference_title_from_feed = "N/A"

    if not hasattr(feed, "feed"):
        return conference_short_name, conference_year, conference_title_from_feed

    feed_meta = feed.feed
    conference_title_from_feed = feed_meta.get("title", "N/A")
    conf_desc = feed_meta.get("description", "N/A")

    # 1. Try to get year from published_parsed
    conference_year = extract_year_from_published(feed_meta)

    # 2. Try to get short name and year from managingEditor
    managing_editor_str = feed_meta.get("managingEditor", "")
    editor_short_name, editor_year = extract_from_managing_editor(managing_editor_str)

    if editor_short_name != "N/A":
        conference_short_name = editor_short_name
    if editor_year != "N/A":
        conference_year = editor_year

    # 3. Fallbacks for year
    conference_year = extract_year_fallbacks(
        feed_meta, conference_title_from_feed, conference_year
    )

    # 4. Fallback for conference_short_name
    if conference_short_name == "N/A" and conference_title_from_feed != "N/A":
        conference_short_name = re.sub(
            r"^Proceedings of\s*", "", conf_desc.split("\n")[0]
        )

    return conference_short_name, conference_year, conference_title_from_feed


def process_entries_to_jsonl(
    feed, conference_metadata, output_file_handle, volume_number
):
    """Process feed entries and write to JSONL format.

    Args:
        feed: Parsed RSS feed object.
        conference_metadata (tuple): Conference metadata tuple.
        output_file_handle: File handle for writing.
        volume_number (int): Volume number for error reporting.

    Returns:
        int: Number of entries processed.
    """
    conference_short_name, conference_year, conference_title_from_feed = (
        conference_metadata
    )

    if not feed.entries:
        print(f"  No entries found in the feed for Volume {volume_number}.")
        return 0

    entries_processed_count = 0
    for i, entry in enumerate(feed.entries):
        try:
            # Create a dictionary from the FeedParserDict to add custom fields
            entry_data = dict(entry)

            # Add extracted conference metadata to each paper entry
            entry_data["conference_short_name"] = conference_short_name
            entry_data["conference_year"] = conference_year
            entry_data["conference_title_from_feed"] = conference_title_from_feed

            # Drop specified fields before writing
            for field_to_drop in FIELDS_TO_DROP:
                if field_to_drop in entry_data:
                    del entry_data[field_to_drop]

            json_string = json.dumps(entry_data, default=json_converter)
            output_file_handle.write(json_string + "\n")
            entries_processed_count += 1
        except (TypeError, ValueError, KeyError) as e:
            print(
                f"    Error serializing entry {i + 1} for Volume {volume_number}: {e}"
            )

    return entries_processed_count


# --- Core Processing Function ---
def process_volume_to_jsonl(volume_number, output_file_handle):
    """Fetches, parses, extracts conference metadata, and writes entries.

    From a single volume's RSS feed to the output file.

    Args:
        volume_number (int): The PMLR volume number.
        output_file_handle: An open file handle for writing JSON lines.

    Returns:
        int: Number of entries processed for this volume.
    """
    # Fetch RSS feed
    feed = fetch_rss_feed(volume_number)
    if feed is None:
        return 0

    # Extract conference metadata
    conference_metadata = extract_conference_metadata(feed)
    conference_short_name, conference_year, conference_title_from_feed = (
        conference_metadata
    )

    print(
        f"  Extracted Conference Info: Name='{conference_short_name}', "
        f"Year='{conference_year}', FeedTitle='{conference_title_from_feed[:60]}...'"
    )

    # Process entries and write to JSONL
    entries_processed_count = process_entries_to_jsonl(
        feed, conference_metadata, output_file_handle, volume_number
    )

    print(
        f"  Successfully processed {entries_processed_count} entries "
        f"for Volume {volume_number}."
    )
    return entries_processed_count


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "PMLR Multi-Volume RSS to JSONL Extractor "
            "(with Conference Metadata & Field Dropping)"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # Shows defaults
    )
    parser.add_argument(
        "-s",
        "--start-volume",
        type=int,
        default=230,
        help="The first PMLR volume number to process.",
    )
    parser.add_argument(
        "-e",
        "--end-volume",
        type=int,
        default=232,
        help="The last PMLR volume number to process",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",  # Becomes True if flag is present
        help="Overwrite the output file if it exists, otherwise append.",
    )

    args = parser.parse_args()

    start_volume = args.start_volume
    end_volume = args.end_volume
    TRIAL = 0
    print("PMLR Multi-Volume RSS to JSONL Extractor (with Conference Metadata)")
    print("-" * 70)

    # drotherm/repos/dr_util/scripts/read_rss.py
    # drotherm/data/rss_paper_data/
    OUTPUT_FILENAME = (
        f"../../../data/rss_paper_data/pmlr_papers."
        f"v{start_volume}.v{end_volume}.t{TRIAL}.jsonl"
    )

    print(f"Will process volumes from {start_volume} to {end_volume}.")
    print(f"Output will be saved to: {OUTPUT_FILENAME}")
    print(f"Fields to be dropped from each entry: {', '.join(FIELDS_TO_DROP)}")

    file_mode = "a"
    output_path = Path(OUTPUT_FILENAME)
    if output_path.exists():
        while True:
            choice = (
                input(
                    f"File '{OUTPUT_FILENAME}' already exists. "
                    "(A)ppend, (O)verwrite, or (Q)uit? [A/O/Q]: "
                )
                .strip()
                .lower()
            )
            if choice == "o":
                file_mode = "w"
                print(f"Output file '{OUTPUT_FILENAME}' will be overwritten.")
                break
            elif choice == "q":
                print("Exiting.")
                sys.exit()
            elif choice == "a":
                print(f"Appending to existing file '{OUTPUT_FILENAME}'.")
                break
            else:
                print("Invalid choice. Please enter A, O, or Q.")
    else:
        file_mode = "w"
        print(f"Creating new output file '{OUTPUT_FILENAME}'.")

    total_entries_overall = 0
    with output_path.open(file_mode, encoding="utf-8") as outfile:
        for volume in range(start_volume, end_volume + 1):
            entries_from_volume = process_volume_to_jsonl(volume, outfile)
            total_entries_overall += entries_from_volume
            if volume < end_volume:
                print(
                    f"  Waiting for {DELAY_BETWEEN_VOLUMES} seconds "
                    "before next volume..."
                )
                time.sleep(DELAY_BETWEEN_VOLUMES)

    print("-" * 70)
    print(f"Processing complete. Total entries written: {total_entries_overall}")
    print(f"Data saved to {OUTPUT_FILENAME}")
