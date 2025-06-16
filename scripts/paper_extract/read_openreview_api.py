# OpenReview API to JSONL Extractor
# This script fetches data from a paginated OpenReview-like API,
# iterates through results using 'offset' and 'limit',
# and saves each 'note' (paper entry) as a JSON line in an output file.

import argparse
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

# --- Configuration ---
DELAY_BETWEEN_REQUESTS = 1  # seconds, to be polite to the server
# Dictionary of OpenReview API Endpoints
# Keys are descriptive names, values are base URLs without limit/offset.
OPENREVIEW_API_ENDPOINTS = {
    # ICLR 2025
    "iclr_2025_oral": "https://api2.openreview.net/notes?content.venue=ICLR%202025%20Oral&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2025%2FConference&limit=25&offset=0",
    "iclr_2025_spotlight": "https://api2.openreview.net/notes?content.venue=ICLR%202025%20Spotlight&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2025%2FConference&limit=25&offset=0",
    "iclr_2025_poster": "https://api2.openreview.net/notes?content.venue=ICLR%202025%20Poster&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2025%2FConference&limit=25&offset=0",
    "iclr_2025_blogposts": "https://api2.openreview.net/notes?content.venue=ICLR%202025%20Blogpost%20Track&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2025%2FBlogPosts&invitation=ICLR.cc%2F2025%2FBlogPosts%2F-%2FSubmission&limit=25&offset=0",
    # ICLR 2024
    "iclr_2024_oral": "https://api2.openreview.net/notes?content.venue=ICLR%202024%20oral&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2024%2FConference&limit=25&offset=0",
    "iclr_2024_spotlight": "https://api2.openreview.net/notes?content.venue=ICLR%202024%20spotlight&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2024%2FConference&limit=25&offset=0",
    "iclr_2024_poster": "https://api2.openreview.net/notes?content.venue=ICLR%202024%20poster&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2024%2FConference&limit=25&offset=0",
    "iclr_2024_blogposts": "https://api2.openreview.net/notes?content.venue=BT%40ICLR2024&details=replyCount%2Cpresentation%2Cwritable&domain=ICLR.cc%2F2024%2FBlogPosts&limit=25&offset=0",
    # ICLR 2023
    # Note: The venue names for 2023 are more specific (e.g., "notable top 5%"
    "iclr_2023_notable_top_5_percent": "https://api.openreview.net/notes?content.venue=ICLR+2023+notable+top+5%25&details=replyCount&offset=0&limit=25&invitation=ICLR.cc%2F2023%2FConference%2F-%2FBlind_Submission",
    "iclr_2023_poster": "https://api.openreview.net/notes?content.venue=ICLR+2023+poster&details=replyCount&offset=0&limit=25&invitation=ICLR.cc%2F2023%2FConference%2F-%2FBlind_Submission",
    "iclr_2023_notable_top_25_percent": "https://api.openreview.net/notes?content.venue=ICLR+2023+notable+top+25%25&details=replyCount&offset=0&limit=25&invitation=ICLR.cc%2F2023%2FConference%2F-%2FBlind_Submission",
    "iclr_2023_blogposts": "https://api.openreview.net/notes?content.venue=Blogposts+%40+ICLR+2023&details=replyCount&offset=0&limit=25&invitation=ICLR.cc%2F2023%2FBlogPosts%2F-%2FBlind_Submission",
    # ICLR 2022
    "iclr_2022_spotlight": "https://api.openreview.net/notes?content.venue=ICLR+2022+Spotlight&details=replyCount&offset=0&limit=50&invitation=ICLR.cc%2F2022%2FConference%2F-%2FBlind_Submission",
    "iclr_2022_poster": "https://api.openreview.net/notes?content.venue=ICLR+2022+Poster&details=replyCount&offset=0&limit=50&invitation=ICLR.cc%2F2022%2FConference%2F-%2FBlind_Submission",
    "iclr_2022_oral": "https://api.openreview.net/notes?content.venue=ICLR+2022+Oral&details=replyCount&offset=0&limit=50&invitation=ICLR.cc%2F2022%2FConference%2F-%2FBlind_Submission",
    # ICLR 2021
    # For 2021 and 2020, the URLs are identical except for the offset,
    # indicating they point to the same base query.
    # We only need one entry for the base URL.
    "iclr_2021_conference_submissions": "https://api.openreview.net/notes?invitation=ICLR.cc%2F2021%2FConference%2F-%2FBlind_Submission&details=replyCount%2Cinvitation%2Coriginal%2CdirectReplies&limit=1000&offset=0",
    # ICLR 2020
    "iclr_2020_conference_submissions": "https://api.openreview.net/notes?invitation=ICLR.cc%2F2020%2FConference%2F-%2FBlind_Submission&details=replyCount%2Cinvitation%2Coriginal%2CdirectReplies&limit=1000&offset=0",
}


