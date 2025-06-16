# cvf_open_access_scraper.py
# This script scrapes paper information from a CVF Open Access conference page
# (e.g., http://openaccess.thecvf.com/CVPR2024?day=all) and saves it to a JSONL file.

import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def extract_paper_info_from_cvf(html_content, page_url):
    """Parses the HTML content of a CVF Open Access page and extracts paper information.

    Args:
        html_content (str): The HTML content of the page.
        page_url (str): The URL of the page being scraped, used to resolve relative
            links.

    Returns:
        list: A list of dictionaries, where each dictionary contains info for one paper.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    papers_data = []

    # The base URL for resolving relative links (e.g., http://openaccess.thecvf.com)
    parsed_page_url = urlparse(page_url)
    base_url = f"{parsed_page_url.scheme}://{parsed_page_url.netloc}"

    # Each paper's title is in a <dt class="ptitle">
    # The subsequent <dd> elements contain authors and then links/bibtex
    paper_titles_dt = soup.find_all("dt", class_="ptitle")

    for dt_title in paper_titles_dt:
        paper_info = {
            "title": None,
            "cvf_html_link": None,
            "authors": [],
            "pdf_link": None,
            "supplemental_link": None,
            "arxiv_link": None,
            "bibtex": None,
            "source_url": page_url # Keep track of where this data came from
        }

        # --- Extract Title and HTML link ---
        title_anchor = dt_title.find("a")
        if title_anchor and title_anchor.get("href"):
            paper_info["title"] = title_anchor.get_text(strip=True)
            paper_info["cvf_html_link"] = urljoin(base_url, title_anchor["href"])
        else:
            # If no anchor, might be an issue with the structure or an empty dt
            print(
                f"Warning: Could not find title anchor for a <dt class='ptitle'> "
                f"element. Content: {dt_title.get_text(strip=True)}"
            )
            continue # Skip this entry if title can't be found

        # --- Extract Authors ---
        # Authors are in the first <dd> immediately following the <dt class="ptitle">
        authors_dd = dt_title.find_next_sibling("dd")
        if authors_dd:
            author_anchors = authors_dd.find_all("a")  # Authors are in <a> tags
            for author_anchor in author_anchors:
                paper_info["authors"].append(author_anchor.get_text(strip=True))

        # --- Extract PDF, Supplemental, arXiv links and BibTeX ---
        # These are in the second <dd> following the <dt class="ptitle">
        # (which is the next sibling of authors_dd)
        links_bibtex_dd = authors_dd.find_next_sibling("dd") if authors_dd else None
        if links_bibtex_dd:
            # Extract links
            link_anchors = links_bibtex_dd.find_all("a")
            for link_anchor in link_anchors:
                link_text = link_anchor.get_text(strip=True).lower()
                link_href = link_anchor.get("href")
                if not link_href:
                    continue

                if link_text == "pdf":
                    paper_info["pdf_link"] = urljoin(base_url, link_href)
                elif link_text == "supp":
                    paper_info["supplemental_link"] = urljoin(base_url, link_href)
                elif link_text == "arxiv":
                    # arXiv links are usually absolute, but urljoin is safe
                    paper_info["arxiv_link"] = urljoin(base_url, link_href)

            # Extract BibTeX
            bibtex_div = links_bibtex_dd.find("div", class_="bibref")
            if bibtex_div:
                # Get text and strip leading/trailing whitespace, preserve newlines
                paper_info["bibtex"] = bibtex_div.get_text(strip=False).strip()

        papers_data.append(paper_info)
        print(f"  Extracted: {paper_info['title'][:50]}...")

    return papers_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape paper information from a CVF Open Access conference page.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--url-name",
        required=True,
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it exists, otherwise append (or create)."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for the HTTP request."
    )

    args = parser.parse_args()
    urls = {
        "wacv_2025": "http://openaccess.thecvf.com/WACV2025",
        "wacv_2024": "http://openaccess.thecvf.com/WACV2024",
        "wacv_2023": "http://openaccess.thecvf.com/WACV2023",
        "wacv_2022": "http://openaccess.thecvf.com/WACV2022",
        "wacv_2021": "http://openaccess.thecvf.com/WACV2021",
        "wacv_2020": "http://openaccess.thecvf.com/WACV2020",
        "cvpr_2024": "http://openaccess.thecvf.com/CVPR2024?day=all",
        "cvpr_2023": "http://openaccess.thecvf.com/CVPR2023?day=all",
        "cvpr_2022": "http://openaccess.thecvf.com/CVPR2022?day=all",
        "cvpr_2021": "http://openaccess.thecvf.com/CVPR2021?day=all",
        "cvpr_2020": "http://openaccess.thecvf.com/CVPR2020?day=all",
        "iccv_2023": "http://openaccess.thecvf.com/ICCV2023?day=all",
        "iccv_2021": "http://openaccess.thecvf.com/ICCV2021?day=all",
    }
    url = urls[args.url_name]
    TRIAL = 0
    output_file = (
        f"../../../data/rss_paper_data/cvf_papers.{args.url_name}.t{TRIAL}.jsonl"
    )

    print("CVF Open Access Scraper")
    print("--------------------------")
    print(f"Target URL: {url}")
    print(f"Output File: {output_file}")

    try:
        print("Fetching page content...")
        headers = {  # Mimic a browser a bit
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=args.timeout)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        print("Page content fetched successfully.")

        print("Parsing HTML and extracting paper information...")
        extracted_papers = extract_paper_info_from_cvf(response.text, url)

        if not extracted_papers:
            print("No papers found on the page or an issue occurred during parsing.")
        else:
            print(
                f"Successfully extracted information for "
                f"{len(extracted_papers)} papers."
            )

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

            with Path(output_file).open(file_mode, encoding="utf-8") as outfile:
                for paper_data in extracted_papers:
                    outfile.write(json.dumps(paper_data) + "\n")

            print(f"Data saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
    except (OSError, ValueError, KeyError) as e:
        print(f"An unexpected error occurred: {e}")

    print("--------------------------")
    print("Script finished.")
