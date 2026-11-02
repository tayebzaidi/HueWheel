"""Regenerates bom/HueWheel_BOM.xlsx.  Requires openpyxl.

Once you've started filling in the Have? column in the spreadsheet, edit the
spreadsheet directly rather than re-running this (it would overwrite your edits).
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

F = "Arial"
HDR = PatternFill("solid", fgColor="1F2937")
INP = PatternFill("solid", fgColor="FFF9C4")
SEC = PatternFill("solid", fgColor="E5E7EB")
thin = Side(style="thin", color="D1D5DB")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

# name, spec, qty, unit $, have?, include?, price basis, notes
ROWS = [
    ("Philips Hue Bridge", "Your existing bridge (EXAMPLE ROW: shows a filled-in 'Have?')", 1, 0, "Y", "Y",
     "Already owned (per project brief)", "Needs to be on the same 2.4 GHz-reachable network as the ESP32."),
    ("Rotary encoder, 24-detent (x2)", "Bourns PEC11R-4215F-S0024: 24 detents, 6 mm D-shaft, 15 mm shaft, bushing mount", 2, 3.00, "", "Y",
     "Estimate. Listings seen: Element14 NOK 20.58 (qty 1), Electrokit SEK 32 inc. VAT",
     "CRITICAL: detent count sets the number spacing on the wheels. A 20-detent encoder (e.g. KY-040) needs reprinted wheels and a new numbering scheme. Tell me what you have first."),
    ("ESP32-C3 SuperMini", "Wi-Fi microcontroller, about 22.5 x 18 mm, USB-C", 1, 3.50, "", "Y",
     "Estimate. Street price quoted at about $2-4 (atomic14, espboards.dev); single-unit retail runs higher",
     "Any ESP32 with Wi-Fi works, but a different board needs a redesigned tray in the base plate."),
    ("Mini slide switch (alarm on/off)", "SPDT, about 12.7 x 6.6 mm body, 2.54 mm pitch (SS12D00-style)", 1, 0.25, "", "Y",
     "Estimate, not checked against a listing", "Fits the 9 x 4.5 mm side slot; hot-glued from inside."),
    ("Hookup wire", "26-30 AWG, about 1 m total", 1, 2.00, "", "Y",
     "Estimate, not checked against a listing", "Offcuts from an old USB or ribbon cable are fine."),
    ("M3 x 10 screws", "Pan or socket head; thread into 2.6 mm pilot holes in the shell", 4, 0.15, "", "Y",
     "Estimate, not checked against a listing", "Any M3 x 8-12. Self-tapping #4 screws also work."),
    ("USB-C cable + 5 V charger", "Any phone charger; 500 mA is plenty", 1, 5.00, "", "Y",
     "Estimate, not checked against a listing", "Almost certainly already owned; the board's Wi-Fi draws only short peaks."),
    ("Rubber feet", "Stick-on, up to 9 mm diameter (recesses in the base plate)", 4, 0.25, "", "Y",
     "Estimate, not checked against a listing", "Free alternative: four dots of hot glue."),
    ("PLA filament", "About 120 g total, see Printed Parts tab", 120, 0.02, "", "Y",
     "Estimate at $20/kg; grams from PrusaSlicer", "Two colours recommended for contrast, but one is fine."),
    ("Shipping", "If encoders and ESP32 come from a distributor or marketplace", 1, 6.00, "", "Y",
     "Estimate. Varies a lot by vendor; can exceed the parts cost", "Combine into one order. Set 'Have?' to Y if shipping is free."),
    ("Ballast", "Steel washers, nuts or coins glued inside the front of the base", 1, 0, "", "N",
     "Scrap", "Printed unit is only about 120 g plus parts. Add weight if it slides when you roll a wheel."),
    ("Numeral contrast", "Paint pen or wax crayon rubbed into the engraved numerals", 1, 0, "", "N",
     "Scrap", "Greatly improves legibility of the numerals."),
    ("Night-light LED + resistor", "3 mm white LED + about 220 ohm, lights the window while setting", 1, 0.20, "", "N",
     "Estimate, not checked against a listing", "Only if you set the alarm in the dark. Not yet in the CAD model."),
]

wb = Workbook()
wb.calculation.fullCalcOnLoad = True
ws = wb.active
ws.title = "BOM"
ws["A1"] = "HueWheel Bill of Materials"
ws["A1"].font = Font(name=F, size=14, bold=True)
ws["A2"] = ("How to use: edit the yellow cells only. Have? = Y if you already own it. Include? = N to leave an item "
            "out. Unit prices are planning estimates, not quotes; update them when you order.")
ws["A2"].font = Font(name=F, size=9, italic=True)
ws.merge_cells("A2:J2")
ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
ws.row_dimensions[2].height = 28

heads = ["Item", "Specification", "Qty", "Unit price ($)", "Have?", "Include?", "Line cost if buying everything ($)",
         "Still to buy ($)", "Price basis", "Notes"]
H = 4
for c, h in enumerate(heads, 1):
    x = ws.cell(H, c, h)
    x.font = Font(name=F, bold=True, color="FFFFFF")
    x.fill = HDR
    x.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    x.border = BOX
ws.row_dimensions[H].height = 44

first = H + 1
for i, r in enumerate(ROWS):
    n = first + i
    name, spec, qty, price, have, inc, basis, notes = r
    vals = [name, spec, qty, price, have or None, inc,
            f'=IF(F{n}="Y",C{n}*D{n},0)', f'=IF(AND(F{n}="Y",E{n}<>"Y"),C{n}*D{n},0)', basis, notes]
    for c, v in enumerate(vals, 1):
        x = ws.cell(n, c, v)
        x.font = Font(name=F, size=10)
        x.border = BOX
        x.alignment = Alignment(wrap_text=True, vertical="top")
    for c in (3, 4, 5, 6):
        ws.cell(n, c).fill = INP
        ws.cell(n, c).font = Font(name=F, size=10, color="0000FF")
        if c in (5, 6):
            ws.cell(n, c).alignment = Alignment(horizontal="center", vertical="top")
    for c in (4, 7, 8):
        ws.cell(n, c).number_format = "$#,##0.00"
last = first + len(ROWS) - 1

t = last + 2
labels = [("If you bought every included item", f"=SUM(G{first}:G{last})"),
          ("Still to buy", f"=SUM(H{first}:H{last})"),
          ("Budget", 30),
          ("Left in budget", f"=H{t + 2}-H{t + 1}")]
for i, (lab, val) in enumerate(labels):
    a = ws.cell(t + i, 2, lab)
    a.font = Font(name=F, bold=True)
    a.alignment = Alignment(horizontal="right")
    b = ws.cell(t + i, 8, val)
    b.font = Font(name=F, bold=True, color="0000FF" if i == 2 else "000000")
    b.number_format = "$#,##0.00"
    b.border = BOX
ws.cell(t + 2, 8).fill = INP
ws.cell(t + 2, 8).comment = Comment("Target from the project brief: under $30 of new purchases.", "HueWheel")

dv = DataValidation(type="list", formula1='"Y,N"', allow_blank=True)
ws.add_data_validation(dv)
dv.add(f"E{first}:F{last}")
ws.conditional_formatting.add(f"A{first}:J{last}", FormulaRule(
    formula=[f'OR($E{first}="Y",$F{first}="N")'], font=Font(color="9CA3AF")))
ws.conditional_formatting.add(f"H{t + 3}", FormulaRule(formula=[f"$H${t + 3}<0"], font=Font(color="FF0000", bold=True)))
for col, w in zip("ABCDEFGHIJ", (30, 46, 6, 9, 7, 9, 13, 10, 38, 52)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = ws.cell(first, 2)

p = wb.create_sheet("Printed Parts")
p["A1"] = "Printed Parts"
p["A1"].font = Font(name=F, size=14, bold=True)
p["A2"] = ("Weight and time: PrusaSlicer 2.9.6 default 0.4 mm profile, 0.2 mm layers, 15% infill, PLA at 1.24 g/cm3. "
           "Your printer's times will differ.")
p["A2"].font = Font(name=F, size=9, italic=True)
for c, h in enumerate(["Part", "STL", "Qty", "Weight (g)", "Time (h)", "Supports", "Print orientation"], 1):
    x = p.cell(4, c, h)
    x.font = Font(name=F, bold=True, color="FFFFFF")
    x.fill = HDR
    x.border = BOX
P = [("Base plate", "cad/stl/plate.stl", 1, 29.0, 3.03, "None", "Flat as exported; cradles point up"),
     ("Shell", "cad/stl/shell.stl", 1, 72.0, 5.52, "Build plate only (figures include them)", "Open side down on the bed, as exported"),
     ("Hours wheel", "cad/stl/wheel_hours.stl", 1, 9.3, 0.81, "None", "On its side, stub boss up, as exported"),
     ("Minutes wheel", "cad/stl/wheel_minutes.stl", 1, 9.3, 0.80, "None", "On its side, stub boss up, as exported")]
for i, r in enumerate(P):
    for c, v in enumerate(r, 1):
        x = p.cell(5 + i, c, v)
        x.font = Font(name=F, size=10, color="0000FF" if c in (4, 5) else "000000")
        x.border = BOX
p["A9"] = "Total"
p["A9"].font = Font(name=F, bold=True)
p["D9"] = "=SUMPRODUCT(C5:C8,D5:D8)"
p["E9"] = "=SUMPRODUCT(C5:C8,E5:E8)"
for a in ("D9", "E9"):
    p[a].font = Font(name=F, bold=True)
    p[a].number_format = "0.0"
    p[a].border = BOX
for col, w in zip("ABCDEFG", (16, 26, 6, 11, 9, 38, 40)):
    p.column_dimensions[col].width = w

wb.save(Path(__file__).with_name("HueWheel_BOM.xlsx"))
