import dotenv
from main_agent import TodoAgent
import asyncio


if __name__ == "__main__":
    dotenv.load_dotenv()

    agent = TodoAgent()
    while True:
        user_input = input(
            "I'm your Todo AI assistant. Ask me for a favor (or type 'quit' to exit): "
        )
        if user_input.lower() == "quit":
            print("Exiting...")
            break
        else:
            asyncio.run(agent.runagent(user_input))
