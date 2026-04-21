'''
Script to get text of article from html or xml file into json file.

Usage:
    python article_to_json.py --data_dir /path/to/articles [--save_dir /path/to/output]
                              [--skip_extras] [--skip_abstract]

Requires the ELSEVIER_API_KEY environment variable for abstract retrieval:
    export ELSEVIER_API_KEY=your_key_here
'''

import json
import os
import re
import sys
import time
import argparse
from datetime import datetime

from bs4 import BeautifulSoup

import to_json
import add_abstract
import captions_extractor
import tables_extractor
import figure_downloader


# Publisher prefix mapping shared across routing helpers
_PUB_PREFIX = {
    "RSC":      "10.1039",
    "ACS":      "10.1021",
    "Nature":   "10.1038",
    "Science":  "10.1126",
    "Frontiers":"10.3389",
    "MDPI":     "10.3390",
    "Wiley":    "10.1002",
    "Springer": "10.1007",
    "TandF":    "10.1080",
    "Elsevier": "10.1016",
}
_PREFIX_TO_PUB = {v: k for k, v in _PUB_PREFIX.items()}


def _get_publisher(doi_filename):
    """Return publisher name from a DOI filename (e.g. '10.1016-j.foo.txt')."""
    return _PREFIX_TO_PUB.get(doi_filename[:7])


def _get_soup(content, publisher):
    """Parse article content with the correct BeautifulSoup parser for the publisher."""
    if publisher == "Elsevier":
        return BeautifulSoup(content, 'xml')
    if publisher == "Wiley" and content.startswith('<component xmlns'):
        return BeautifulSoup(content, 'xml')
    return BeautifulSoup(content, 'html.parser')


def _extract_figure_labels(figure_captions):
    """Extract figure/scheme labels (e.g. 'Figure 1', 'Fig. 2') from caption strings."""
    label_pattern = re.compile(r'^((?:Fig\.?|Figure|Scheme)\s+\d+)', re.IGNORECASE)
    labels = []
    for cap in figure_captions:
        m = label_pattern.match(cap)
        if m:
            labels.append(m.group(1))
    return labels


def _get_captions(soup, publisher):
    """Route to the correct publisher captions extractor. Returns structured caption list."""
    dispatch = {
        "ACS":      captions_extractor.acs_captions,
        "Frontiers":captions_extractor.acs_captions,   # same HTML pattern
        "RSC":      captions_extractor.rsc_captions,
        "MDPI":     captions_extractor.rsc_captions,   # same HTML pattern
        "Nature":   captions_extractor.springer_nature_captions,
        "Science":  captions_extractor.science_captions,
        "Wiley":    captions_extractor.wiley_captions,
        "Springer": captions_extractor.springer_nature_captions,
        "TandF":    captions_extractor.tandf_captions,
        "Elsevier": captions_extractor.elsevier_captions,
    }
    fn = dispatch.get(publisher)
    return fn(soup) if fn else []


def _get_tables(soup, publisher):
    """Route to the correct publisher table extractor. Returns list of table dicts."""
    dispatch = {
        "ACS":      tables_extractor.acs_table,
        "RSC":      tables_extractor.rsc_table,
        "Nature":   tables_extractor.nature_table,
        "Science":  tables_extractor.science_table,
        "MDPI":     tables_extractor.mdpi_table,
        "Wiley":    tables_extractor.wiley_table,
        "Springer": tables_extractor.springer_table,
        "TandF":    tables_extractor.tandf_table,
        "Elsevier": tables_extractor.elsevier_table,
    }
    fn = dispatch.get(publisher)
    return fn(soup) if fn else []


def _get_figure_urls(soup, publisher, figure_labels):
    """Route to the correct publisher figure URL extractor. Returns list of URLs."""
    dispatch = {
        "ACS":      figure_downloader.acs_figure,
        "RSC":      figure_downloader.rsc_figure,
        "Nature":   figure_downloader.springer_nature_figure,
        "Science":  figure_downloader.science_figure,
        "MDPI":     figure_downloader.mdpi_figure,
        "Wiley":    figure_downloader.wiley_figure,
        "Springer": figure_downloader.springer_nature_figure,   # same function per figure_downloader
        "TandF":    figure_downloader.tandf_figure,
        "Elsevier": figure_downloader.elsevier_figure,
    }
    fn = dispatch.get(publisher)
    if fn and figure_labels:
        return fn(soup, figure_labels)
    return []


