# bibtex_to_jsonl_parser.py
# This script parses a BibTeX file (can be gzipped), extracts information
# from each entry, and saves it as a JSON line in an output file.
# Designed with ACL Anthology's "anthology+abstracts.bib.gz" in mind.

import argparse
import gzip
import json
import shutil
from pathlib import Path
from typing import Any

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import homogenize_latex_encoding, latex_to_unicode


class BibtexParsingError(Exception):
    """Exception raised when BibTeX parsing fails."""

    def __init__(self, message: str = "Simple mode parsing failed") -> None:
        super().__init__(message)


class BibtexInputError(TypeError):
    """Exception raised for invalid input types."""

    def __init__(self, input_path: str, input_type: type) -> None:
        super().__init__(
            f"Input file path for gzipped file must be a string, "
            f"but got {input_type}. Value: {input_path}"
        )


def preprocess_bibtex_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Apply standard customizations to a BibTeX entry.

    Converts LaTeX to Unicode. This function is used by the 'default' parser
    mode via parser.customization and also called manually in the 'simple'
    mode after initial parsing.

    Args:
        entry: A BibTeX entry dictionary.

    Returns:
        The processed entry dictionary.
    """
    # Ensure entry is a dict, which it should be from bibtexparser
    if not isinstance(entry, dict):
        # This case should ideally not be hit if bibtexparser works as expected
        print(f"Warning: preprocess_bibtex_entry received non-dict type: {type(entry)}")
        return entry

    # These functions expect a dictionary (the entry) and modify it or return
    # a modified version.
    entry = homogenize_latex_encoding(entry)
    return latex_to_unicode(entry)


def extract_info_from_bib_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant information from a single BibTeX entry dictionary."""
    return {
        "id": entry.get("ID"),  # Note: keys might be lowercase after homogenization
        "entry_type": entry.get("ENTRYTYPE"),
        "title": entry.get("title"),
        "author": entry.get("author"),
        "authors_list": (
            [author.strip() for author in entry.get("author", "").split(" and ")]
            if entry.get("author") and isinstance(entry.get("author"), str)
            else []
        ),
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
        "bibtex_entry_raw": entry,  # Contains entry after parsing and customizations
    }


