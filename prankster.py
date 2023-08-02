"""Flexible date format solver.

Get a list of strings representing dates. infer the format based on a regex match.

"""
import re
from typing import List

pattern = re.compile(r"^(?:[\D ]*)(?=[\D ]*?(?:(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9]))?(?=[\D ]*?(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9])|(Mar|May|Jan|Feb|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec))))?(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9]))?(?:[\D ]+)*?(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9]))?(?=[\D ]*?(?:(Mar|May|Jan|Feb|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|(0\d|1[0-2]))?(?=[\D ]?(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9]))(?=[\D ]?(?:(20\d{2}|19\d{2}|18\d{2})|(0\d|1[0-2])|(1[3-9]|2\d|3[0-1])|(3[2-9]|[4-9][1-9]))?(?=[\D ]?(Mar|May|Jan|Feb|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?)))))")

def detect_format_lazy(day_first=False, year_first=False):
    outcome = {
        "day": None,
        "month": None,
        "year": None}
    while any(outcome[key] is None for key in outcome.keys()):
        date_ = yield
        match = re.match(pattern, date_)
        field_names = [
            ("year_4", (0,)),
            ("year_2_month_2_day_2", (0,)),
            ("year_2_day_2", (0,)),
            ("year_2", (0,)),
            ("year_4", (1,)),
            ("year_2_month_2_day_2", (1,)),
            ("year_2_day_2", (1,)),
            ("year_2", (1,)),
            ("month_letter", (0, 1)),
            ("year_4", (1, 2)),
            ("year_2_month_2_day_2", (1, 2)),
            ("year_2_day_2", (1, 2)),
            ("year_2", (1, 2)),
            ("year_4", (1, 2)),
            ("year_2_month_2_day_2", (1, 2)),
            ("year_2_day_2", (1, 2)),
            ("year_2", (1, 2)),
            ("month_letter", (1, 2)),
            ("year_2_month_2_day_2", (2,)),
            ("year_4", (1,)),
            ("year_2_month_2_day_2", (1,)),
            ("year_2_day_2", (1,)),
            ("year_2", (1,)),
            ("year_4", (2,)),
            ("year_2_month_2_day_2", (2,)),
            ("year_2_day_2", (2,)),
            ("year_2", (2,)),
            ("month_letter", (2,)),
            ]
        formats_mapping = {
            "year_4": {"year": "%Y" , "explicit": True},
            "year_2_month_2_day_2":{
                "year": "%y",
                "month": "%m",
                "day": "%d"},
            "year_2_day_2": {
                "year": "%y",
                "day": "%d"},
            "year_2": {"year": "%y", "explicit": True},
            "month_letter": {"month": "%b", "explicit": True}
        }
        formats = [formats_mapping[field_name] for field_name, _ in field_names]
        if match is None:
            raise ValueError("no match found by regex")
        groups = match.groups()
        possible_value_sets = {
            k: {(val, (formats_mapping[title].get(k), pos, formats_mapping[title].get("explicit", False))) for val, (title, pos) in zip(groups, field_names)
                if k in title and val is not None}
            for k in ("day", "month", "year")}
        for k, set_ in possible_value_sets.items():
            if any(val[1][2] for val in set_):
                possible_value_sets[k] = {val for val in set_ if val[1][2]}
        unambiguous_sets = {key: set_ for key, set_ in possible_value_sets.items()
                            if len(set_) == 1}
        ambiguous_sets = {key: set_ for key, set_ in possible_value_sets.items()
                          if len(set_) > 1}
        if day_first and "day" in ambiguous_sets:
            unambiguous_sets["day"] = {tuple(sorted(list(ambiguous_sets["day"]), key=lambda x: x[1])[0])}
            del ambiguous_sets["day"]
        elif year_first and "year" in ambiguous_sets:
            unambiguous_sets["year"] = {tuple(sorted(list(ambiguous_sets["year"]), key=lambda x: x[1])[0])}
            del ambiguous_sets["year"]
        while any(unambiguous_sets):
            first_key = list(unambiguous_sets.keys())[0]
            some = unambiguous_sets[first_key]
            del unambiguous_sets[first_key]
            
            key_value, outcome[first_key] = some.pop()
            resolved_positions = [ix for pos in outcome.values() if pos is not None for ix in pos[1] if len(pos) == 1 ]
            outcome[first_key] = (outcome[first_key][0], tuple(pos for pos in outcome[first_key][1] if pos not in resolved_positions), outcome[first_key][2])
            sets_to_update = {key: set_ for key, set_ in ambiguous_sets.items() if key_value in [val[0] for val in set_]}
            for key, set_ in sets_to_update.items():
                
                ambiguous_sets[key] = {(key_value, (unit, pos, explicit))
                                       for key_value, (unit, pos, explicit) in set_
                                       if pos != outcome[first_key][1]}
                if len(ambiguous_sets[key]) == 1:
                    unambiguous_sets[key] = ambiguous_sets[key]
                    del ambiguous_sets[key]

    condensed_pattern = build_parse_string(outcome)
    final_pattern = map_condensed(condensed_pattern, date_)
    yield final_pattern


def build_parse_string(outcome: dict[str, tuple]):
    ambiguous_positions = {content: position for (content, position, _) in outcome.values() if len(position) > 1}
    unambiguous_positions = {content: position[0] for (content, position, _) in outcome.values() if len(position) == 1}
    ix = 0
    while any(ambiguous_positions) and ix < 9:
        content = list(ambiguous_positions.keys())[0]
        pos = ambiguous_positions[content]
        ambiguous_positions[content] = [val for val in pos
)                                        if val not in unambiguous_positions.values()]
        if len(ambiguous_positions[content]) == 1:
            unambiguous_positions[content] = ambiguous_positions[content][0]
            del ambiguous_positions[content]
        ix += 1

    condensed_pattern = "".join([str(val) for val, _ in sorted(list(unambiguous_positions.items()),
                                                               key=lambda x: x[1]) + sorted(list(ambiguous_positions.items()), key=lambda x: tuple(x[1]))])
    return condensed_pattern


def map_condensed(condensed_pattern, date):
    symbols = [f"%{patt}" for patt in condensed_pattern.split("%") if patt]
    symbols_regex = {
        "%y": r"([0-9]{2})",
        "%m": r"([0-9]{2})",
        "%b": r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
        "%d": r"([0-9]{2})",
        "%Y": r"([0-9]{4})"
    }
    expr = date
    for symbol in symbols:
        expr = re.sub(symbols_regex[symbol], f"{symbol}", expr, 1)
    return expr


def detect_format(dates: List[str], day_first: bool = False, year_first: bool = False) -> str:
    """Test datse string against a regex match and infer position of year, month, and day.
    Go through the list of dates until the format is an evidence.

    Infer where is month, day, year, and provide a parsing format as output.

    Args:
      dates, List[str]: An iterable of valid dates.
      day_first, bool: whether to already consider that the first digit combination is the day, default `False`.
      year_first, bool: whether to consider that the first digit combination is the year, default `False`.


    Returns:
      str representing a date format e.g. `%Y-%m-%d`.

    """
    detector = detect_format_lazy(day_first=day_first, year_first=year_first)
    next(detector)
    format_ = None
    for date_ in dates:
        format_ = detector.send(date_)
        if format_ is not None:
            return format_


__all__ = [detect_format]


def benchmark():
    pass


if __name__ == "__main__":
    pass
