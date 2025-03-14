import datetime
from typing import List
from agents import (
    Agent,
    function_tool,
    Runner,
    handoff,
    GuardrailFunctionOutput,
    input_guardrail,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
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


class TodoHandoffData(BaseModel):
    tasks: list[TodoOutput]


class TodoGuardrailOutput(BaseModel):
    is_todo: bool


class Task(TypedDict):
    name: str
    due_date: str
    is_done: bool


class TodoAgent:
    def __init__(self) -> None:
        # init db instance
        self.db = Db_psql()

        @function_tool
        async def get_todos() -> list[TodoOutput]:
            todos = self.db.get_all_todos()
            logging.info("Getting all todo lists.")
            return todos

        @function_tool
        async def update_is_done(name: str, new_status: bool) -> str:
            try:
                # Log the input values
                logging.info(
                    f"Attempting to update task '{name}' to new status: {'done' if new_status else 'not done'}"
                )

                # Find the todo task by name
                todo = self.db.find_todo_by_name(name)

                if todo is None:
                    logging.warning(f"Task '{name}' not found.")
                    return "Not found the task."

                # Update the task's is_done status
                self.db.update_is_done(todo.id, new_status)
                logging.info(
                    f"Task '{name}' updated to {'done' if new_status else 'not done'} successfully."
                )

            except Exception as e:
                # Log the exception and return a generic error message
                logging.error(f"Error updating task '{name}' status: {e}")
                return "Cannot update the task's status."

            return f"Task '{name}' status updated to {'done' if new_status else 'not done'}."

        @function_tool
        async def reschedule_todo(name: str, new_time: str) -> str:
            try:
                print(name, new_time)
                todo = self.db.find_todo_by_name(name)
                if todo is None:
                    logging.warning("Not found the task.")
                    return "Not found the task."
                self.db.reschedule_todo_time(todo.id, new_time)
            except Exception as e:
                if e:
                    logging.error("Err at rescheduling a task.")
                    return "Cannot reschedule the task."
            logging.info("Rescheduled a todo task.")
            return "Rescheduled the task."

        @function_tool
        async def delete_todos(name: str) -> str:
            try:
                todo = self.db.find_todo_by_name(name)
                if todo is None:
                    logging.warning("Not found the task.")
                    return "Not found the task."
                self.db.delete_todo(todo.id)
            except Exception as e:
                if e:
                    logging.error("Err at deleting a task.")
                    return "Cannot delete the task."
            logging.info("Deleted a todo task.")
            return "Deleted the task."

        @function_tool
        async def update_task_name(name: str, new_name: str) -> str:
            try:
                # Log the input values
                logging.info(
                    f"Attempting to update task '{name}' to new name: {new_name}"
                )

                # Find the todo task by current name
                todo = self.db.find_todo_by_name(name)

                if todo is None:
                    logging.warning(f"Task '{name}' not found.")
                    return "Not found the task."

                # Update the task's name
                self.db.update_task_name(todo.id, new_name)
                logging.info(
                    f"Task '{name}' updated to new name: '{new_name}' successfully."
                )

            except Exception as e:
                # Log the exception and return a generic error message
                logging.error(f"Error updating task '{name}' name: {e}")
                return "Cannot update the task's name."

            return f"Task name updated from '{name}' to '{new_name}'."

        @function_tool
        async def add_todo(task: Task) -> str:
            try:
                print(task)
                self.db.add_todo(
                    task["name"], task["is_done"], task["due_date"])
            except Exception as e:
                if e:
                    logging.error("Cannot create a task.")
                    return "Cannot create a task."
            logging.info("Created a task.")
            return "Created a task."

        self.manager_agent = Agent(
            name="Todo manager",
            instructions=f"You are a helpful todo manager. Do not use your own knowledge just use the provided tools. You job is to retrieve, reschedule and manage tasks list. Use utc current date time: {datetime.datetime.utcnow()}.",
            model="gpt-4o-mini",
            tools=[
                get_todos,
                add_todo,
                reschedule_todo,
                delete_todos,
                update_is_done,
                update_task_name,
            ],
        )
        self.organizer_agent = Agent(
            name="Todo organizer",
            instructions="You are a smart todo categorizer. You will retrieve only criteria based todo list. You are not doing anything except categorizing todo list. Only showed the requested category. Show all by default.",
            model="gpt-4o-mini",
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

        async def on_handoff(ctx: RunContextWrapper[None], input_data: TodoHandoffData):
            print("Organizer agent is called")

        organizer_handoff = handoff(
            agent=self.organizer_agent,
            on_handoff=on_handoff,
            input_type=TodoHandoffData,
        )

        self.triage_agent = Agent(
            name="Triage agent",
            instructions="Determine which agent to use based on user's todo questions.",
            handoffs=[self.manager_agent, organizer_handoff],
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
