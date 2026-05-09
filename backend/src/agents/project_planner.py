from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(
    model=settings.PLANNING_MODEL,
    temperature=settings.LLM_TEMPERATURE,
)

TASK_EXTRACTION_PROMPT = """You are an expert project analyst.

Read the following case study or project description and extract a precise, structured task list.

Case Study:
{case_study}

Rules:
- Extract ONLY tasks explicitly mentioned or clearly implied by the case study.
- Maintain the natural order of tasks.
- Identify dependencies between tasks.
- Include deadlines if mentioned.

Output format — use this exact structure:

## Extracted Task List

1. **[Task Name]**
   - **Description:** What needs to be done.
   - **Dependencies:** Which tasks must be done first (or "None").
   - **Deadline:** If mentioned, otherwise omit this line.

Continue for all tasks."""

PLAN_CREATION_PROMPT = """You are an expert project manager.

You have been given a task list. Create a detailed project roadmap organized into logical phases.

Task List:
{task_list}

Rules:
- Use ONLY the tasks provided — do not add or remove tasks.
- Group them into phases (Planning, Development, Testing, Deployment, etc.).
- For each task include: priority, timeline estimate, resources needed.

Output format:

## Project Roadmap

---

### Phase 1: [Phase Name]

#### Task: [Task Name]
- **Description:** What this involves.
- **Priority:** High / Medium / Low
- **Dependencies:** Prerequisites (or "None").
- **Timeline:** Estimated time (e.g., 2 days, 1 week).
- **Resources:** Tools, technologies, or team roles needed.

Repeat for all phases and tasks.

---

### Summary
Provide a brief overall project timeline and key milestones."""


class PlannerState(BaseModel):
    case_study: str
    task_list: str = ""
    project_plan: str = ""


workflow = StateGraph(PlannerState)


@workflow.add_node
def extract_tasks(state: PlannerState) -> PlannerState:
    prompt = TASK_EXTRACTION_PROMPT.format(case_study=state.case_study)
    task_list = llm.invoke(prompt)
    return state.model_copy(update={"task_list": task_list})


@workflow.add_node
def build_plan(state: PlannerState) -> PlannerState:
    prompt = PLAN_CREATION_PROMPT.format(task_list=state.task_list)
    plan = llm.invoke(prompt)
    return state.model_copy(update={"project_plan": plan})


workflow.set_entry_point("extract_tasks")
workflow.add_edge("extract_tasks", "build_plan")
workflow.add_edge("build_plan", END)

planner_executor = workflow.compile()


def get_project_plan(case_study: str) -> dict:
    result = planner_executor.invoke(PlannerState(case_study=case_study))
    return {
        "task_list": result["task_list"],
        "project_plan": result["project_plan"],
    }