def _augment_json(json_path, content, publisher, api_key=None,
                  skip_extras=False, skip_abstract=False):
    """
    Load a JSON file produced by article_extractor, add captions, tables,
    figure URLs, and abstract, then save back to the same path.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not skip_extras:
        soup = _get_soup(content, publisher)

        try:
            caption_results = _get_captions(soup, publisher)
            figure_captions = []
            table_captions = []
            for entry in caption_results:
                if entry.get("name") == "Figures":
                    figure_captions = entry.get("content", [])
                elif entry.get("name") == "Tables":
                    table_captions = entry.get("content", [])
            data["Figure_captions"] = figure_captions
            data["Table_captions"] = table_captions
        except Exception as e:
            print(f"  Warning: captions extraction failed: {e}")
            data.setdefault("Figure_captions", [])
            data.setdefault("Table_captions", [])

        try:
            data["Tables"] = _get_tables(soup, publisher)
        except Exception as e:
            print(f"  Warning: tables extraction failed: {e}")
            data.setdefault("Tables", [])

        try:
            figure_labels = _extract_figure_labels(data.get("Figure_captions", []))
            data["Figure_urls"] = _get_figure_urls(soup, publisher, figure_labels)
        except Exception as e:
            print(f"  Warning: figure URL extraction failed: {e}")
            data.setdefault("Figure_urls", [])

    if not skip_abstract and api_key:
        doi_str = data.get("DOI", "")
        try:
            xml_content = add_abstract.abstract_retrieve(doi_str, api_key)
            data["Abstract"] = add_abstract.extract_abstract(xml_content)
        except Exception as e:
            print(f"  Warning: abstract retrieval failed for {doi_str}: {e}")
            data.setdefault("Abstract", "")
        time.sleep(1)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description='Extract article text from HTML/XML files and save as JSON'
    )
    parser.add_argument(
        '--data_dir', required=True,
        help='Directory containing the article .txt files'
    )
    parser.add_argument(
        '--save_dir', default=None,
        help='Directory to save extracted JSON files (default: <data_dir>/../extracted_json)'
    )
    parser.add_argument(
        '--skip_extras', action='store_true',
        help='Skip captions, tables, and figure URL extraction'
    )
    parser.add_argument(
        '--skip_abstract', action='store_true',
        help='Skip abstract retrieval from the Scopus API'
    )
    args = parser.parse_args()

    data_dir = args.data_dir
    save_dir = args.save_dir

    elsevier_api_key = os.environ.get('ELSEVIER_API_KEY')
    if not args.skip_abstract and not elsevier_api_key:
        print("Warning: ELSEVIER_API_KEY not set — abstract retrieval will be skipped.")
        args.skip_abstract = True

    if not os.path.exists(data_dir):
        print(f"Error: Data directory '{data_dir}' does not exist.")
        sys.exit(1)

    if save_dir is None:
        parent_dir = os.path.dirname(os.path.abspath(data_dir))
        save_dir = os.path.join(parent_dir, 'extracted_json')

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"Created save directory: {save_dir}")

    # Set up logging — tee stdout to both console and a timestamped log file
    parent_dir = os.path.dirname(os.path.abspath(data_dir))
    log_filename = f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    log_path = os.path.join(parent_dir, log_filename)
    log_file = open(log_path, 'w')

    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, data):
            for s in self.streams:
                s.write(data)
        def flush(self):
            for s in self.streams:
                s.flush()

    original_stdout = sys.stdout
    sys.stdout = Tee(original_stdout, log_file)

    print(f"Processing files from: {data_dir}")
    print(f"Saving JSON files to:  {save_dir}")
    print(f"Log file:              {log_path}")
    if not args.skip_extras:
        print("Extras:    captions, tables, and figure URLs will be extracted")
    if not args.skip_abstract:
        print("Abstract:  will be retrieved from the Scopus API (1 s delay per article)")
    print("-" * 80)

    pattern = re.compile(r'^10\.\d{4,9}[^\s]*\.txt$')
    matching_files = [f for f in os.listdir(data_dir) if pattern.match(f)]

    print(f"Found {len(matching_files)} matching files")
    print("-" * 80)

    if not matching_files:
        print("No matching files found. Please check the directory.")
        print("Expected pattern: 10.{4-9 digits}[any characters].txt")
        sys.stdout = original_stdout
        log_file.close()
        print(f"Log file created: {log_path}")
        return

    failed_files = []
    successful_count = 0

    for filename in matching_files:
        try:
            print(f"Processing: {filename}")
            success = to_json.article_extractor(filename, data_dir, save_dir)
            if success:
                successful_count += 1
                json_path = os.path.join(save_dir, filename.replace('.txt', '.json'))
                publisher = _get_publisher(filename)
                with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                    content = f.read()
                _augment_json(
                    json_path, content, publisher,
                    api_key=elsevier_api_key,
                    skip_extras=args.skip_extras,
                    skip_abstract=args.skip_abstract,
                )
            else:
                failed_files.append(filename)
        except Exception as e:
            print(f"FAILED: {filename} - Error: {str(e)}")
            failed_files.append(filename)

    print("-" * 80)
    print(f"Processing complete!")
    print(f"Total files processed: {len(matching_files)}")
    print(f"Successful:            {successful_count}")
    print(f"Failed:                {len(failed_files)}")

    if failed_files:
        print("\nFailed files:")
        for f in failed_files:
            print(f"  - {f}")

    sys.stdout = original_stdout
    log_file.close()
    print(f"Processing complete. Log file created: {log_path}")
    print(f"Processed {successful_count}/{len(matching_files)} files successfully")
    if failed_files:
        print(f"Failed: {len(failed_files)}")


if __name__ == '__main__':
    main()
