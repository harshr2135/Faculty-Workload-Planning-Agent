"""Export allocation timetable grids to Excel (.xlsx) or PDF packs.

Produces three stakeholder packs from an allocation run:
- faculty: one sheet/page per faculty member
- students: one sheet/page per batch section (class)
- rooms: one sheet/page per classroom and laboratory
"""

from __future__ import annotations

import io
import re
from enum import Enum

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.schemas.allocation import (
    AllocationRunRead,
    FacultyTimetableGridRead,
    RoomTimetableGridRead,
    SectionTimetableGridRead,
    TimetableGridItemRead,
    TimetableGridRead,
)

_EXCEL_SHEET_MAX = 31
_INVALID_SHEET_CHARS = re.compile(r"[\[\]\*\/\\?:]")

_HEADER_FILL = PatternFill("solid", fgColor="E2E8F0")
_BREAK_FILL = PatternFill("solid", fgColor="FEF3C7")
_LUNCH_FILL = PatternFill("solid", fgColor="FFEDD5")
_DAY_FILL = PatternFill("solid", fgColor="F8FAFC")
_THIN = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)
_WRAP = Alignment(wrap_text=True, vertical="top", horizontal="left")
_CENTER = Alignment(wrap_text=True, vertical="center", horizontal="center")

_PDF_HEADER = colors.HexColor("#E2E8F0")
_PDF_BREAK = colors.HexColor("#FEF3C7")
_PDF_LUNCH = colors.HexColor("#FFEDD5")
_PDF_DAY = colors.HexColor("#F8FAFC")
_PDF_GRID = colors.HexColor("#CBD5E1")


class TimetableExportPack(str, Enum):
    FACULTY = "faculty"
    STUDENTS = "students"
    ROOMS = "rooms"


class TimetableExportFormat(str, Enum):
    XLSX = "xlsx"
    PDF = "pdf"


class TimetableExportError(ValueError):
    """Raised when a timetable pack cannot be built for a run."""


def export_timetable_pack(
    run: AllocationRunRead,
    pack: TimetableExportPack,
    fmt: TimetableExportFormat = TimetableExportFormat.XLSX,
) -> bytes:
    """Build one timetable pack (.xlsx or .pdf) and return file bytes."""
    if fmt is TimetableExportFormat.PDF:
        return _export_pdf_pack(run, pack)
    if pack is TimetableExportPack.FACULTY:
        return _workbook_bytes(
            _build_faculty_workbook(run),
            empty_message="No faculty timetable grids to export for this run.",
        )
    if pack is TimetableExportPack.STUDENTS:
        return _workbook_bytes(
            _build_students_workbook(run),
            empty_message="No section (student) timetable grids to export for this run.",
        )
    if pack is TimetableExportPack.ROOMS:
        return _workbook_bytes(
            _build_rooms_workbook(run),
            empty_message="No classroom or laboratory timetable grids to export for this run.",
        )
    raise TimetableExportError(f"Unknown export pack: {pack}")


def export_filename(
    run: AllocationRunRead,
    pack: TimetableExportPack,
    fmt: TimetableExportFormat = TimetableExportFormat.XLSX,
) -> str:
    run_id = run.id if run.id is not None else 0
    labels = {
        TimetableExportPack.FACULTY: "Faculty",
        TimetableExportPack.STUDENTS: "Student",
        TimetableExportPack.ROOMS: "Room",
    }
    return f"AIML_{labels[pack]}_Timetable_run{run_id}.{fmt.value}"


def export_media_type(fmt: TimetableExportFormat) -> str:
    if fmt is TimetableExportFormat.PDF:
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def export_single_faculty_pdf(run: AllocationRunRead, faculty_id: int) -> bytes:
    """Build a one-page PDF for a single faculty member's weekly timetable."""
    item = next(
        (grid for grid in run.faculty_timetable_grids if grid.faculty_id == faculty_id),
        None,
    )
    if item is None:
        raise TimetableExportError(
            f"No faculty timetable grid found for faculty_id={faculty_id}."
        )
    pages = [
        (
            f"Faculty timetable — {item.faculty_name}",
            item.grid,
            {"hide_faculty": True, "hide_batch": False, "hide_room": False},
        )
    ]
    title = f"AIML_Timetable_{_sanitize_sheet_name(item.faculty_name)}_run{run.id}.pdf"
    return _render_pdf_pages(pages, document_title=title)