def _handle_gzipped_file(input_path: str) -> str:
    """Handle decompression of gzipped BibTeX file.

    Args:
        input_path: Path to the gzipped file.

    Returns:
        Path to the decompressed temporary file.

    Raises:
        TypeError: If input_path is not a string.
    """
    if not isinstance(input_path, str):
        raise BibtexInputError(input_path, type(input_path))

    print(f"Input file '{input_path}' is gzipped. Decompressing temporarily...")
    temp_path = input_path.replace(".gz", "") + "_temp.bib"

    temp_path_obj = Path(temp_path)
    if temp_path_obj.exists():
        temp_path_obj.unlink()

    with gzip.open(input_path, "rb") as f_in, Path(temp_path).open("wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    print(f"Decompressed to: {temp_path}")
    return temp_path


def _parse_with_simple_mode(content: str) -> BibDatabase:
    """Parse BibTeX content using simple parser mode.

    Args:
        content: The BibTeX file content as string.

    Returns:
        Parsed BibTeX database object.

    Raises:
        RuntimeError: If parsing fails even in simple mode.
    """
    print("Using 'simple' parser mode (minimal settings for initial load).")

    parser = BibTexParser(
        common_strings=True,
        ignore_nonstandard_types=True,  # Be lenient with @type names
        homogenize_fields=False  # Do not change field keys during initial parse
    )

    try:
        bib_database = bibtexparser.loads(content, parser=parser)
    except Exception as e_load:
        print(f"CRITICAL ERROR during bibtexparser.loads() in 'simple' mode: {e_load}")
        print("This suggests a fundamental parsing issue with an entry's syntax.")
        print("Consider validating the BibTeX file or identify problematic entries.")
        raise BibtexParsingError from e_load

    if not bib_database or not bib_database.entries:
        return bib_database

    print("Initial parsing successful. Now applying customizations entry by entry...")
    customized_entries = []

    for entry_idx, original_entry in enumerate(bib_database.entries):
        current_entry = dict(original_entry)
        try:
            # Homogenize field keys to lowercase manually
            current_entry = {k.lower(): v for k, v in current_entry.items()}
            # Apply standard BibTeX customizations
            current_entry = preprocess_bibtex_entry(current_entry)
            customized_entries.append(current_entry)
        except AttributeError as e_attr:
            _handle_entry_error(original_entry, entry_idx, e_attr, "AttributeError")
            customized_entries.append({k.lower(): v for k, v in original_entry.items()})
        except (KeyError, ValueError, UnicodeDecodeError) as e_custom:
            _handle_entry_error(original_entry, entry_idx, e_custom, "General error")
            customized_entries.append({k.lower(): v for k, v in original_entry.items()})

    bib_database.entries = customized_entries
    return bib_database


def _parse_with_default_mode(content: str) -> BibDatabase:
    """Parse BibTeX content using default parser mode.

    Args:
        content: The BibTeX file content as string.

    Returns:
        Parsed BibTeX database object.
    """
    print("Using 'default' parser mode.")
    parser = BibTexParser(common_strings=True)
    parser.customization = preprocess_bibtex_entry
    parser.ignore_nonstandard_types = False
    parser.homogenize_fields = True  # Field keys will be lowercased by parser
    return bibtexparser.loads(content, parser=parser)


def _handle_entry_error(
    original_entry: dict[str, Any],
    entry_idx: int,
    error: Exception,
    error_type: str
) -> None:
    """Handle errors that occur during entry processing.

    Args:
        original_entry: The problematic entry.
        entry_idx: Index of the entry.
        error: The exception that occurred.
        error_type: Type of error for logging.
    """
    problematic_id_dict = {k.lower(): v for k, v in original_entry.items()}
    problematic_id = problematic_id_dict.get("id", original_entry.get("ID", "N/A"))
    print(f"WARNING: {error_type} during customization of entry "
          f"ID '{problematic_id}' (index {entry_idx}): {error}")
    if error_type == "AttributeError":
        print(f"  Problematic entry data (before error): {original_entry}")


def _write_entries_to_jsonl(
    entries: list[dict[str, Any]],
    output_path: str,
    parser_mode: str,
    parser: BibTexParser,
    overwrite_flag: bool
) -> int:
    """Write processed entries to JSONL file.

    Args:
        entries: List of processed BibTeX entries.
        output_path: Path to output JSONL file.
        parser_mode: The parser mode used.
        parser: The parser object.
        overwrite_flag: Whether to overwrite existing file.

    Returns:
        Number of successfully written entries.
    """
    count = 0
    current_file_mode = "w" if overwrite_flag else "a"

    if not Path(output_path).exists():
        current_file_mode = "w"

    with Path(output_path).open(current_file_mode, encoding="utf-8") as outfile:
        for entry_idx, entry in enumerate(entries):
            try:
                # Ensure keys are lowercase for extract_info_from_bib_entry
                if (parser_mode == "simple" and
                    not getattr(parser, "homogenize_fields", False)):
                    normalized_entry = {k.lower(): v for k, v in entry.items()}
                else:
                    normalized_entry = entry

                paper_info = extract_info_from_bib_entry(normalized_entry)
                outfile.write(json.dumps(paper_info) + "\n")
                count += 1

                if count % 1000 == 0:
                    print(f"  Processed {count} entries...")

            except (KeyError, TypeError, ValueError, OSError) as e:
                problematic_id = "N/A"
                if isinstance(entry, dict):
                    problematic_id = entry.get("id", entry.get("ID", "N/A"))
                print(f"Error writing entry ID '{problematic_id}' "
                      f"(index {entry_idx}) to JSON: {e}")

    return count


def process_bibtex_file(
    input_bib_path: str,
    output_jsonl_path: str,
    is_gzipped: bool,
    parser_mode: str,
    overwrite_flag: bool
) -> int:
    """Read a BibTeX file, process entries, and write to JSONL.

    Args:
        input_bib_path: Path to input BibTeX file.
        output_jsonl_path: Path to output JSONL file.
        is_gzipped: Whether input file is gzipped.
        parser_mode: Parser mode ('simple' or 'default').
        overwrite_flag: Whether to overwrite existing output file.

    Returns:
        Number of successfully processed entries.
    """
    temp_decompressed_path: str | None = None

    try:
        # Handle gzipped files
        actual_bib_path = input_bib_path
        if is_gzipped:
            temp_decompressed_path = _handle_gzipped_file(input_bib_path)
            actual_bib_path = temp_decompressed_path

        print(f"Parsing BibTeX file: {actual_bib_path} (Mode: {parser_mode})")

        # Read file content
        with Path(actual_bib_path).open(encoding="utf-8") as bibtex_file:
            bib_content_str = bibtex_file.read()

        # Parse based on mode
        if parser_mode == "simple":
            bib_database = _parse_with_simple_mode(bib_content_str)
        else:  # Default mode
            bib_database = _parse_with_default_mode(bib_content_str)

        if not bib_database or not bib_database.entries:
            print(
                "No entries found in the BibTeX file after parsing and customization."
            )
            return 0

        print(f"Found {len(bib_database.entries)} entries. "
              f"Processing and writing to {output_jsonl_path}...")

        # Write entries to JSONL
        parser = BibTexParser()  # Create parser object for _write_entries_to_jsonl
        count = _write_entries_to_jsonl(
            bib_database.entries,
            output_jsonl_path,
            parser_mode,
            parser,
            overwrite_flag
        )

        print(
f"\nSuccessfully processed and wrote {count} entries to "
            f"{output_jsonl_path}."
        )
    except FileNotFoundError:
        print(f"Error: Input file '{input_bib_path}' not found.")
        return 0
    except TypeError as e:
        print(f"Configuration or Type Error: {e}")
        return 0
    except (OSError, MemoryError) as e:
        print(f"An unexpected error occurred: {e}")
        return 0
    finally:
        if temp_decompressed_path and Path(temp_decompressed_path).exists():
            print(f"Cleaning up temporary file: {temp_decompressed_path}")
            Path(temp_decompressed_path).unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Parse a BibTeX file (gzipped or plain) and output entries to a JSONL file."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
"Overwrite the output file if it exists, otherwise append "
            "(or create if new)."
        )
    )

    args = parser.parse_args()
    input_file = "../../../data/rss_paper_data/anthology+abstracts.bib"
    output_file = "../../../data/rss_paper_data/acl_papers_w_abstracts.t0.jsonl"

    print("BibTeX to JSONL Parser")
    print("----------------------")
    print(f"Input BibTeX File: {input_file}")
    print(f"Output JSONL File: {output_file}")

    is_gzipped_input = False

    if not args.overwrite and Path(output_file).exists():
        print(
            f"Output file '{output_file}' already exists. "
            "Appending. Use --overwrite to overwrite."
        )
    elif args.overwrite and Path(output_file).exists():
        print(f"Output file '{output_file}' will be overwritten.")
    else:
        print(f"Creating new output file '{output_file}'.")

    process_bibtex_file(
        input_file, output_file, is_gzipped_input, "simple", overwrite_flag=False
    )

    print("----------------------")
    print("Script finished.")
