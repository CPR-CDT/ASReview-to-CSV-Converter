#!/usr/bin/env python3
"""Convert ASReview project files (.asreview) to CSV.

Usage:
    python asreview_to_csv.py project.asreview [more.asreview ...] [-o out.csv]

With one input and no -o, writes <project>.csv next to the input.
With several inputs, -o (if given) must be a directory.

Only the Python standard library is needed. Works with ASReview v2/v3
project files (those containing results.db with a `record` table).
"""
import argparse
import csv
import json
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

LABELS = {1: "included", 0: "excluded", None: "unlabelled"}

QUERY = """
SELECT r.record_id, r.title, r.abstract, r.authors, r.keywords, r.year,
       r.doi, r.url, r.duplicate_of,
       res.label, res.user_id, res.time, res.querier, res.classifier,
       res.training_set, res.note, res.tags, lr.ranking
FROM record r
LEFT JOIN results res ON res.record_id = r.record_id
LEFT JOIN last_ranking lr ON lr.record_id = r.record_id
ORDER BY res.time IS NULL, res.time, lr.ranking, r.record_id
"""

COLUMNS = ["screening_order", "record_id", "title", "abstract", "authors",
           "keywords", "year", "doi", "url", "duplicate_of", "label",
           "decision", "user_id", "labelled_at_utc", "querier", "classifier",
           "training_set", "note", "tags", "last_ranking"]


def _join_json(value):
    """JSON list -> '; '-separated string; passes other values through."""
    if not value:
        return ""
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return value
    return "; ".join(map(str, parsed)) if isinstance(parsed, list) else str(parsed)


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds") if ts else ""


def convert(src: Path, dst: Path) -> int:
    with zipfile.ZipFile(src) as zf, tempfile.TemporaryDirectory() as tmp:
        if "results.db" not in zf.namelist():
            raise ValueError(f"{src}: no results.db found (ASReview v1 project?)")
        db = Path(zf.extract("results.db", tmp))
        con = sqlite3.connect(db)
        tables = {t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "record" not in tables:
            raise ValueError(f"{src}: results.db has no `record` table (unsupported version)")
        query = QUERY if "last_ranking" in tables else \
            QUERY.replace("LEFT JOIN last_ranking lr ON lr.record_id = r.record_id", "") \
                 .replace("lr.ranking", "NULL")
        rows = con.execute(query).fetchall()
        con.close()

    with open(dst, "w", newline="", encoding="utf-8-sig") as f:  # BOM: Excel-friendly
        w = csv.writer(f)
        w.writerow(COLUMNS)
        order = 0
        for (rid, title, abstract, authors, keywords, year, doi, url, dup,
             label, user, ts, querier, clf, train, note, tags, rank) in rows:
            labelled = label is not None
            order += labelled
            w.writerow([order if labelled else "", rid, title, abstract,
                        _join_json(authors), _join_json(keywords), year, doi, url,
                        dup, label, LABELS.get(label, label), user, _iso(ts),
                        querier, clf, train, note, _join_json(tags), rank])
    return len(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("inputs", nargs="+", type=Path, help=".asreview file(s)")
    p.add_argument("-o", "--output", type=Path, help="output .csv (one input) or directory")
    a = p.parse_args(argv)

    if len(a.inputs) > 1 and a.output and a.output.suffix:
        p.error("with several inputs, -o must be a directory")

    for src in a.inputs:
        if a.output is None:
            dst = src.with_suffix(".csv")
        elif a.output.suffix:
            dst = a.output
        else:
            a.output.mkdir(parents=True, exist_ok=True)
            dst = a.output / f"{src.stem}.csv"
        try:
            n = convert(src, dst)
        except (ValueError, zipfile.BadZipFile, sqlite3.Error) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"{src} -> {dst} ({n} records)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
