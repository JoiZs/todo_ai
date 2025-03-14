# Python CLI Todo Application with OpenAI SDK and Dockerized PostgreSQL

This is a Python CLI (Command Line Interface) application that allows users to perform CRUD (Create, Read, Update, Delete) operations on a simple Todo list. The app uses OpenAI's GPT model via the OpenAI SDK (API) to perform tasks and interact with the user. It also uses Docker to run a PostgreSQL container for persistent data storage.

## Features

- **Create a Todo**: Add new tasks to the Todo list.
- **Read Todos**: Retrieve all existing todos or search for a specific task.
- **Update a Todo**: Mark tasks as done or update their descriptions.
- **Delete a Todo**: Remove tasks from the list.
- **Persistent Data Storage**: PostgreSQL database running in a Docker container to persist todos.

## Requirements

### Prerequisites

- Python 3.8 or higher
- Docker (for running PostgreSQL)
- OpenAI API key (for integrating the OpenAI SDK)

### Install Dependencies

pip install -r requirements.txt

### Environment Variables

`

> OPENAI_API_KEY="your-openai-api-key"

`

### Set up PostgreSQL Docker container

```bash
> docker compose up -f docker-compose.yml up -d
```

### Run development server

```bash
> python main.py
```
