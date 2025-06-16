# bibtex_to_jsonl_parser.py
# This script parses a BibTeX file (can be gzipped), extracts information
# from each entry, and saves it as a JSON line in an output file.
# Designed with ACL Anthology's "anthology+abstracts.bib.gz" in mind.

import argparse
import gzip
import json
import os
import shutil

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding, latex_to_unicode


def preprocess_bibtex_entry(entry):
    """Apply standard customizations to a BibTeX entry.
    Converts LaTeX to Unicode.
    This function is used by the 'default' parser mode via parser.customization
    and also called manually in the 'simple' mode after initial parsing.
    """
    # Ensure entry is a dict, which it should be from bibtexparser
    if not isinstance(entry, dict):
        # This case should ideally not be hit if bibtexparser works as expected
        print(f"Warning: preprocess_bibtex_entry received non-dict type: {type(entry)}")
        return entry

    # These functions expect a dictionary (the entry) and modify it or return a modified version.
    entry = homogenize_latex_encoding(entry)
    entry = latex_to_unicode(entry)
    return entry

def extract_info_from_bib_entry(entry):
    """Extracts relevant information from a single BibTeX entry dictionary.
    """
    return {
        "id": entry.get("ID"), # Note: keys might be lowercase after homogenization
        "entry_type": entry.get("ENTRYTYPE"),
        "title": entry.get("title"),
        "author": entry.get("author"),
        "authors_list": [author.strip() for author in entry.get("author", "").split(" and ")] if entry.get("author") and isinstance(entry.get("author"), str) else [],
        "abstract": entry.get("abstract"),
        "year": entry.get("year"),
        "month": entry.get("month"),
        "booktitle": entry.get("booktitle"),
        "journal": entry.get("journal"),
        "volume": entry.get("volume"),
        "number": entry.get("number"),
        "pages": entry.get("pages"),
        "url": entry.get("url"),
        "doi": entry.get("doi"),
        "publisher": entry.get("publisher"),
        "address": entry.get("address"),
        "editor": entry.get("editor"),
        "bibtex_entry_raw": entry # Contains the entry after parsing and any customizations
    }

