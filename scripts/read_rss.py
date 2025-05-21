# PMLR RSS Feed Inspector
# This script fetches and parses a PMLR RSS feed and displays the available information for each entry.

# Prerequisites:
# You need to install the 'requests' and 'feedparser' libraries if you haven't already.
# You can install them using pip:
# pip install requests feedparser

import requests
import feedparser

def inspect_rss_feed(feed_url):
    """
    Fetches, parses, and prints the contents of an RSS feed.

    Args:
        feed_url (str): The URL of the RSS feed to inspect.
    """
    print(f"Attempting to fetch RSS feed from: {feed_url}\n")

    try:
        # 1. Fetch the RSS feed content using requests
        # Adding a User-Agent is good practice
        headers = {
            'User-Agent': 'PMLRFeedInspector/1.0 (https://example.com/my-script-info)'
        }
        response = requests.get(feed_url, headers=headers, timeout=10) # 10-second timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print("Feed fetched successfully.\n")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the RSS feed: {e}")
        return

    # 2. Parse the feed content using feedparser
    # response.content contains the raw bytes of the feed, feedparser handles decoding
    feed = feedparser.parse(response.content)

    # 3. Display general feed information (optional, but useful)
    print("--- Feed Information ---")
    if hasattr(feed, 'feed'):
        if hasattr(feed.feed, 'title'):
            print(f"Feed Title: {feed.feed.title}")
        if hasattr(feed.feed, 'link'):
            print(f"Feed Link: {feed.feed.link}")
        if hasattr(feed.feed, 'description'):
            print(f"Feed Description: {feed.feed.description}")
    print(f"Number of entries: {len(feed.entries)}\n")

    # 4. Iterate through each entry and print its available fields
    if not feed.entries:
        print("No entries found in the feed.")
        return

    print("--- Feed Entries ---")
    for i, entry in enumerate(feed.entries):
        print(f"\n--- Entry {i+1} ---")
        # feedparser entries behave like dictionaries, so we can iterate over their keys
        for key in entry.keys():
            print(f"  {key}: {entry[key]}")
        
        # Some common attributes might be nested (e.g., authors)
        # feedparser often normalizes these.
        # For example, 'authors' is usually a list of author detail objects.
        # 'summary' or 'description' often contains the abstract.

        # Example of explicitly checking for common fields:
        # if 'title' in entry:
        #     print(f"  Title: {entry.title}")
        # if 'link' in entry:
        #     print(f"  Link: {entry.link}")
        # if 'summary' in entry: # 'summary' often holds the abstract
        #     print(f"  Summary (Abstract?): {entry.summary[:200]}...") # Print first 200 chars
        # if 'authors' in entry:
        #     # Authors is a list of dicts, e.g., [{'name': 'Author One'}, {'name': 'Author Two'}]
        #     author_names = [author.get('name', 'N/A') for author in entry.authors]
        #     print(f"  Authors: {', '.join(author_names)}")
        # if 'published' in entry:
        #     print(f"  Published Date: {entry.published}")
        # if 'id' in entry: # Often a unique identifier, sometimes the same as the link
        #     print(f"  ID: {entry.id}")

    print("\n--- End of Feed Inspection ---")

if __name__ == "__main__":
    # Example PMLR RSS feed URL (CoLLAs 2023 - v232)
    # You can replace this with any other PMLR RSS feed URL
    default_feed_url = "https://proceedings.mlr.press//v232/assets/rss/feed.xml"
    
    # You could also get the URL from user input:
    # feed_url_input = input(f"Enter RSS feed URL (or press Enter for default: {default_feed_url}): ")
    # if not feed_url_input:
    #     feed_url_input = default_feed_url
    
    inspect_rss_feed(default_feed_url)

    # Example of another feed (PMLR Volume 202 - AISTATS 2023)
    # print("\n\n--- Inspecting another feed (AISTATS 2023) ---")
    # inspect_rss_feed("https://proceedings.mlr.press/v202/rss.xml")
