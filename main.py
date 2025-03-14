import dotenv
from pydantic import BaseModel
from agents import Agent, Runner


class TodoOutput(BaseModel):
    name: str
    is_done: bool


if __name__ == "__main__":
    dotenv.load_dotenv()
    todo_assistant = Agent(
        name="Todo Assistant", instructions="You are a helpful assistant."
    )