def process_bibtex_file(input_bib_path, output_jsonl_path, is_gzipped, parser_mode, overwrite_flag):
    """Reads a BibTeX file, processes entries, and writes to JSONL.
    """
    bib_database = None
    temp_decompressed_path = None

    try:
        actual_bib_path_to_parse = input_bib_path
        if is_gzipped:
            if not isinstance(input_bib_path, str):
                raise TypeError(
                    f"Input file path for gzipped file must be a string, but got {type(input_bib_path)}. Value: {input_bib_path}"
                )
            print(f"Input file '{input_bib_path}' is gzipped. Decompressing temporarily...")
            temp_decompressed_path = input_bib_path.replace(".gz", "") + "_temp.bib"
            if os.path.exists(temp_decompressed_path):
                os.remove(temp_decompressed_path)
            with gzip.open(input_bib_path, "rb") as f_in:
                with open(temp_decompressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            actual_bib_path_to_parse = temp_decompressed_path
            print(f"Decompressed to: {actual_bib_path_to_parse}")

        print(f"Parsing BibTeX file: {actual_bib_path_to_parse} (Mode: {parser_mode})")

        bib_content_str = ""
        with open(actual_bib_path_to_parse, encoding="utf-8") as bibtex_file:
            bib_content_str = bibtex_file.read()

        if parser_mode == "simple":
            print("Using 'simple' parser mode (minimal settings for initial load).")
            # Simplest possible parser for the initial .loads() call.
            # No parser.customization is set here for the .loads() step.
            parser = BibTexParser(
                common_strings=True,
                ignore_nonstandard_types=True, # Be lenient with @type names
                homogenize_fields=False # Do not change field keys during initial parse
            )
            try:
                bib_database = bibtexparser.loads(bib_content_str, parser=parser)
            except Exception as e_load:
                print(f"CRITICAL ERROR during bibtexparser.loads() in 'simple' mode: {e_load}")
                print("This suggests a fundamental parsing issue with an entry's syntax that even the simplest parser mode could not handle.")
                print("Consider trying to validate the BibTeX file or identify problematic entries manually.")
                return 0 # Abort if even the simplest load fails

            if bib_database and bib_database.entries:
                print("Initial parsing successful with simple mode. Now applying customizations entry by entry...")
                customized_entries = []
                for entry_idx, original_entry in enumerate(bib_database.entries):
                    # Work on a copy to avoid modifying the list being iterated over if not careful
                    current_entry = dict(original_entry)
                    try:
                        # 1. Homogenize field keys to lowercase manually
                        # This ensures consistency before other steps and for extract_info_from_bib_entry
                        current_entry = {k.lower(): v for k, v in current_entry.items()}

                        # 2. Apply standard BibTeX customizations (homogenize_latex_encoding, latex_to_unicode)
                        # These are applied to the dictionary representing the current entry.
                        current_entry = preprocess_bibtex_entry(current_entry)

                        customized_entries.append(current_entry)
                    except AttributeError as e_attr:
                        # Try to get ID from lowercased keys if available, else from original
                        problematic_id_dict = {k.lower(): v for k, v in original_entry.items()}
                        problematic_id = problematic_id_dict.get("id", original_entry.get("ID", "N/A"))
                        print(f"WARNING: AttributeError during manual customization of entry ID '{problematic_id}' (index {entry_idx}): {e_attr}")
                        print(f"  Problematic entry data (original, before error): {original_entry}")
                        customized_entries.append({k.lower(): v for k, v in original_entry.items()}) # Add original (with lowercased keys) if customization fails
                    except Exception as e_custom:
                        problematic_id_dict = {k.lower(): v for k, v in original_entry.items()}
                        problematic_id = problematic_id_dict.get("id", original_entry.get("ID", "N/A"))
                        print(f"WARNING: General error during manual customization of entry ID '{problematic_id}' (index {entry_idx}): {e_custom}")
                        customized_entries.append({k.lower(): v for k, v in original_entry.items()}) # Add original (with lowercased keys)
                bib_database.entries = customized_entries
        else: # Default mode
            print("Using 'default' parser mode.")
            parser = BibTexParser(common_strings=True)
            parser.customization = preprocess_bibtex_entry # This will be called for each entry by .loads()
            parser.ignore_nonstandard_types = False
            parser.homogenize_fields = True # Field keys will be lowercased by the parser
            bib_database = bibtexparser.loads(bib_content_str, parser=parser)

        if not bib_database or not bib_database.entries:
            print("No entries found in the BibTeX file after parsing and customization.")
            return 0

        print(f"Found {len(bib_database.entries)} entries. Processing and writing to {output_jsonl_path}...")

        count = 0
        current_file_mode = "w" if overwrite_flag else "a"
        # If appending but file doesn't exist, 'a' mode will create it, so 'w' is only for explicit overwrite.
        if not os.path.exists(output_jsonl_path): # If file doesn't exist, 'a' acts like 'w' for creation
            current_file_mode = "w"


        with open(output_jsonl_path, current_file_mode, encoding="utf-8") as outfile:
            for entry_idx, entry in enumerate(bib_database.entries): # Use enumerate for better error reporting
                try:
                    # Ensure keys are lowercase for extract_info_from_bib_entry if not already done by parser
                    # (homogenize_fields=True in default, manual in simple)
                    normalized_entry = {k.lower(): v for k,v in entry.items()} if parser_mode == "simple" and not getattr(parser, "homogenize_fields", False) else entry

                    paper_info = extract_info_from_bib_entry(normalized_entry)
                    outfile.write(json.dumps(paper_info) + "\n")
                    count += 1
                    if count % 1000 == 0:
                        print(f"  Processed {count} entries...")
                except Exception as e:
                    problematic_id = "N/A"
                    if isinstance(entry, dict): # entry should be a dict
                        problematic_id = entry.get("id", entry.get("ID", "N/A")) # Check both cases
                    print(f"Error writing entry ID '{problematic_id}' (index {entry_idx}) to JSON: {e}")
                    # print(f"  Problematic entry data being written: {paper_info}") # Careful, paper_info might be partial

        print(f"\nSuccessfully processed and wrote {count} entries to {output_jsonl_path}.")
        return count

    except FileNotFoundError:
        print(f"Error: Input file '{input_bib_path}' not found.")
        return 0
    except TypeError as e: # Catch the TypeError we might raise from input_bib_path check
        print(f"Configuration or Type Error: {e}")
        return 0
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0
    finally:
        if temp_decompressed_path and os.path.exists(temp_decompressed_path):
            print(f"Cleaning up temporary file: {temp_decompressed_path}")
            os.remove(temp_decompressed_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse a BibTeX file (gzipped or plain) and output entries to a JSONL file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it exists, otherwise append (or create if new)."
    )

    args = parser.parse_args()
    input_file = "../../../data/rss_paper_data/anthology+abstracts.bib"
    output_file = "../../../data/rss_paper_data/acl_papers_w_abstracts.t0.jsonl"

    print("BibTeX to JSONL Parser")
    print("----------------------")
    print(f"Input BibTeX File: {input_file}")
    print(f"Output JSONL File: {output_file}")

    #is_gzipped_input = input_file.endswith('.gz')
    is_gzipped_input = False

    if not args.overwrite and os.path.exists(output_file):
        print(f"Output file '{output_file}' already exists. Appending. Use --overwrite to overwrite.")
    elif args.overwrite and os.path.exists(output_file):
         print(f"Output file '{output_file}' will be overwritten.")
    else:
        print(f"Creating new output file '{output_file}'.")


    process_bibtex_file(input_file, output_file, is_gzipped_input, "simple", False)


    print("----------------------")
    print("Script finished.")
