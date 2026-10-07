from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

DB = Path(__file__).with_name("students.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                year INTEGER NOT NULL
            )
            """
        )


# Create the database table when the app starts
# Works with both Flask and Gunicorn/Railway
init_db()


@app.route("/")
def index():
    q = request.args.get("q", "").strip()

    with get_db() as conn:
        if q:
            students = conn.execute(
                """
                SELECT *
                FROM students
                WHERE name LIKE ? OR roll_no LIKE ?
                ORDER BY id DESC
                """,
                (f"%{q}%", f"%{q}%")
            ).fetchall()
        else:
            students = conn.execute(
                """
                SELECT *
                FROM students
                ORDER BY id DESC
                """
            ).fetchall()

    return render_template(
        "index.html",
        students=students,
        q=q
    )


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        data = (
            request.form["name"].strip(),
            request.form["roll_no"].strip(),
            request.form["email"].strip(),
            request.form["course"].strip(),
            int(request.form["year"])
        )

        try:
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT INTO students
                    (name, roll_no, email, course, year)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    data
                )

            flash("Student added successfully.", "success")
            return redirect(url_for("index"))

        except sqlite3.IntegrityError:
            flash("Roll number already exists.", "error")

    return render_template(
        "form.html",
        student=None
    )


@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    with get_db() as conn:
        student = conn.execute(
            """
            SELECT *
            FROM students
            WHERE id = ?
            """,
            (student_id,)
        ).fetchone()

        if student is None:
            return "Student not found", 404

        if request.method == "POST":
            try:
                conn.execute(
                    """
                    UPDATE students
                    SET name = ?,
                        roll_no = ?,
                        email = ?,
                        course = ?,
                        year = ?
                    WHERE id = ?
                    """,
                    (
                        request.form["name"].strip(),
                        request.form["roll_no"].strip(),
                        request.form["email"].strip(),
                        request.form["course"].strip(),
                        int(request.form["year"]),
                        student_id
                    )
                )

                flash("Student updated successfully.", "success")
                return redirect(url_for("index"))

            except sqlite3.IntegrityError:
                flash("Roll number already exists.", "error")

    return render_template(
        "form.html",
        student=student
    )


@app.post("/delete/<int:student_id>")
def delete_student(student_id):
    with get_db() as conn:
        conn.execute(
            """
            DELETE FROM students
            WHERE id = ?
            """,
            (student_id,)
        )

    flash("Student deleted.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)