def extract_paper_data(note):
    """Extracts relevant information from a single 'note' object.

    Adjust this function based on the actual structure of the API response.
    """
    content = note.get("content", {})

    # Helper to safely get values from nested dictionaries
    def get_value(data_dict, key, default=None) -> Any:  # noqa: ANN401
        if isinstance(data_dict.get(key), dict):
            return data_dict.get(key, {}).get("value", default)
        return data_dict.get(key, default)

    return {
        "id": note.get("id"),
        "forum": note.get("forum"),
        "title": get_value(content, "title"),
        "authors": get_value(content, "authors", []),  # Expecting a list
        "author_ids": get_value(content, "authorids", []),  # Expecting a list
        "keywords": get_value(content, "keywords", []),  # Expecting a list
        "abstract": get_value(content, "abstract"),
        "venue": get_value(content, "venue"),
        "venue_id": get_value(content, "venueid"),
        "bibtex": get_value(content, "_bibtex"),
        "blogpost_url": get_value(content, "blogpost_url"),  # From example
        "pdf_url": get_value(content, "pdf"),  # Common field
        "html_url": get_value(content, "html"),  # Common field
        "cdate": note.get("cdate"),  # Creation date of the note itself
        "mdate": note.get("mdate"),  # Modification date
        "odate": note.get("odate"),  # Original submission date
        "tcdate": note.get("tcdate"),  # True creation date
        "tmdate": note.get("tmdate"),  # True modification date
        "original_note_content": content,  # Store whole content for analysis
        # Add any other fields from 'note' or 'note.content' you need
    }


