from __future__ import annotations

import csv
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _format_number(value: float, digits: int = 0) -> str:
    if digits <= 0:
        return f"{value:,.0f}"
    return f"{value:,.{digits}f}"


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _register_pdf_font() -> str:
    candidates = [
        ("CNFont", FONT_DIR / "DejaVuSans.ttf"),
        ("CNFont", FONT_DIR / "Arial.ttf"),
    ]
    for font_name, font_path in candidates:
        if not font_path.exists():
            continue
        try:
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
            return font_name
        except Exception:
            continue
    return "Helvetica"


def _format_range_label(start_date: date | None, end_date: date | None) -> str:
    if start_date and end_date:
        return f"Từ ngày: {start_date.strftime('%d/%m/%Y')} - Đến ngày: {end_date.strftime('%d/%m/%Y')}"
    if start_date:
        return f"Từ ngày: {start_date.strftime('%d/%m/%Y')}"
    if end_date:
        return f"Đến ngày: {end_date.strftime('%d/%m/%Y')}"
    return "Toàn bộ dữ liệu"


def build_transactions_csv(
    transactions: list[Any],
    name_map: dict[int, str],
    summary: Any,
    start_date: date | None,
    end_date: date | None,
) -> bytes:
    output = StringIO(newline="")
    writer = csv.writer(output)

    writer.writerow(["Báo cáo giao dịch CNFund"])
    writer.writerow(["Khoảng thời gian", _format_range_label(start_date, end_date)])
    writer.writerow(["Tổng giao dịch", str(getattr(summary, "total_count", 0))])
    writer.writerow(["Tổng giá trị", _format_number(_safe_float(getattr(summary, "total_volume", 0.0)))])
    writer.writerow(["Tổng tiền nạp", _format_number(_safe_float(getattr(summary, "total_deposits", 0.0)))])
    writer.writerow(["Tổng tiền rút", _format_number(_safe_float(getattr(summary, "total_withdrawals", 0.0)))])
    writer.writerow(["Lãi/Lỗ ròng", _format_number(_safe_float(getattr(summary, "gross_profit_loss", 0.0)))])
    writer.writerow(["% Lãi/Lỗ", _format_percent(_safe_float(getattr(summary, "gross_profit_loss_percent", 0.0)))])
    writer.writerow([])
    writer.writerow(["ID", "Nhà đầu tư", "Loại", "Số tiền", "NAV", "Ngày", "Đơn vị thay đổi"])

    for tx in transactions:
        writer.writerow(
            [
                tx.id,
                name_map.get(tx.investor_id, f"Investor {tx.investor_id}"),
                tx.type,
                _safe_float(tx.amount),
                _safe_float(tx.nav),
                _to_datetime(tx.date).strftime("%Y-%m-%d"),
                f"{_safe_float(tx.units_change):.6f}",
            ]
        )

    return output.getvalue().encode("utf-8-sig")


def build_transactions_pdf(
    transactions: list[Any],
    name_map: dict[int, str],
    summary: Any,
    start_date: date | None,
    end_date: date | None,
    generated_at: datetime,
) -> bytes:
    font_name = _register_pdf_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="CNFund Transactions Report",
    )

    styles = getSampleStyleSheet()
    heading_style = styles["Heading2"].clone("HeadingCN")
    heading_style.fontName = font_name
    heading_style.fontSize = 16
    heading_style.spaceAfter = 6

    text_style = styles["Normal"].clone("NormalCN")
    text_style.fontName = font_name
    text_style.fontSize = 10
    text_style.leading = 13

    elements: list[Any] = []
    elements.append(Paragraph("CNFUND - BÁO CÁO GIAO DỊCH", heading_style))
    elements.append(Paragraph(_format_range_label(start_date, end_date), text_style))
    elements.append(Spacer(1, 6))

    summary_rows = [
        ["Tổng giao dịch", str(getattr(summary, "total_count", 0))],
        ["Tổng giá trị", _format_number(_safe_float(getattr(summary, "total_volume", 0.0)))],
        ["Tổng tiền nạp", _format_number(_safe_float(getattr(summary, "total_deposits", 0.0)))],
        ["Tổng tiền rút", _format_number(_safe_float(getattr(summary, "total_withdrawals", 0.0)))],
        ["Lãi/Lỗ ròng", _format_number(_safe_float(getattr(summary, "gross_profit_loss", 0.0)))],
        ["% Lãi/Lỗ", _format_percent(_safe_float(getattr(summary, "gross_profit_loss_percent", 0.0)))],
    ]
    summary_table = Table(summary_rows, colWidths=[50 * mm, 55 * mm], hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    details_rows: list[list[str]] = [
        ["ID", "Nhà đầu tư", "Loại", "Số tiền", "NAV", "Ngày", "Đơn vị thay đổi"],
    ]
    for tx in transactions:
        details_rows.append(
            [
                str(tx.id),
                name_map.get(tx.investor_id, f"Investor {tx.investor_id}"),
                str(tx.type),
                _format_number(_safe_float(tx.amount)),
                _format_number(_safe_float(tx.nav)),
                _to_datetime(tx.date).strftime("%d/%m/%Y"),
                _format_number(_safe_float(tx.units_change), digits=6),
            ]
        )

    details_table = Table(
        details_rows,
        repeatRows=1,
        colWidths=[14 * mm, 52 * mm, 30 * mm, 34 * mm, 34 * mm, 24 * mm, 36 * mm],
    )
    details_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (3, 1), (4, -1), "RIGHT"),
                ("ALIGN", (6, 1), (6, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    elements.append(details_table)
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Ngày xuất: {generated_at.strftime('%d/%m/%Y %H:%M')}", text_style))

    doc.build(elements)
    return buffer.getvalue()
