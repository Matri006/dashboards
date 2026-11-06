"""Показатели формы F10 «Движение персонала до 35 лет»."""

import math
import re
from numbers import Real

from detector import normalize


_METRICS = (
    ("headcount", "Среднесписочная численность"),
    ("dismissed", "Уволено"),
    ("hired", "Принято"),
)


def _number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, str):
        try:
            value = float(value.replace("\u00a0", "").replace(" ", "").replace(",", "."))
        except ValueError:
            return None
    if isinstance(value, Real) and math.isfinite(value) and value >= 0:
        return float(value)
    return None


def _reason_items(values):
    for value in values:
        if value is None:
            continue
        for reason in re.split(r"[,;\n]+", str(value)):
            reason = " ".join(reason.split()).strip(" .")
            if reason:
                yield reason


def personnel_report(workbook):
    records = []
    reason_counts = {}
    warnings = []
    found_header = False
    invalid_values = 0

    for sheet in workbook.worksheets:
        header_row = None
        for row_number, row in enumerate(
            sheet.iter_rows(min_row=1, max_row=min(sheet.max_row, 30), values_only=True),
            1,
        ):
            labels = [normalize(value) for value in row]
            if (
                any("персонал" == label for label in labels)
                and any("среднесписочная численность" in label for label in labels)
                and any("уволено за период" in label for label in labels)
                and any("принято за период" in label for label in labels)
            ):
                header_row = row_number
                break
        if header_row is None:
            continue

        found_header = True
        sheet_records = []
        for row in sheet.iter_rows(min_row=header_row + 1, values_only=True):
            values = list(row)
            label = str(values[0]).strip() if values and values[0] is not None else ""
            normalized_label = normalize(label)
            if not label or normalized_label in {"1", "2", "3", "4", "5"}:
                continue
            is_total = normalized_label.startswith(("итого", "всего"))
            is_subcategory = normalized_label.startswith("из них")
            if not is_total and not is_subcategory and not any(
                character.isalpha() for character in label
            ):
                continue

            metrics = {}
            for index, (key, _) in enumerate(_METRICS, start=1):
                raw_value = values[index] if index < len(values) else None
                metrics[key] = _number(raw_value)
                if raw_value not in (None, "") and metrics[key] is None:
                    invalid_values += 1

            reason_items = list(_reason_items(values[4:]))
            reasons = "; ".join(reason_items)
            sheet_records.append({
                "role": label,
                "subcategory": is_subcategory,
                "total": is_total,
                "reasons": reasons,
                **metrics,
            })

        for index, record in enumerate(sheet_records):
            has_subcategories = (
                not record["subcategory"]
                and index + 1 < len(sheet_records)
                and sheet_records[index + 1]["subcategory"]
            )
            if (
                not record["total"]
                and not has_subcategories
                and (record["dismissed"] or 0) > 0
            ):
                for reason in _reason_items([record["reasons"]]):
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
        records.extend(sheet_records)

    if not found_header:
        warnings.append("Не найдена шапка формы F10 с показателями движения персонала.")
    elif not records:
        warnings.append("В форме F10 не найдены строки категорий персонала.")
    elif not any(
        record[key] is not None
        for record in records
        for key, _ in _METRICS
    ):
        warnings.append(
            "Числовые показатели не заполнены; показаны категории шаблона без графика."
        )
    if invalid_values:
        warnings.append(f"Некорректные числовые значения пропущены: {invalid_values}.")

    total_row = next((record for record in records if record["total"]), None)
    totals = {
        key: total_row[key] if total_row else None
        for key, _ in _METRICS
    }
    reason_frequencies = [
        {"reason": reason, "count": count}
        for reason, count in sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0].casefold()),
        )
    ]
    return {
        "totals": totals,
        "records": records,
        "reason_frequencies": reason_frequencies,
    }, warnings
