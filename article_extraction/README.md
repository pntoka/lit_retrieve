# article_extraction

Parses downloaded article HTML/XML files and extracts structured content into JSON. Also includes utilities for converting JSON to Markdown and for keyword-based section extraction.

## Scripts

| Script | Purpose |
|---|---|
| `article_to_json.py` | Main entry point — extract all articles in a directory to JSON |
| `json_to_md.py` | Convert JSON files to Markdown |
| `json_section_extract.py` | Extract sections matching keywords from JSON files |

## Usage

### Extract articles to JSON

```bash
python article_to_json.py \
    --data_dir /path/to/articles/ \
    --save_dir /path/to/json_output/
```

Processes all files matching the pattern `10.XXXX*.txt`. Requires `ELSEVIER_API_KEY`
for abstract retrieval (skipped automatically with a warning if not set).

**Options:**

| Flag | Description |
|---|---|
| `--skip_extras` | Skip captions, tables, and figure URL extraction |
| `--skip_abstract` | Skip abstract retrieval from the Scopus API |

A timestamped log file (`extraction_log_YYYYMMDD_HHMM.txt`) is written to the parent directory of `--data_dir`.

### Convert JSON to Markdown

```bash
python json_to_md.py \
    --data_dir /path/to/json_output/ \
    --save_dir /path/to/markdown/
```

**Options:**

| Flag | Description |
|---|---|
| `--include_captions` | Append `## Figure Captions` and `## Table Captions` sections to each article |

### Extract keyword-matched sections

```bash
python json_section_extract.py \
    --data_dir /path/to/json_output/ \
    --save_dir /path/to/sections/ \
    --keywords experimental methods
```

Returns only the sections whose headings contain any of the given keywords (case-insensitive).

## Module overview

| File | Description |
|---|---|
| `to_json.py` | Publisher-specific HTML/XML → JSON extraction functions |
| `section_extractor.py` | Publisher-specific section parsing |
| `extractor_tools.py` | Shared helpers: tag removal, paragraph finding, `create_json_data` |
| `add_abstract.py` | Scopus API abstract retrieval |
| `captions_extractor.py` | Figure and table caption extraction |
| `tables_extractor.py` | Table HTML extraction |
| `figure_downloader.py` | Figure URL extraction and download |
| `doi_tools.py` | DOI ↔ filename conversion utilities |

