# ASReview-to-CSV-Converter
Python script to convert .asreview files to .csv files

# asreview_to_csv
 
Converts ASReview project files (`.asreview`) into a CSV with one row per record, including screening decisions.
 
## Requirements
 
- Python 3.8 or newer
- No extra packages (standard library only)
- ASReview project files from version 2 or 3 (files containing `results.db`). Version 1 projects are rejected with an error.
## Usage
 
Run from a terminal in the folder containing the script:
 
```bash
# One project -> CSV next to it (same name, .csv)
python3 asreview_to_csv.py "Rian IRR 100.asreview"
 
# Choose the output file
python3 asreview_to_csv.py "Rian IRR 100.asreview" -o screening.csv
 
# Several projects -> one CSV each in a folder
python3 asreview_to_csv.py a.asreview b.asreview -o exports/
```
 
Put file names that contain spaces in quotes, or drag the file into the terminal window. On Windows, use `python` or `py` instead of `python3`.
 
On success the script prints `input -> output (N records)`.
 
## Output columns
 
| Column | Description |
|---|---|
| `screening_order` | Order in which the record was labelled (1 = first). Empty if unlabelled. |
| `record_id` | ASReview's internal record ID |
| `title`, `abstract` | From the imported dataset |
| `authors`, `keywords` | Separated by `; ` |
| `year`, `doi`, `url` | From the imported dataset |
| `duplicate_of` | `record_id` of the original if ASReview marked this record as a duplicate |
| `label` | `1` = included, `0` = excluded, empty = unlabelled |
| `decision` | `included` / `excluded` / `unlabelled` |
| `user_id` | ASReview user who labelled the record |
| `labelled_at_utc` | Time of the decision (ISO 8601, UTC) |
| `querier`, `classifier`, `training_set` | How ASReview selected the record (e.g. `random` during the prior phase) |
| `note`, `tags` | Reviewer notes and tags |
| `last_ranking` | Position in ASReview's most recent relevance ranking |
 
Rows are sorted by labelling time. Unlabelled records come last, ordered by ranking.
 
The file is UTF-8 with a byte-order mark, so Excel and Numbers display accented characters correctly.
 
## Notes
 
- Only the final decision per record is exported. Earlier changed decisions, which ASReview keeps in its `decision_changes` table, are not included.
- The `.asreview` file is only read, never modified.
## Troubleshooting
 
| Error | Fix |
|---|---|
| `the following arguments are required: inputs` | Add the `.asreview` file name after the script name. |
| `No such file or directory` | The name or path is wrong. Run `ls *.asreview` (macOS/Linux) or `dir *.asreview` (Windows) to see the exact name, and use quotes if it contains spaces. |
| `no results.db found` | The project is from ASReview v1. Open it in a current ASReview version and export it again. |
| `python3: command not found` | Install Python from python.org. |
 
