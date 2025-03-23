# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime, timedelta

# Flask config
app = Flask(__name__)
app.secret_key = 'some_random_secret_key'

DATABASE = 'library.db'

def init_db():
    """Creates the tables in library.db if they don't exist."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # 1) customers table
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            dob TEXT,
            address TEXT,
            preferences TEXT,
            outstanding_fine_balance REAL DEFAULT 0.0
        )
    ''')

    # 2) library_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS library_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            item_type TEXT,
            format TEXT,
            genre TEXT,
            published_date TEXT,
            availability TEXT DEFAULT 'Available',
            is_future_item BOOLEAN DEFAULT 0,
            restriction INTEGER DEFAULT 0
        )
    ''')

    # 3) borrowing table
    c.execute('''
        CREATE TABLE IF NOT EXISTS borrowing (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            borrowed_date TEXT,
            due_date TEXT,
            returned_date TEXT,
            amount_of_fine REAL DEFAULT 0.0,
            FOREIGN KEY (item_id) REFERENCES library_items(item_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # 4) fines table
    c.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount_of_fine REAL,
            fine_status TEXT DEFAULT 'Unpaid',
            FOREIGN KEY (transaction_id) REFERENCES borrowing(transaction_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # 5) events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            event_description TEXT,
            event_type TEXT,
            targeted_customers TEXT,
            restriction INTEGER DEFAULT 0,
            location TEXT,
            datetime TEXT,
            capacity INTEGER
        )
    ''')

    # 6) register table (join table between customers & events)
    c.execute('''
        CREATE TABLE IF NOT EXISTS register (
            register_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # 7) personnel table
    c.execute('''
        CREATE TABLE IF NOT EXISTS personnel (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            address TEXT,
            email TEXT,
            phone TEXT,
            salary REAL,
            job_role TEXT
        )
    ''')

    # 8) manage table (join table between personnel & events)
    c.execute('''
        CREATE TABLE IF NOT EXISTS manage (
            manage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            FOREIGN KEY (employee_id) REFERENCES personnel(employee_id)
        )
    ''')


    conn.commit()
    conn.close()

def get_db_connection():
    """Helper function to connect to the SQLite DB with row dictionary factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Home Page."""
    return render_template('index.html')

# -----------------------------------------------------
# (1) FIND AN ITEM /items
# -----------------------------------------------------
@app.route('/items')
def list_items():
    """List library items, optionally searching by query q."""
    search_query = request.args.get('q', '')
    conn = get_db_connection()
    c = conn.cursor()
    if search_query:
        c.execute(
            """
            SELECT * FROM library_items
            WHERE title LIKE ? OR author LIKE ?
            """,
            (f'%{search_query}%', f'%{search_query}%')
        )
    else:
        c.execute("SELECT * FROM library_items")
    items = c.fetchall()
    conn.close()
    return render_template('items.html', items=items, search_query=search_query)

# -----------------------------------------------------
# (2) BORROW AN ITEM /borrow/<item_id>
# -----------------------------------------------------
@app.route('/borrow/<int:item_id>', methods=['GET', 'POST'])
def borrow_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()

    # GET -> show form
    if request.method == 'GET':
        c.execute("SELECT * FROM library_items WHERE item_id = ?", (item_id,))
        item = c.fetchone()
        if not item:
            flash("Item not found.", "danger")
            conn.close()
            return redirect(url_for('list_items'))
        return render_template('borrow_item.html', item=item)

    # POST -> process borrow
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        borrowed_date = request.form.get('borrowed_date')
        # due_date = request.form.get('due_date')

        # Calculate due date (2 weeks after borrowed date)
        borrowed_date_obj = datetime.strptime(borrowed_date, '%Y-%m-%d')
        due_date_obj = borrowed_date_obj + timedelta(weeks=2)
        due_date = due_date_obj.strftime('%Y-%m-%d')

        # Insert new borrowing record
        c.execute('''
            INSERT INTO borrowing (item_id, customer_id, borrowed_date, due_date)
            VALUES (?, ?, ?, ?)
        ''', (item_id, customer_id, borrowed_date, due_date))

        # Update item availability
        c.execute("UPDATE library_items SET availability = 'Borrowed' WHERE item_id = ?", (item_id,))

        conn.commit()
        conn.close()
        flash("Item borrowed successfully!", "success")
        return redirect(url_for('list_items'))

# -----------------------------------------------------
# (3) RETURN AN ITEM /return/<transaction_id>
# -----------------------------------------------------
@app.route('/return', methods=['GET', 'POST'])
def return_item():
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'GET':
        # Render the page with a form to input transaction_id
        conn.close()
        return render_template('return_item.html', transaction=None, item=None)

    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        returned_date = request.form.get('returned_date')
        amount_of_fine = request.form.get('amount_of_fine', 0)

        if not transaction_id:
            flash("Please enter a valid Transaction ID.", "danger")
            conn.close()
            return redirect(url_for('return_item'))

        # Fetch the transaction details
        c.execute("SELECT * FROM borrowing WHERE transaction_id = ?", (transaction_id,))
        transaction = c.fetchone()
        if not transaction:
            flash("Transaction not found.", "danger")
            conn.close()
            return redirect(url_for('return_item'))

        # Update the borrowing record with the returned date and fine
        c.execute('''
            UPDATE borrowing
            SET returned_date = ?, amount_of_fine = ?
            WHERE transaction_id = ?
        ''', (returned_date, amount_of_fine, transaction_id))

        # Update the item's availability to 'Available'
        c.execute('''
            UPDATE library_items
            SET availability = 'Available'
            WHERE item_id = ?
        ''', (transaction['item_id'],))

        conn.commit()
        conn.close()

        flash("Item returned successfully!", "success")
        return redirect(url_for('list_items'))
# -----------------------------------------------------
# (4) DONATE AN ITEM /donate
# -----------------------------------------------------
@app.route('/donate', methods=['GET', 'POST'])
def donate_item():
    if request.method == 'GET':
        return render_template('donate.html')

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        item_type = request.form.get('item_type')
        format_ = request.form.get('format')
        genre = request.form.get('genre')
        published_date = request.form.get('published_date')
        restriction = request.form.get('restriction', 0)
        is_future_item = 0

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO library_items (
                title, author, item_type, format, genre, published_date, availability,
                is_future_item, restriction
            )
            VALUES (?, ?, ?, ?, ?, ?, 'Available', ?, ?)
        ''', (title, author, item_type, format_, genre, published_date, is_future_item, restriction))
        conn.commit()
        conn.close()

        flash("Thank you for donating the item!", "success")
        return redirect(url_for('list_items'))

# -----------------------------------------------------
# (5) FIND AN EVENT /events
# -----------------------------------------------------
@app.route('/events', methods=['GET', 'POST'])
def list_events():
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch all events
    c.execute("SELECT * FROM events")
    events = c.fetchall()

    # Handle registration form submission
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        customer_id = request.form.get('customer_id')

        # Insert registration into the database
        c.execute('''
            INSERT INTO registered_events (event_id, customer_id)
            VALUES (?, ?)
        ''', (event_id, customer_id))
        conn.commit()
        flash("You have successfully registered for the event!", "success")
        conn.close()
        return redirect(url_for('list_events'))

    conn.close()
    return render_template('register_event.html', events=events)

# -----------------------------------------------------
# (6) REGISTER FOR AN EVENT /register_event/<event_id>
# -----------------------------------------------------
@app.route('/register_event/<int:event_id>', methods=['GET', 'POST'])
def register_event(event_id):
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'GET':
        c.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        event = c.fetchone()
        if not event:
            flash("Event not found.", "danger")
            conn.close()
            return redirect(url_for('list_events'))
        conn.close()
        return render_template('register_event.html', event=event)

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        c.execute('''
            INSERT INTO register (event_id, customer_id)
            VALUES (?, ?)
        ''', (event_id, customer_id))
        conn.commit()
        conn.close()
        flash("You have registered for the event!", "success")
        return redirect(url_for('list_events'))

# -----------------------------------------------------
# (7) VOLUNTEER FOR THE LIBRARY /volunteer
# -----------------------------------------------------
@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    if request.method == 'GET':
        return render_template('volunteer.html')

    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        salary = request.form.get('salary', 0)
        job_role = request.form.get('job_role', 'Volunteer')

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO personnel (name, dob, address, email, phone, salary, job_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, dob, address, email, phone, salary, job_role))
        conn.commit()
        conn.close()
        flash("Thank you for volunteering!", "success")
        return redirect(url_for('index'))

# -----------------------------------------------------
# (8) ASK FOR HELP FROM A LIBRARIAN /ask_librarian
# -----------------------------------------------------
@app.route('/ask_librarian', methods=['GET', 'POST'])
def ask_librarian():
    if request.method == 'GET':
        return render_template('ask_librarian.html')

    if request.method == 'POST':
        question = request.form.get('question')
        # In a real system, you'd store the question or send an email, etc.
        flash("Your question has been received. A librarian will contact you soon.", "success")
        return redirect(url_for('index'))
    

# -----------------------------------------------------
# (9) CREATE A NEW CUSTOMER ACCOUNT
# -----------------------------------------------------
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'GET':
        # Render the form to add a new customer
        return render_template('add_customer.html')

    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob = request.form.get('dob')
        address = request.form.get('address')
        preferences = request.form.get('preferences')
        outstanding_fine_balance = request.form.get('outstanding_fine_balance', 0.0)

        # Insert the new customer into the database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO customers (name, email, phone, dob, address, preferences, outstanding_fine_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, dob, address, preferences, outstanding_fine_balance))
        conn.commit()

        # Fetch the newly created customer's information
        customer_id = c.lastrowid
        c.execute('SELECT * FROM customers WHERE customer_id = ?', (customer_id,))
        customer = c.fetchone()
        conn.close()

        # Redirect to the completion page with customer details
        return render_template('completion.html', customer=customer)

if __name__ == '__main__':
    # Initialize the DB
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # If DB exists, we could call init_db() again if we want to ensure tables
        # but that might drop data in some designs. We won't call it by default.
        init_db()

    app.run(debug=True)


