from typing_extensions import TypedDict
import psycopg2
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class Task(TypedDict):
    name: str
    due_date: str
    is_done: bool


class TodoOutput(BaseModel):
    id: int
    name: str
    is_done: bool
    due_date: str

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, row):
        return cls(
            id=row[0],
            name=row[1],
            is_done=row[2],
            # Convert datetime to string
            due_date=row[3].strftime("%Y-%m-%d %H:%M:%S"),
        )


class Db_psql:
    def __init__(self) -> None:
        # Connect to PostgreSQL DB and create todo table
        self.conn = psycopg2.connect(
            user="postgres",
            password="admintodo",
            host="localhost",
            port=5432,
            dbname="postgres",
        )
        self.cur = self.conn.cursor()
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS todo (
                id serial PRIMARY KEY,
                name varchar,
                is_done boolean,
                due_date timestamp
            );
            """
        )
        self.conn.commit()

        print("db connection: ", self.conn.status)

    # CREATE: Add multiple todos
    def add_multiple_todos(self, tasks: List[Task]) -> None:
        created_at = datetime.now()

        # Prepare data for insertion
        task_data = []
        for task in tasks:
            name = task.get("name")
            is_done = task.get("is_done", False)
            due_date = task.get("due_date")

            # Convert due_date to datetime if it's passed as a string
            if due_date:
                due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
            else:
                due_date = created_at

            task_data.append((name, is_done, due_date))

        # Insert multiple tasks into the database at once
        self.cur.executemany(
            "INSERT INTO todo (name, is_done, due_date) VALUES (%s, %s, %s)", task_data
        )
        self.conn.commit()
        print(f"{len(tasks)} tasks were added successfully.")

    # CREATE: Add a new todo with a due date
    def add_todo(
        self, name: str, is_done: bool, due_date: Optional[str] = None
    ) -> None:
        created_at = datetime.now()
        new_due: datetime
        if due_date:
            # Convert string to datetime
            new_due = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
        else:
            new_due = created_at

        self.cur.execute(
            "INSERT INTO todo (name, is_done, due_date) VALUES (%s, %s, %s)",
            (name, is_done, new_due),
        )
        self.conn.commit()

    # READ: Get all todos
    def get_all_todos(self) -> list[TodoOutput]:
        self.cur.execute("SELECT * FROM todo;")
        rows = self.cur.fetchall()
        return [TodoOutput.from_orm(row) for row in rows for row in rows]

    # RESCHEDULE: Only reschedule the time (update due_date)

    def reschedule_todo_time(self, todo_id: int, new_due_date: str) -> None:
        new_due = datetime.strptime(
            new_due_date, "%Y-%m-%d %H:%M:%S"
        )  # Convert string to datetime

        # Update only the due_date of the task
        self.cur.execute(
            "UPDATE todo SET due_date = %s WHERE id = %s", (new_due, todo_id)
        )
        self.conn.commit()
        print(
            f"Task {todo_id} has been rescheduled to {new_due.strftime('%Y-%m-%d %H:%M:%S')}."
        )

    # UPDATE: Update a todo's status or name

    def update_todo(
        self,
        todo_id: int,
        name: Optional[str] = None,
        is_done: Optional[bool] = None,
        due_date: Optional[str] = None,
    ) -> None:
        new_due: Optional[datetime] = None
        if due_date:
            # Convert string to datetime
            new_due = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")

        if name is not None and is_done is not None:
            self.cur.execute(
                "UPDATE todo SET name = %s, is_done = %s, due_date = %s WHERE id = %s",
                (name, is_done, new_due, todo_id),
            )
        elif name is not None:
            self.cur.execute("UPDATE todo SET name = %s WHERE id = %s", (name, todo_id))
        elif is_done is not None:
            self.cur.execute(
                "UPDATE todo SET is_done = %s WHERE id = %s", (is_done, todo_id)
            )
        elif due_date is not None:
            self.cur.execute(
                "UPDATE todo SET due_date = %s WHERE id = %s", (new_due, todo_id)
            )
        self.conn.commit()

    # DELETE: Delete a todo by ID
    def delete_todo(self, todo_id: int) -> None:
        self.cur.execute("DELETE FROM todo WHERE id = %s;", (todo_id,))
        self.conn.commit()

    # FIND: Find the first todo by name (partial match using LIKE)
    def find_todo_by_name(self, name: str) -> Optional[TodoOutput]:
        self.cur.execute(
            "SELECT * FROM todo WHERE name LIKE %s LIMIT 1;", (f"%{name}%",)
        )
        row = self.cur.fetchone()

        if row:
            return TodoOutput.from_orm(row)
        return None

    # Close DB connection and cursor
    def close(self) -> None:
        self.cur.close()
        self.conn.close()