def single_faculty_pdf_filename(run: AllocationRunRead, faculty_name: str) -> str:
    run_id = run.id if run.id is not None else 0
    return f"AIML_Timetable_{_sanitize_sheet_name(faculty_name)}_run{run_id}.pdf"


def _workbook_bytes(workbook: Workbook, *, empty_message: str) -> bytes:
    if not workbook.sheetnames:
        raise TimetableExportError(empty_message)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _build_faculty_workbook(run: AllocationRunRead) -> Workbook:
    workbook = Workbook()
    workbook.remove(workbook.active)
    used_titles: set[str] = set()
    for item in run.faculty_timetable_grids:
        title = _unique_sheet_title(_faculty_sheet_name(item), used_titles)
        sheet = workbook.create_sheet(title=title)
        _write_sheet_banner(sheet, f"Faculty timetable — {item.faculty_name}")
        _write_grid(
            sheet,
            item.grid,
            start_row=3,
            hide_faculty=True,
            hide_batch=False,
            hide_room=False,
        )
    return workbook


def _build_students_workbook(run: AllocationRunRead) -> Workbook:
    workbook = Workbook()
    workbook.remove(workbook.active)
    used_titles: set[str] = set()
    for item in run.section_timetable_grids:
        title = _unique_sheet_title(_section_sheet_name(item), used_titles)
        sheet = workbook.create_sheet(title=title)
        _write_sheet_banner(
            sheet,
            (
                f"Class timetable — {item.batch_code} · Section {item.section_index} "
                f"(Semester {item.semester_number})"
            ),
        )
        _write_grid(
            sheet,
            item.grid,
            start_row=3,
            hide_faculty=False,
            hide_batch=True,
            hide_room=False,
        )
    return workbook


def _build_rooms_workbook(run: AllocationRunRead) -> Workbook:
    workbook = Workbook()
    workbook.remove(workbook.active)
    used_titles: set[str] = set()
    room_items: list[RoomTimetableGridRead] = [
        *run.classroom_timetable_grids,
        *run.laboratory_timetable_grids,
    ]
    for item in room_items:
        title = _unique_sheet_title(_room_sheet_name(item), used_titles)
        sheet = workbook.create_sheet(title=title)
        kind_label = "Laboratory" if item.room_type == "laboratory" else "Classroom"
        _write_sheet_banner(sheet, f"{kind_label} timetable — {item.room_name}")
        _write_grid(
            sheet,
            item.grid,
            start_row=3,
            hide_faculty=False,
            hide_batch=False,
            hide_room=True,
        )
    return workbook


def _write_sheet_banner(sheet: Worksheet, title: str) -> None:
    sheet["A1"] = title
    sheet["A1"].font = Font(bold=True, size=14, color="0F172A")
    sheet["A2"] = "AIML weekly timetable export"
    sheet["A2"].font = Font(italic=True, size=10, color="64748B")


