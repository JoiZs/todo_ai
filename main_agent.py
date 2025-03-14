from agents import Agent, function_tool, Runner
from main_db import Db_psql, TodoOutput
from typing_extensions import TypedDict
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Todo Task type


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
        self.agent = Agent(
            name="Todo Assistant",
            instructions="You are a helpful todo assistant.",
            model="gpt-4o-mini",
            tools=[get_todos, add_todo, delete_todos, update_todo],
        )

    # ai agent runner
    async def runagent(self, req: str) -> None:
        result = await Runner.run(self.agent, req)
        print("*" * (len(result.final_output) + 4))
        print(f"* {result.final_output} *")
        print("*" * (len(result.final_output) + 4))
        return
