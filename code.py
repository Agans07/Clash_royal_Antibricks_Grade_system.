"""Print a points-based grade chart for the current clan roster."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROSTER_COLUMNS = {"tag", "name", "donations", "trophies"}
PARTICIPATION_COLUMNS = {
    "player_tag",
    "player_name",
    "player_participation_ratio",
}


@dataclass(frozen=True)
class PlayerScore:
    name: str
    tag: str
    participation_ratio: float
    donations: int
    trophies: int

    @property
    def participation_points(self) -> float:
        return self.participation_ratio * 10

    @property
    def donation_points(self) -> int:
        return self.donations // 100

    @property
    def trophy_points(self) -> int:
        return self.trophies // 1000

    @property
    def total_points(self) -> float:
        return (
            self.participation_points
            + self.donation_points
            + self.trophy_points
        )


def normalize_tag(tag: str) -> str:
    return tag.strip().lstrip("#").upper()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} has no header row.")
        return list(reader)


def find_input_files(directory: Path) -> tuple[Path, Path]:
    roster_files: list[Path] = []
    participation_files: list[Path] = []

    for path in directory.glob("*.csv"):
        with path.open(encoding="utf-8-sig", newline="") as csv_file:
            header = set(next(csv.reader(csv_file), []))

        if ROSTER_COLUMNS.issubset(header):
            roster_files.append(path)
        if PARTICIPATION_COLUMNS.issubset(header):
            participation_files.append(path)

    if len(roster_files) != 1 or len(participation_files) != 1:
        raise ValueError(
            "Expected exactly one roster CSV and one participation CSV in "
            f"{directory}. Found {len(roster_files)} roster file(s) and "
            f"{len(participation_files)} participation file(s)."
        )

    return roster_files[0], participation_files[0]


def parse_int(value: str, field: str, player_name: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid {field!r} value for player {player_name!r}: {value!r}."
        ) from error


def parse_ratio(value: str, player_name: str) -> float:
    try:
        ratio = float(value)
    except ValueError as error:
        raise ValueError(
            f"Invalid participation ratio for player {player_name!r}: {value!r}."
        ) from error

    if not 0 <= ratio <= 1:
        raise ValueError(
            f"Participation ratio for player {player_name!r} must be from 0 to 1, "
            f"not {ratio}."
        )
    return ratio


def load_participation_ratios(path: Path) -> dict[str, float]:
    ratios: dict[str, float] = {}

    for row in read_rows(path):
        name = row["player_name"].strip()
        tag = normalize_tag(row["player_tag"])
        if tag in ratios:
            raise ValueError(f"Duplicate player tag {tag!r} in {path.name}.")
        ratios[tag] = parse_ratio(row["player_participation_ratio"], name)

    return ratios


def load_scores(roster_path: Path, participation_path: Path) -> list[PlayerScore]:
    ratios = load_participation_ratios(participation_path)
    scores: list[PlayerScore] = []
    player_tags: set[str] = set()

    for row in read_rows(roster_path):
        name = row["name"].strip()
        tag = normalize_tag(row["tag"])
        if tag in player_tags:
            raise ValueError(f"Duplicate player tag {tag!r} in {roster_path.name}.")
        player_tags.add(tag)

        scores.append(
            PlayerScore(
                name=name,
                tag=tag,
                participation_ratio=ratios.get(tag, 0.0),
                donations=parse_int(row["donations"], "donations", name),
                trophies=parse_int(row["trophies"], "trophies", name),
            )
        )

    return sorted(
        scores,
        key=lambda score: (
            -score.total_points,
            -score.participation_points,
            -score.donation_points,
            -score.trophy_points,
            score.name.casefold(),
            score.tag,
        ),
    )


def print_chart(scores: list[PlayerScore]) -> None:
    headers = (
        "Rank",
        "Player",
        "Participation (ratio / pts)",
        "Donations (value / pts)",
        "Trophies (value / pts)",
        "Total pts",
    )
    rows = [
        (
            str(rank),
            score.name,
            f"{score.participation_ratio:.2f} / {score.participation_points:.1f}",
            f"{score.donations} / {score.donation_points}",
            f"{score.trophies} / {score.trophy_points}",
            f"{score.total_points:.1f}",
        )
        for rank, score in enumerate(scores, start=1)
    ]
    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]

    def format_row(row: tuple[str, ...]) -> str:
        return " | ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        )

    print(f"Clan grade chart ({len(scores)} current players)")
    print(format_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(format_row(row))


def main() -> None:
    roster_path, participation_path = find_input_files(Path(__file__).parent)
    print_chart(load_scores(roster_path, participation_path))


if __name__ == "__main__":
    main()