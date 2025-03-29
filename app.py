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
            email TEXT UNIQUE,
            phone TEXT,
            dob TEXT NOT NULL,
            address TEXT,
            preferences TEXT,
            outstanding_fine_balance REAL DEFAULT 0.0 CHECK (outstanding_fine_balance >= 0)
        )
    ''')

    # 2) library_items table
    c.execute('''
        CREATE TABLE IF NOT EXISTS library_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            item_type TEXT CHECK (item_type IN ('Book', 'CD', 'DVD', 'Magazine', 'Journal', 'Record')),
            format TEXT CHECK (format IN ('Print', 'Online', 'Audio', 'Video')),
            genre TEXT,
            published_date TEXT,
            availability TEXT DEFAULT 'Available' CHECK (availability IN ('Available', 'Borrowed')),
            is_future_item BOOLEAN DEFAULT 0 CHECK (is_future_item IN (0, 1)),
            restriction INTEGER DEFAULT 0 CHECK (restriction >= 0)
        )
    ''')

    # 3) borrowing table
    c.execute('''
        CREATE TABLE IF NOT EXISTS borrowing (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            borrowed_date TEXT NOT NULL,
            due_date TEXT,
            returned_date TEXT,
            amount_of_fine REAL DEFAULT 0.0 CHECK (amount_of_fine >= 0),
            FOREIGN KEY (item_id) REFERENCES library_items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )
    ''')

    # 4) fines table
    c.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            amount_of_fine REAL NOT NULL CHECK (amount_of_fine >= 0),
            fine_status TEXT DEFAULT 'Unpaid' CHECK (fine_status IN ('Paid', 'Unpaid')),
            FOREIGN KEY (transaction_id) REFERENCES borrowing(transaction_id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )
    ''')

    # 5) events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_description TEXT,
            event_type TEXT CHECK (event_type IN ('Workshop', 'Seminar', 'Film Screening', 'Book Club', 'Art Show')),
            targeted_customers TEXT,
            restriction INTEGER DEFAULT 0 CHECK (restriction >= 0),
            location TEXT,
            datetime TEXT NOT NULL,
            capacity INTEGER CHECK (capacity >= 0)
        )
    ''')

    # 6) register table (join table between customers & events)
    c.execute('''
        CREATE TABLE IF NOT EXISTS register (
            register_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )
    ''')

    # 7) personnel table
    c.execute('''
        CREATE TABLE IF NOT EXISTS personnel (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            address TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            salary REAL DEFAULT 0.0 CHECK (salary >= 0),
            job_role TEXT NOT NULL
        )
    ''')

    # 8) manage table (join table between personnel & events)
    c.execute('''
        CREATE TABLE IF NOT EXISTS manage (
            manage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES personnel(employee_id) ON DELETE CASCADE
        )
    ''')

    # TRIGGERS --------------------------------------------

    # Trigger to update item availability in library_items table when insert on borrowing table
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_item_borrowed
        AFTER INSERT ON borrowing
        BEGIN
            UPDATE library_items
            SET availability = 'Borrowed'
            WHERE item_id = NEW.item_id;
        END;        
    ''')
    
    # Trigger to update item availability to Available when item returned
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_item_returned
        AFTER UPDATE ON borrowing 
        WHEN NEW.returned_date IS NOT NULL AND OLD.returned_date IS NULL
        BEGIN
            UPDATE library_items
            SET availability = 'Available'
            WHERE item_id = NEW.item_id;
        END;
    ''')

    # Trigger to update customer fine balance when a fine is added
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_customer_fine_balance
        AFTER INSERT ON fines
        BEGIN
            UPDATE customers
            SET outstanding_fine_balance = outstanding_fine_balance + NEW.amount_of_fine
            WHERE customer_id = NEW.customer_id;
        END;
    ''')

    # Trigger to update customer fine balance when a fine is paid
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_customer_fine_balance_paid
        AFTER UPDATE ON fines
        WHEN NEW.fine_status = 'Paid' AND OLD.fine_status = 'Unpaid'
        BEGIN
            UPDATE customers
            SET outstanding_fine_balance = outstanding_fine_balance - NEW.amount_of_fine
            WHERE customer_id = NEW.customer_id;
        END;
    ''')

    conn.commit()
    conn.close()

def get_db_connection():
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

        # Calculate due date (2 weeks after borrowed date)
        borrowed_date_obj = datetime.strptime(borrowed_date, '%Y-%m-%d')
        due_date_obj = borrowed_date_obj + timedelta(weeks=2)
        due_date = due_date_obj.strftime('%Y-%m-%d')

        # Insert new borrowing record
        c.execute('''
            INSERT INTO borrowing (item_id, customer_id, borrowed_date, due_date)
            VALUES (?, ?, ?, ?)
        ''', (item_id, customer_id, borrowed_date, due_date))
        
        # Get the transaction ID of the newly inserted record
        transaction_id = c.lastrowid
        
        # Get item details for the confirmation page
        c.execute("SELECT * FROM library_items WHERE item_id = ?", (item_id,))
        item = c.fetchone()
        
        # Get customer details
        c.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        customer = c.fetchone()

        conn.commit()
        conn.close()
        
        # Render a borrow confirmation page with transaction details
        return render_template('borrow_confirmation.html', 
                              transaction_id=transaction_id,
                              item=item,
                              customer=customer,
                              borrowed_date=borrowed_date,
                              due_date=due_date)

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
        # Check which form was submitted
        transaction_id = request.form.get('transaction_id')
        returned_date = request.form.get('returned_date')
        
        # Case 1: Just searching for a transaction
        if transaction_id and not returned_date:
            c.execute("SELECT * FROM borrowing WHERE transaction_id = ?", (transaction_id,))
            transaction = c.fetchone()
            
            if not transaction:
                flash("Transaction not found.", "danger")
                conn.close()
                return redirect(url_for('return_item'))
            
            # If it's already returned, show a message
            if transaction['returned_date']:
                flash(f"This item was already returned on {transaction['returned_date']}", "info")
                conn.close()
                return redirect(url_for('return_item'))
            
            # Get item details to display
            c.execute("SELECT * FROM library_items WHERE item_id = ?", (transaction['item_id'],))
            item = c.fetchone()
            
            conn.close()
            return render_template('return_item.html', transaction=transaction, item=item)
        
        # Case 2: Confirming the return
        elif transaction_id and returned_date:
            # Fetch the transaction details
            c.execute("SELECT * FROM borrowing WHERE transaction_id = ?", (transaction_id,))
            transaction = c.fetchone()
            
            if not transaction:
                flash("Transaction not found.", "danger")
                conn.close()
                return redirect(url_for('return_item'))
            
            # Calculate fine based on return date
            # If return date is more than 3 weeks after borrowed date, add fine
            borrowed_date_obj = datetime.strptime(transaction['borrowed_date'], '%Y-%m-%d')
            returned_date_obj = datetime.strptime(returned_date, '%Y-%m-%d')
            
            # Calculate days difference
            days_difference = (returned_date_obj - borrowed_date_obj).days
            
            # Set fine if more than 2 weeks (15 days)
            amount_of_fine = 0.0
            if days_difference > 15:
                # $1 per day after the 15-day period
                amount_of_fine = (days_difference - 15) * 1.0
            
            # Record fine if applicable
            if amount_of_fine > 0:
                c.execute('''
                    INSERT INTO fines (transaction_id, customer_id, amount_of_fine)
                    VALUES (?, ?, ?)
                ''', (transaction_id, transaction['customer_id'], amount_of_fine))
                
                flash(f"A fine of ${amount_of_fine:.2f} has been applied for late return.", "info")
            
            # Update the borrowing record with the returned date
            c.execute('''
                UPDATE borrowing
                SET returned_date = ?, amount_of_fine = ?
                WHERE transaction_id = ?
            ''', (returned_date, amount_of_fine, transaction_id))
            
            conn.commit()
            conn.close()
            
            flash("Item returned successfully!", "success")
            return redirect(url_for('list_items'))
        
        else:
            flash("Please enter a valid Transaction ID.", "danger")
            conn.close()
            return redirect(url_for('return_item'))
        
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
    search_query = request.args.get('q', '')

    if search_query:
        c.execute(
            """
            SELECT * FROM events
            WHERE event_name LIKE ? OR event_description LIKE ?
            """,
            (f'%{search_query}%', f'%{search_query}%')
        )
    else:
        c.execute("SELECT * FROM events")
    events = c.fetchall()

    # Handle registration form submission
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        customer_id = request.form.get('customer_id')

        # Insert registration into the database
        c.execute('''
            INSERT INTO register (event_id, customer_id)
            VALUES (?, ?)
        ''', (event_id, customer_id))
        conn.commit()
        flash("You have successfully registered for the event!", "success")
        conn.close()
        return redirect(url_for('list_events'))

    conn.close()
    return render_template('events.html', events=events)

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

        salary = 0.0  # Default salary for volunteers
        job_role = "Volunteer"  # Default job role for volunteers

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO personnel (name, dob, address, email, phone, salary, job_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, dob, address, email, phone, salary, job_role))
        
        # Get the employee ID of the newly inserted record
        employee_id = c.lastrowid
        
        # Get personnel details for the confirmation page
        c.execute("SELECT * FROM personnel WHERE employee_id = ?", (employee_id,))
        personnel = c.fetchone()
        
        conn.commit()
        conn.close()
        
        # Render a confirmation page with application details
        return render_template('volunteer_confirmation.html', personnel=personnel)

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


