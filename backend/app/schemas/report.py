from pydantic import BaseModel


class ReportRead(BaseModel):
    title: str
    summary: str
    lines: list[str]
