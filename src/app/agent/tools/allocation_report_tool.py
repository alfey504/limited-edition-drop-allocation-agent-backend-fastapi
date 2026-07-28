import asyncio
import uuid
from pathlib import Path

from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.repositories.report_repository import ReportRepository


class AllocationReportInput(BaseModel):
    sneaker_id: int = Field(..., description="Id of the sneaker this report is for.")
    sneaker_name: str = Field(..., description="Sneaker name, for the report header.")
    total_inventory: int = Field(..., description="Total units available across all regions.")
    demand_forecast: dict[str, float] = Field(
        ..., description="Mapping of region name to ML-predicted demand units."
    )
    forecast_analysis: str = Field(
        ...,
        description=(
            "Your analysis of the demand forecast itself, independent of the allocation "
            "decision: notable regional concentration or outliers, how much to trust the "
            "per-region numbers (see get_regional_demand_drivers), and anything else worth "
            "noting about the forecast before it's turned into an allocation."
        ),
    )
    allocation: dict[str, int] = Field(
        ..., description="Mapping of region name to units allocated to that region."
    )
    reasoning: str = Field(..., description="Explanation of why this allocation was chosen.")


def _table(header: tuple[str, str], rows: list[tuple[str, str]]) -> Table:
    table = Table([list(header), *rows], colWidths=[3 * inch, 2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )
    return table


def _build_pdf(path: Path, data: AllocationReportInput) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=letter)

    forecast_rows = [
        (region, f"{units:.1f}")
        for region, units in sorted(
            data.demand_forecast.items(), key=lambda item: item[1], reverse=True
        )
    ]
    allocation_rows = [
        (region, str(units))
        for region, units in sorted(
            data.allocation.items(), key=lambda item: item[1], reverse=True
        )
    ]
    allocated_total = sum(data.allocation.values())

    story = [
        Paragraph(f"Inventory Allocation Report — {data.sneaker_name}", styles["Title"]),
        Paragraph(f"Sneaker ID: {data.sneaker_id}", styles["Normal"]),
        Paragraph(f"Total inventory: {data.total_inventory}", styles["Normal"]),
        Paragraph(f"Allocated: {allocated_total} | Unallocated: {data.total_inventory - allocated_total}", styles["Normal"]),
        Spacer(1, 0.3 * inch),
        Paragraph("Forecasted Demand", styles["Heading2"]),
        _table(("Region", "Forecasted demand"), forecast_rows),
        Spacer(1, 0.3 * inch),
        Paragraph("Forecast Analysis", styles["Heading2"]),
        Paragraph(data.forecast_analysis, styles["BodyText"]),
        Spacer(1, 0.3 * inch),
        Paragraph("Allocation", styles["Heading2"]),
        _table(("Region", "Allocated units"), allocation_rows),
        Spacer(1, 0.3 * inch),
        Paragraph("Reasoning", styles["Heading2"]),
        Paragraph(data.reasoning, styles["BodyText"]),
    ]
    doc.build(story)


def make_allocation_report_tool(
    reports_dir: Path,
    report_repository: ReportRepository,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> StructuredTool:
    @tool(
        description=(
            "Generate a PDF report of the final inventory allocation for this conversation, "
            "containing the forecasted demand per region, your analysis of that forecast, the "
            "allocation per region, and the reasoning behind it. Call this once, after arriving "
            "at a final allocation. Returns a filename the user can use to download the report."
        ),
        args_schema=AllocationReportInput,
    )
    async def generate_allocation_report_pdf(
        sneaker_id: int,
        sneaker_name: str,
        total_inventory: int,
        demand_forecast: dict[str, float],
        forecast_analysis: str,
        allocation: dict[str, int],
        reasoning: str,
    ) -> dict[str, str]:
        data = AllocationReportInput(
            sneaker_id=sneaker_id,
            sneaker_name=sneaker_name,
            total_inventory=total_inventory,
            demand_forecast=demand_forecast,
            forecast_analysis=forecast_analysis,
            allocation=allocation,
            reasoning=reasoning,
        )

        reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{sneaker_name}_{uuid.uuid4()}.pdf"
        path = reports_dir / filename

        # reportlab has no async API and PDF layout isn't instant — keep it off the event loop.
        await asyncio.to_thread(_build_pdf, path, data)

        # Ownership record — the future GET /file/{filename} route checks this
        # to make sure only the user who generated a report can download it.
        report = await report_repository.create(user_id=user_id, document=filename)

        return {"filename": filename, "report_id": report.id}

    return generate_allocation_report_pdf
