from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "bliss_2025"

DB_PATH = "bliss_reservation.db"
ADMIN_PASSWORD = "admin123"

MENU_DATA = [
    {
        "category": "Food",
        "description": "Fresh meals and snacks",
        "items": [
            {"name": "Chicken Sandwich", "price": "180 ден"},
            {"name": "Club Sandwich", "price": "220 ден"},
            {"name": "Toast Ham & Cheese", "price": "150 ден"},
            {"name": "Chicken Wrap", "price": "200 ден"},
        ],
    },
    {
        "category": "Coffee",
        "description": "Hot and cold coffee drinks",
        "items": [
            {"name": "Espresso", "price": "70 ден"},
            {"name": "Macchiato", "price": "80 ден"},
            {"name": "Cappuccino", "price": "100 ден"},
            {"name": "Latte", "price": "110 ден"},
        ],
    },
    {
        "category": "Drinks",
        "description": "Soft drinks and fresh drinks",
        "items": [
            {"name": "Coca Cola", "price": "90 ден"},
            {"name": "Fanta", "price": "90 ден"},
            {"name": "Lemonade", "price": "70 ден"},
            {"name": "Fresh Orange Juice", "price": "150 ден"},
        ],
    },
]

TABLES = [
    {"id": 1, "seats": 2},
    {"id": 2, "seats": 2},
    {"id": 3, "seats": 4},
    {"id": 4, "seats": 4},
    {"id": 5, "seats": 4},
    {"id": 6, "seats": 6},
    {"id": 7, "seats": 2},
    {"id": 8, "seats": 4},
    {"id": 9, "seats": 6},
]


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            guests INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            reservation_time TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("index.html", menu=MENU_DATA)


@app.route("/menu")
def menu():
    return render_template("menu.html", menu=MENU_DATA)


@app.route("/reserve")
def reserve_map():
    return render_template("reserve_map.html", tables=TABLES)


@app.route("/reserve/<int:table_id>", methods=["GET", "POST"])
def reserve_form(table_id):
    selected_table = next((table for table in TABLES if table["id"] == table_id), None)

    if selected_table is None:
        flash("This table does not exist.")
        return redirect(url_for("reserve_map"))

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        guests = request.form.get("guests", "").strip()
        reservation_date = request.form.get("reservation_date", "").strip()
        reservation_time = request.form.get("reservation_time", "").strip()
        notes = request.form.get("notes", "").strip()

        if (
            not customer_name
            or not phone
            or not guests
            or not reservation_date
            or not reservation_time
        ):
            flash("Please fill in all required fields.")
            return redirect(url_for("reserve_form", table_id=table_id))

        connection = get_db_connection()

        existing_reservation = connection.execute(
            """
            SELECT id FROM reservations
            WHERE table_id = ?
            AND reservation_date = ?
            AND reservation_time = ?
            AND status IN ('pending', 'confirmed')
            """,
            (table_id, reservation_date, reservation_time),
        ).fetchone()

        if existing_reservation:
            connection.close()
            flash(
                "This table is already reserved or waiting confirmation at that time."
            )
            return redirect(url_for("reserve_form", table_id=table_id))

        connection.execute(
            """
            INSERT INTO reservations (
                table_id,
                customer_name,
                phone,
                guests,
                reservation_date,
                reservation_time,
                notes,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                table_id,
                customer_name,
                phone,
                int(guests),
                reservation_date,
                reservation_time,
                notes,
                "pending",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        connection.commit()
        connection.close()

        return redirect(url_for("success"))

    return render_template("reserve_form.html", table=selected_table)


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
def admin():
    pin = request.args.get("pin", "")

    if pin != ADMIN_PASSWORD:
        return "Unauthorized"

    connection = get_db_connection()

    reservations = connection.execute(
        """
        SELECT * FROM reservations
        ORDER BY
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'confirmed' THEN 2
                WHEN 'rejected' THEN 3
            END,
            reservation_date ASC,
            reservation_time ASC
        """
    ).fetchall()

    connection.close()

    return render_template("admin.html", reservations=reservations, pin=pin)


@app.route("/admin/reservation/<int:reservation_id>/<action>", methods=["POST"])
def update_reservation(reservation_id, action):
    pin = request.form.get("pin", "")

    if pin != ADMIN_PASSWORD:
        return "Unauthorized"

    if action not in ["confirm", "reject"]:
        return "Invalid action"

    new_status = "confirmed" if action == "confirm" else "rejected"

    connection = get_db_connection()
    connection.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE id = ?
        """,
        (new_status, reservation_id),
    )
    connection.commit()
    connection.close()

    return redirect(url_for("admin", pin=pin))


@app.route("/placeholder/<path:text>")
def placeholder(text):
    safe_text = text[:24]
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">
        <rect width="100%" height="100%" fill="#f4eadc"/>
        <circle cx="300" cy="155" r="72" fill="#d8b27c"/>
        <rect x="150" y="250" width="300" height="42" rx="21" fill="#3b2417"/>
        <text x="300" y="335" text-anchor="middle" font-size="32" font-family="Arial" fill="#3b2417">
            {safe_text}
        </text>
    </svg>
    """
    return Response(svg, mimetype="image/svg+xml")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
