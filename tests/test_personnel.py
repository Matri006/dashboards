import unittest
from io import BytesIO

from openpyxl import Workbook

from analyzer import analyze_file
from app import PERSONNEL_FILE, app


def sample_personnel_workbook():
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Движение персонала в возрасте до 35 лет"])
    sheet.append(["Персонал", "Среднесписочная численность", "Уволено за период", "Принято за период", "Причины"])
    sheet.append(["Специалисты", 10, 4, 2, "Собственное желание, Переезд"])
    sheet.append(["из них рабочие", 3, 1, 1, "Собственное желание"])
    sheet.append(["из них прочие", 2, 0, 0, "Переезд"])
    sheet.append(["Руководители", 5, 2, 1, "Собственное желание"])
    sheet.append(["Итого", 17, 6, 3, "Собственное желание"])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


class PersonnelTests(unittest.TestCase):
    def test_reason_frequency_ignores_zero_dismissal_rows_and_totals(self):
        result = analyze_file("personnel.xlsx", sample_personnel_workbook())

        self.assertEqual(result["profile"].code, "F10")
        self.assertEqual(
            result["personnel"]["records"][0]["reasons"],
            "Собственное желание; Переезд",
        )
        self.assertEqual(
            result["personnel"]["reason_frequencies"],
            [
                {"reason": "Собственное желание", "count": 2},
            ],
        )

    def test_grouped_parent_reason_is_excluded_from_frequency(self):
        result = analyze_file(PERSONNEL_FILE.name, PERSONNEL_FILE.read_bytes())
        frequencies = {
            item["reason"]: item["count"]
            for item in result["personnel"]["reason_frequencies"]
        }

        self.assertEqual(frequencies["1 причина"], 2)

    def test_f10_upload_redirects_to_separate_page(self):
        response = app.test_client().post(
            "/",
            data={"files": [(BytesIO(sample_personnel_workbook()), "personnel.xlsx")]},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/personnel")

    def test_personnel_page_has_separate_reason_chart(self):
        client = app.test_client()
        client.post("/personnel")

        page = client.get("/personnel").data
        other_dashboard = client.get("/dashboards").data

        self.assertIn("Причины увольнения".encode(), page)
        self.assertIn("personnel-reason-chart".encode(), page)
        self.assertNotIn(PERSONNEL_FILE.name.encode(), other_dashboard)
