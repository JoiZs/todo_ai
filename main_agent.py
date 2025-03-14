from agents import (
    Agent,
    function_tool,
    Runner,
    handoff,
    GuardrailFunctionOutput,
    input_guardrail,
    InputGuardrailTripwireTriggered,
)
from main_db import Db_psql, TodoOutput
from typing_extensions import TypedDict
from pydantic import BaseModel
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Todo Task type


class TodoGuardrailOutput(BaseModel):
    is_todo: bool


class Task(TypedDict):
    name: str
    is_done: bool


# init db instance
db = Db_psql()


@function_tool
async def get_todos() -> list[TodoOutput]:
    todos = db.get_all_todos()
    logging.info("Getting all todo lists.")
    return todos


@function_tool
async def delete_todos(name: str) -> str:
    try:
        todo = db.find_todo_by_name(name)
        if todo is None:
            logging.warning("Not found the task.")
            return "Not found the task."
        db.delete_todo(todo.id)
    except Exception as e:
        if e:
            logging.error("Err at deleting a task.")
            return "Cannot delete the task."
    logging.info("Deleted a todo task.")
    return "Deleted the task."


@function_tool
async def update_todo(prev: Task, newtask: Task) -> str:
    try:
        todo = db.find_todo_by_name(prev["name"])
        if todo is None:
            logging.warning("Not found the task.")
            return "Not found the task."
        db.update_todo(todo.id, newtask["name"], newtask["is_done"])
    except Exception as e:
        if e:
            logging.error("Cannot update the task.")
            return "Cannot update the task."
    logging.info("Updated a task.")
    return "Updated the task."


@function_tool
async def add_todo(task: Task) -> str:
    try:
        db.add_todo(task["name"], task["is_done"])
    except Exception as e:
        if e:
            logging.error("Cannot create a task.")
            return "Cannot create a task."
    logging.info("Created a task.")
    return "Created a task."


class TodoAgent:
    def __init__(self) -> None:
        self.manager_agent = Agent(
            name="Todo manager",
            instructions="You are a helpful todo manager. Only performs on the provided tool. You are not doing anything except todo management.",
            model="gpt-4o-mini",
            tools=[get_todos, add_todo, delete_todos, update_todo],
        )
        self.organizer_agent = Agent(
            name="Todo organizer",
            instructions="You are a smart todo organizer. Only performs on the provided tool. You are not doing anything except organizing todo list. Only showed the requested category. Show all by default.",
            model="gpt-4o-mini",
            tools=[get_todos],
        )

        guardrail_agent = Agent(
            name="Guardrail check",
            instructions="Check if user is asking about todo.",
            output_type=TodoGuardrailOutput,
        )

        @input_guardrail
        async def todo_guardrail(ctx, agent, input_data):
            result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
            final_output = result.final_output_as(TodoGuardrailOutput)

            return GuardrailFunctionOutput(
                output_info=final_output, tripwire_triggered=not final_output.is_todo
            )

        self.triage_agent = Agent(
            name="Triage agent",
            instructions="Determine which agent to use based on user's todo questions.",
            handoffs=[self.manager_agent, handoff(self.organizer_agent)],
            input_guardrails=[todo_guardrail],
        )

    # ai agent runner
    async def runagent(self, req: str) -> None:
        try:
            result = await Runner.run(self.triage_agent, req)
            print("*" * (len(result.final_output) + 4))
            print(f"* {result.final_output} *")
            print("*" * (len(result.final_output) + 4))
        except InputGuardrailTripwireTriggered:
            print("Please only asks questions about todos list.")