def _write_grid(
    sheet: Worksheet,
    grid: TimetableGridRead,
    *,
    start_row: int,
    hide_faculty: bool,
    hide_batch: bool,
    hide_room: bool,
) -> None:
    if not grid.rows:
        sheet.cell(row=start_row, column=1, value="(No scheduled sessions)")
        return

    header_row = start_row
    subheader_row = start_row + 1
    day_header = sheet.cell(row=header_row, column=1, value="Day")
    day_header.fill = _HEADER_FILL
    day_header.font = Font(bold=True)
    day_header.border = _THIN
    day_header.alignment = _CENTER
    sheet.merge_cells(
        start_row=header_row,
        start_column=1,
        end_row=subheader_row,
        end_column=1,
    )

    for col_offset, period in enumerate(grid.periods, start=2):
        top = sheet.cell(row=header_row, column=col_offset, value=period.column_header)
        bottom = sheet.cell(
            row=subheader_row,
            column=col_offset,
            value=period.fixed_label or period.label,
        )
        fill = _slot_fill(period.slot_type)
        for cell in (top, bottom):
            cell.fill = fill if fill is not None else _HEADER_FILL
            cell.font = Font(bold=True, size=9)
            cell.border = _THIN
            cell.alignment = _CENTER

    data_start = subheader_row + 1
    for row_offset, grid_row in enumerate(grid.rows):
        excel_row = data_start + row_offset
        day_cell = sheet.cell(row=excel_row, column=1, value=grid_row.day.capitalize())
        day_cell.fill = _DAY_FILL
        day_cell.font = Font(bold=True)
        day_cell.border = _THIN
        day_cell.alignment = _CENTER
        sheet.row_dimensions[excel_row].height = 72

        col = 2
        cell_index = 0
        while cell_index < len(grid_row.cells):
            cell = grid_row.cells[cell_index]
            if cell.span_continuation:
                cell_index += 1
                continue

            span = 1
            if cell.items:
                span = max(item.col_span or 1 for item in cell.items)
            span = max(1, min(span, len(grid.periods) - (col - 2)))

            value = _cell_text(
                cell.slot_type,
                cell.fixed_label,
                cell.items,
                hide_faculty=hide_faculty,
                hide_batch=hide_batch,
                hide_room=hide_room,
            )
            excel_cell = sheet.cell(row=excel_row, column=col, value=value)
            excel_cell.border = _THIN
            fill = _slot_fill(cell.slot_type)
            if fill is not None:
                excel_cell.fill = fill
                excel_cell.alignment = _CENTER
                excel_cell.font = Font(bold=True, size=11)
            else:
                excel_cell.alignment = _WRAP
                excel_cell.font = Font(size=9)

            if span > 1:
                sheet.merge_cells(
                    start_row=excel_row,
                    start_column=col,
                    end_row=excel_row,
                    end_column=col + span - 1,
                )
                for merge_col in range(col + 1, col + span):
                    merged = sheet.cell(row=excel_row, column=merge_col)
                    merged.border = _THIN
                    if fill is not None:
                        merged.fill = fill

            col += span
            cell_index += 1

    sheet.column_dimensions["A"].width = 12
    for col_offset in range(2, len(grid.periods) + 2):
        sheet.column_dimensions[get_column_letter(col_offset)].width = 18


def _cell_text(
    slot_type: str,
    fixed_label: str | None,
    items: list[TimetableGridItemRead],
    *,
    hide_faculty: bool,
    hide_batch: bool,
    hide_room: bool,
) -> str:
    if slot_type != "teaching":
        return fixed_label or slot_type.upper()
    if not items:
        return ""
    return "\n---\n".join(
        _item_text(
            item,
            hide_faculty=hide_faculty,
            hide_batch=hide_batch,
            hide_room=hide_room,
        )
        for item in items
    )


def _item_text(
    item: TimetableGridItemRead,
    *,
    hide_faculty: bool,
    hide_batch: bool,
    hide_room: bool,
) -> str:
    lines: list[str] = []
    if hide_batch:
        lines.append(item.course_code)
    else:
        lines.append(f"{item.batch_code} · {item.course_code}")
    lines.append(item.course_name)

    meta_parts = [item.course_type, f"Sec {', '.join(str(s) for s in item.section_indices)}"]
    if item.lab_sub_batch:
        meta_parts.append(item.lab_sub_batch)
    meta_parts.append(item.kind)
    if (item.col_span or 1) > 1 and item.period_label:
        meta_parts.append(item.period_label)
    lines.append(" · ".join(meta_parts))

    if not hide_room:
        if item.room_type == "none":
            lines.append("Self-directed")
        elif item.room_name:
            lines.append(item.room_name)

    if not hide_faculty and item.faculty_names:
        lines.append(", ".join(item.faculty_names))

    return "\n".join(lines)


def _slot_fill(slot_type: str) -> PatternFill | None:
    if slot_type == "break":
        return _BREAK_FILL
    if slot_type == "lunch":
        return _LUNCH_FILL
    return None


