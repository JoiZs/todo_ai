import psycopg2
from typing import List, Tuple, Optional
from pydantic import BaseModel


class TodoOutput(BaseModel):
    id: int
    name: str
    is_done: bool

    class Config:
        orm_mode = True


class Db_psql:
    def __init__(self) -> None:
        # Connec to postgresdb  and create todo table
        self.conn = psycopg2.connect(
            user="postgres", password="admintodo", host="localhost"
        )
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS todo (id serial PRIMARY KEY, name varchar, is_done boolean);"
        )

    # CREATE: Add a new todo
    def add_todo(self, name: str, is_done: bool) -> None:
        self.cur.execute(
            "INSERT INTO todo (name, is_done) VALUES (%s, %s)", (name, is_done)
        )
        self.conn.commit()

    # READ: Get all todos
    def get_all_todos(self) -> List[TodoOutput]:
        self.cur.execute("SELECT * FROM todo;")
        rows = self.cur.fetchall()
        return [TodoOutput(id=row[0], name=row[1], is_done=row[2]) for row in rows]

    # UPDATE: Update a todo's status or name
    def update_todo(
        self, todo_id: int, name: Optional[str] = None, is_done: Optional[bool] = None
    ) -> None:
        if name is not None and is_done is not None:
            self.cur.execute(
                "UPDATE todo SET name = %s, is_done = %s WHERE id = %s",
                (name, is_done, todo_id),
            )
        elif name is not None:
            self.cur.execute("UPDATE todo SET name = %s WHERE id = %s", (name, todo_id))
        elif is_done is not None:
            self.cur.execute(
                "UPDATE todo SET is_done = %s WHERE id = %s", (is_done, todo_id)
            )
        self.conn.commit()

    # DELETE: Delete a todo by ID
    def delete_todo(self, todo_id: int) -> None:
        self.cur.execute("DELETE FROM todo WHERE id = %s;", (todo_id,))
        self.conn.commit()

    # FIND: Find the first todo by name (partial match using LIKE)
    def find_todo_by_name(self, name: str) -> Optional[TodoOutput]:
        # Using LIKE for partial matching (contains the substring)
        self.cur.execute(
            "SELECT * FROM todo WHERE name LIKE %s LIMIT 1;", (f"%{name}%",)
        )
        row = self.cur.fetchone()  # Fetch the first matching result
        if row:
            return TodoOutput(id=row[0], name=row[1], is_done=row[2])
        return None

    # Close db connection and cursor

    def close(self) -> None:
        self.cur.close()
        self.conn.close()
