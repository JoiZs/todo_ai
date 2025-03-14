from typing_extensions import TypedDict
import psycopg2
from typing import Optional
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

    # CREATE: Add a new todo with a due date
    def add_todo(
        self, name: str, is_done: bool, due_date: Optional[str] = None
    ) -> None:
        created_at = datetime.utcnow()
        new_due: Optional[datetime] = None
        if due_date:
            # Convert string to datetime
            new_due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        else:
            new_due = created_at
        print(name, is_done, new_due)

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

    def update_task_name(self, task_id: int, new_name: str) -> None:
        # Prepare the SQL query to update the task's name
        query = """
        UPDATE todo
        SET name = %s
        WHERE id = %s
        """

        # Execute the query with the provided new_name and task_id
        self.cur.execute(query, (new_name, task_id))
        self.conn.commit()

    # UPDATE: Change the 'is_done' status of an existing task

    def update_is_done(self, task_id: int, is_done: bool) -> None:
        # Prepare the SQL query to update the task's 'is_done' status
        query = """
        UPDATE todo
        SET is_done = %s
        WHERE id = %s
        """

        # Execute the query with the provided values
        self.cur.execute(query, (is_done, task_id))
        self.conn.commit()

        # Check if the update was successful (optional)
        if self.cur.rowcount == 0:
            print(f"No task found with ID {task_id}.")
        else:
            print(
                f"Task with ID {task_id} has been updated to {'done' if is_done else 'not done'}."
            )

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