def _faculty_sheet_name(item: FacultyTimetableGridRead) -> str:
    return _sanitize_sheet_name(item.faculty_name or f"Faculty_{item.faculty_id}")


def _section_sheet_name(item: SectionTimetableGridRead) -> str:
    return _sanitize_sheet_name(f"{item.batch_code}_Sec{item.section_index}")


def _room_sheet_name(item: RoomTimetableGridRead) -> str:
    prefix = "Lab" if item.room_type == "laboratory" else "CR"
    return _sanitize_sheet_name(f"{prefix}_{item.room_name}")


def _sanitize_sheet_name(raw: str) -> str:
    cleaned = _INVALID_SHEET_CHARS.sub("_", raw.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("'") or "Sheet"
    return cleaned[:_EXCEL_SHEET_MAX]


def _unique_sheet_title(base: str, used: set[str]) -> str:
    candidate = base[:_EXCEL_SHEET_MAX]
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while True:
        suffix_text = f"_{suffix}"
        trimmed = base[: _EXCEL_SHEET_MAX - len(suffix_text)] + suffix_text
        if trimmed not in used:
            used.add(trimmed)
            return trimmed
        suffix += 1


def _export_pdf_pack(run: AllocationRunRead, pack: TimetableExportPack) -> bytes:
    pages = _pdf_pages_for_pack(run, pack)
    if not pages:
        messages = {
            TimetableExportPack.FACULTY: "No faculty timetable grids to export for this run.",
            TimetableExportPack.STUDENTS: (
                "No section (student) timetable grids to export for this run."
            ),
            TimetableExportPack.ROOMS: (
                "No classroom or laboratory timetable grids to export for this run."
            ),
        }
        raise TimetableExportError(messages[pack])

    return _render_pdf_pages(
        pages,
        document_title=export_filename(run, pack, TimetableExportFormat.PDF),
    )


def _render_pdf_pages(
    pages: list[tuple[str, TimetableGridRead, dict[str, bool]]],
    *,
    document_title: str,
) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title=document_title,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TimetableTitle",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "TimetableSubtitle",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "TimetableCell",
        parent=styles["Normal"],
        fontSize=6.5,
        leading=8,
        alignment=TA_LEFT,
    )
    center_style = ParagraphStyle(
        "TimetableCenter",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    story: list[object] = []
    for index, (title, grid, flags) in enumerate(pages):
        if index > 0:
            story.append(PageBreak())
        story.append(Paragraph(_escape_pdf(title), title_style))
        story.append(Paragraph("AIML weekly timetable export", subtitle_style))
        story.append(
            _build_pdf_table(
                grid,
                cell_style=cell_style,
                center_style=center_style,
                hide_faculty=flags["hide_faculty"],
                hide_batch=flags["hide_batch"],
                hide_room=flags["hide_room"],
            )
        )
        story.append(Spacer(1, 4 * mm))

    document.build(story)
    return buffer.getvalue()


def _pdf_pages_for_pack(
    run: AllocationRunRead,
    pack: TimetableExportPack,
) -> list[tuple[str, TimetableGridRead, dict[str, bool]]]:
    pages: list[tuple[str, TimetableGridRead, dict[str, bool]]] = []
    if pack is TimetableExportPack.FACULTY:
        for item in run.faculty_timetable_grids:
            pages.append(
                (
                    f"Faculty timetable — {item.faculty_name}",
                    item.grid,
                    {"hide_faculty": True, "hide_batch": False, "hide_room": False},
                )
            )
    elif pack is TimetableExportPack.STUDENTS:
        for item in run.section_timetable_grids:
            pages.append(
                (
                    (
                        f"Class timetable — {item.batch_code} · Section {item.section_index} "
                        f"(Semester {item.semester_number})"
                    ),
                    item.grid,
                    {"hide_faculty": False, "hide_batch": True, "hide_room": False},
                )
            )
    elif pack is TimetableExportPack.ROOMS:
        for item in [*run.classroom_timetable_grids, *run.laboratory_timetable_grids]:
            kind_label = "Laboratory" if item.room_type == "laboratory" else "Classroom"
            pages.append(
                (
                    f"{kind_label} timetable — {item.room_name}",
                    item.grid,
                    {"hide_faculty": False, "hide_batch": False, "hide_room": True},
                )
            )
    return pages


def _build_pdf_table(
    grid: TimetableGridRead,
    *,
    cell_style: ParagraphStyle,
    center_style: ParagraphStyle,
    hide_faculty: bool,
    hide_batch: bool,
    hide_room: bool,
) -> Table:
    if not grid.rows:
        return Table([[Paragraph("(No scheduled sessions)", cell_style)]])

    header = [Paragraph("<b>Day</b>", center_style)]
    subheader = [Paragraph("", center_style)]
    for period in grid.periods:
        header.append(Paragraph(f"<b>{_escape_pdf(period.column_header)}</b>", center_style))
        subheader.append(
            Paragraph(
                f"<b>{_escape_pdf(period.fixed_label or period.label)}</b>",
                center_style,
            )
        )

    data: list[list[object]] = [header, subheader]
    span_commands: list[tuple] = [("SPAN", (0, 0), (0, 1))]
    bg_commands: list[tuple] = [
        ("BACKGROUND", (0, 0), (0, 1), _PDF_HEADER),
        ("BACKGROUND", (0, 2), (0, -1), _PDF_DAY),
    ]

    for col_offset, period in enumerate(grid.periods, start=1):
        fill = _pdf_slot_color(period.slot_type)
        if fill is not None:
            bg_commands.append(("BACKGROUND", (col_offset, 0), (col_offset, 1), fill))
        else:
            bg_commands.append(("BACKGROUND", (col_offset, 0), (col_offset, 1), _PDF_HEADER))

    for row_offset, grid_row in enumerate(grid.rows):
        table_row: list[object] = [
            Paragraph(f"<b>{_escape_pdf(grid_row.day.capitalize())}</b>", center_style)
        ]
        col = 1
        cell_index = 0
        excel_row_index = row_offset + 2  # after two header rows
        while cell_index < len(grid_row.cells):
            cell = grid_row.cells[cell_index]
            if cell.span_continuation:
                cell_index += 1
                continue

            span = 1
            if cell.items:
                span = max(item.col_span or 1 for item in cell.items)
            span = max(1, min(span, len(grid.periods) - (col - 1)))

            text = _cell_text(
                cell.slot_type,
                cell.fixed_label,
                cell.items,
                hide_faculty=hide_faculty,
                hide_batch=hide_batch,
                hide_room=hide_room,
            )
            style = center_style if cell.slot_type != "teaching" else cell_style
            html = _escape_pdf(text).replace("\n", "<br/>")
            table_row.append(Paragraph(html or " ", style))

            fill = _pdf_slot_color(cell.slot_type)
            if fill is not None:
                bg_commands.append(
                    ("BACKGROUND", (col, excel_row_index), (col + span - 1, excel_row_index), fill)
                )
            if span > 1:
                span_commands.append(
                    ("SPAN", (col, excel_row_index), (col + span - 1, excel_row_index))
                )
                for _ in range(span - 1):
                    table_row.append("")

            col += span
            cell_index += 1

        # Pad incomplete rows so Table columns stay aligned.
        while len(table_row) < len(grid.periods) + 1:
            table_row.append(Paragraph(" ", cell_style))
        data.append(table_row)

    page_width = landscape(A4)[0] - 20 * mm
    day_width = 18 * mm
    period_width = (page_width - day_width) / max(1, len(grid.periods))
    col_widths = [day_width] + [period_width] * len(grid.periods)

    table = Table(data, colWidths=col_widths, repeatRows=2)
    style_commands: list[tuple] = [
        ("GRID", (0, 0), (-1, -1), 0.4, _PDF_GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        *bg_commands,
        *span_commands,
    ]
    table.setStyle(TableStyle(style_commands))
    return table


def _pdf_slot_color(slot_type: str) -> colors.Color | None:
    if slot_type == "break":
        return _PDF_BREAK
    if slot_type == "lunch":
        return _PDF_LUNCH
    return None


def _escape_pdf(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
