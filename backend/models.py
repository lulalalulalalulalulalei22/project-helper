from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    repo_url: str
    force: bool = False


class ChatRequest(BaseModel):
    project_id: int
    question: str


class ProgressEvent(BaseModel):
    step: str
    status: str
    message: str


class ProjectInfo(BaseModel):
    id: int
    repo_url: str
    project_name: str
    tech_stack: list
    created_at: str


class ReportData(BaseModel):
    id: int
    repo_url: str
    project_name: str
    tech_stack: list
    report: str
    tree: dict
    created_at: str