def fetch_and_save_data(api_base_url, output_file_handle, limit_per_request):
    """Fetches all data from the paginated API and saves it."""
    current_offset = 0
    total_processed_count = 0
    total_expected_count = None  # Will be set by the first API call

    print(f"Starting data extraction from: {api_base_url}")
    print(f"Fetching {limit_per_request} items per request.")

    while True:
        # Construct the full API URL with limit and offset
        # Ensure the base URL doesn't already have limit/offset
        paginated_url = (
            f"{api_base_url}&limit={limit_per_request}&offset={current_offset}"
        )

        print(f"  Fetching: {paginated_url}")

        try:
            headers = {"User-Agent": "OpenReviewAPIExtractor/1.0"}
            # Increased timeout for potentially larger responses
            response = requests.get(paginated_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors

            data = response.json()
            notes = data.get("notes", [])

            if total_expected_count is None:  # First call
                total_expected_count = data.get("count", 0)
                if total_expected_count == 0 and not notes:
                    print("  API returned 0 total items and no notes. Exiting.")
                    break
                print(f"  API reports a total of {total_expected_count} items.")

            if not notes:
                print("  No more notes returned by the API.")
                if (
                    total_expected_count is not None
                    and total_processed_count < total_expected_count
                ):
                    print(
                        f"  WARNING: Processed {total_processed_count} items, but API "
                        f"reported {total_expected_count}. There might be an issue or "
                        f"API limit."
                    )
                break

            for note in notes:
                try:
                    paper_data = extract_paper_data(note)
                    # No custom converter needed if data is basic types
                    json_string = json.dumps(paper_data)
                    output_file_handle.write(json_string + "\n")
                    total_processed_count += 1
                except (KeyError, TypeError, ValueError) as e:
                    print(
                        f"    Error processing or serializing note ID "
                        f"{note.get('id', 'N/A')}: {e}"
                    )

            print(
                f"  Processed {len(notes)} notes in this batch. "
                f"Total processed so far: {total_processed_count}"
            )

            # More robust than adding limit_per_request if API returns fewer
            current_offset += len(notes)

            # Check if we've fetched all expected items or if offset implies we're done
            if (
                total_expected_count is not None
                and current_offset >= total_expected_count
            ):
                print(
                    "  Reached or exceeded total expected count based on offset. "
                    "Assuming all data fetched."
                )
                break

            # Safety break if API keeps returning data without count or notes
            # list becomes empty unexpectedly
            if len(notes) < limit_per_request and total_expected_count is None:
                print(
                    "  API returned fewer items than requested and total count "
                    "is unknown. Assuming end of data."
                )
                break

        except requests.exceptions.RequestException as e:
            print(f"  Error fetching data at offset {current_offset}: {e}")
            print("  Retrying in 5 seconds...")
            time.sleep(5)  # Wait a bit before retrying a failed request
            continue  # Retry the current offset
        except json.JSONDecodeError as e:
            print(f"  Error decoding JSON response at offset {current_offset}: {e}")
            # Print beginning of problematic response
            print(f"  Response text: {response.text[:200]}...")
            print("  Skipping this batch and continuing...")
            # Move to next offset to avoid getting stuck
            current_offset += limit_per_request
            # Consider a more robust retry or error logging strategy here

        # Be polite to the server
        time.sleep(DELAY_BETWEEN_REQUESTS)

    print(
        f"\nFinished processing. Total items written to file: {total_processed_count}"
    )
    if (
        total_expected_count is not None
        and total_processed_count != total_expected_count
    ):
        print(
            f"  Note: Final processed count ({total_processed_count}) "
            f"does not match API's reported total ({total_expected_count})."
        )


def remove_pagination_params(url_string):
    """Removes 'limit' and 'offset' query parameters from a URL string."""
    parsed_url = urlparse(url_string)
    query_params = parse_qs(parsed_url.query)

    # Remove 'limit' and 'offset' if they exist
    query_params.pop("limit", None)
    query_params.pop("offset", None)

    # Reconstruct the query string without the removed parameters
    new_query_string = urlencode(query_params, doseq=True)

    # Reconstruct the URL
    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query_string,
            parsed_url.fragment,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "OpenReview API to JSONL Extractor. Fetches paginated 'notes' data."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--api-name",
        type=str,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Number of items to fetch per API request.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Overwrite the output file if it exists, "
            "otherwise append (or create if new)."
        ),
    )

    args = parser.parse_args()
    api_urls = {
        k: remove_pagination_params(v) for k, v in OPENREVIEW_API_ENDPOINTS.items()
    }
    for k, v in api_urls.items():
        print(k, v)

    api_url = api_urls[args.api_name]
    TRIAL = 0
    output_file = f"../../../data/rss_paper_data/open_review_papers.{args.api_name}.t{TRIAL}.jsonl"

    print("OpenReview API to JSONL Extractor")
    print("-" * 40)
    print(f"API Base URL: {api_url}")
    print(f"Output File: {output_file}")
    print(f"Limit per request: {args.limit}")

    file_mode = "a"
    if Path(output_file).exists():
        if args.overwrite:
            file_mode = "w"
            print(f"Output file '{output_file}' will be overwritten.")
        else:
            print(
                f"Appending to existing file '{output_file}'. "
                f"To overwrite, use the --overwrite flag."
            )
    else:
        file_mode = "w"
        print(f"Creating new output file '{output_file}'.")

    try:
        with Path(output_file).open(file_mode, encoding="utf-8") as outfile:
            fetch_and_save_data(api_url, outfile, args.limit)
    except (OSError, ValueError, KeyError) as e:
        print(f"An unexpected error occurred during script execution: {e}")

    print("-" * 40)
    print("Script finished.")
