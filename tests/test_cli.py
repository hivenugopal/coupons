import csv

from couponfinder.cli import CSV_FIELDNAMES, _load_config, _write_csv


def test_load_config_parses_quoted_key_value_lines(tmp_path):
    config_path = tmp_path / "config.ini"
    config_path.write_text(
        'input-file="C:\\data\\urls.txt"\n'
        'output-file="C:\\data\\results.csv"\n'
        "# a comment\n"
        "\n",
        encoding="utf-8",
    )
    config = _load_config(str(config_path))
    assert config["input-file"] == "C:\\data\\urls.txt"
    assert config["output-file"] == "C:\\data\\results.csv"


def test_load_config_returns_empty_dict_when_file_missing(tmp_path):
    assert _load_config(str(tmp_path / "missing.ini")) == {}


def test_write_csv_uses_pipe_delimiter(tmp_path):
    out_path = tmp_path / "results.csv"
    row = {field: field for field in CSV_FIELDNAMES}
    _write_csv(str(out_path), [row])

    content = out_path.read_text(encoding="utf-8")
    assert content.splitlines()[0] == "|".join(CSV_FIELDNAMES)

    with open(out_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        rows = list(reader)
    assert rows == [row]


def test_write_csv_appends_to_existing_file_without_duplicating_header(tmp_path):
    out_path = tmp_path / "results.csv"
    row1 = {field: f"{field}-1" for field in CSV_FIELDNAMES}
    row2 = {field: f"{field}-2" for field in CSV_FIELDNAMES}

    _write_csv(str(out_path), [row1])
    _write_csv(str(out_path), [row2])

    lines = out_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "|".join(CSV_FIELDNAMES)
    assert lines.count("|".join(CSV_FIELDNAMES)) == 1

    with open(out_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")
        rows = list(reader)
    assert rows == [row1, row2]
