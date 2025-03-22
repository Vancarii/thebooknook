import sqlite3

DATABASE = 'library.db'

def populate_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Populate customers table
    c.executemany('''
        INSERT INTO customers (name, email, phone, dob, address, outstanding_fine_balance)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        ('Alice Johnson', 'alice@example.com', '123-456-7890', '1990-05-15', '123 Main St', 0.0),
        ('Bob Smith', 'bob@example.com', '987-654-3210', '1985-08-22', '456 Elm St', 5.0),
        ('Charlie Brown', 'charlie@example.com', '555-123-4567', '2000-01-10', '789 Oak St', 0.0),
        ('Diana Prince', 'diana@example.com', '444-555-6666', '1995-03-25', '321 Maple St', 2.5),
        ('Eve Adams', 'eve@example.com', '333-444-5555', '1992-07-18', '654 Pine St', 0.0),
        ('Frank Castle', 'frank@example.com', '222-333-4444', '1988-11-11', '987 Birch St', 0.0),
        ('Grace Hopper', 'grace@example.com', '111-222-3333', '1991-09-09', '123 Cedar St', 0.0),
        ('Hank Pym', 'hank@example.com', '999-888-7777', '1980-06-06', '456 Spruce St', 0.0),
        ('Ivy League', 'ivy@example.com', '666-555-4444', '1993-03-03', '789 Willow St', 0.0),
        ('Jack Ryan', 'jack@example.com', '333-222-1111', '1987-12-12', '321 Aspen St', 0.0)
    ])

    # Populate library_items table
    c.executemany('''
        INSERT INTO library_items (title, author, item_type, format, genre, published_date, availability, is_future_item, restriction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('The Great Gatsby', 'F. Scott Fitzgerald', 'Book', 'Print', 'Fiction', '1925-04-10', 'Available', 0, 0),
        ('1984', 'George Orwell', 'Book', 'Print', 'Dystopian', '1949-06-08', 'Borrowed', 0, 0),
        ('To Kill a Mockingbird', 'Harper Lee', 'Book', 'Print', 'Fiction', '1960-07-11', 'Available', 0, 0),
        ('The Catcher in the Rye', 'J.D. Salinger', 'Book', 'Print', 'Fiction', '1951-07-16', 'Available', 0, 0),
        ('The Beatles: Abbey Road', 'The Beatles', 'CD', 'Audio', 'Music', '1969-09-26', 'Available', 0, 0),
        ('The Matrix', 'Wachowski Brothers', 'DVD', 'Video', 'Sci-Fi', '1999-03-31', 'Available', 0, 13),
        ('National Geographic', 'Various', 'Magazine', 'Print', 'Science', '2025-01-01', 'Available', 0, 0),
        ('Python Programming', 'Guido van Rossum', 'Book', 'Print', 'Education', '2010-05-01', 'Available', 0, 0),
        ('The Art of War', 'Sun Tzu', 'Book', 'Print', 'Philosophy', '500 BC', 'Available', 0, 0),
        ('The Hobbit', 'J.R.R. Tolkien', 'Book', 'Print', 'Fantasy', '1937-09-21', 'Available', 0, 0)
    ])

    # Populate borrowing table
    c.executemany('''
        INSERT INTO borrowing (item_id, customer_id, borrowed_date, due_date, returned_date, amount_of_fine)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [
        (2, 1, '2025-03-01', '2025-03-15', None, 0.0),
        (3, 2, '2025-02-20', '2025-03-05', '2025-03-06', 1.0),
        (1, 3, '2025-03-10', '2025-03-24', None, 0.0),
        (4, 4, '2025-03-12', '2025-03-26', None, 0.0),
        (5, 5, '2025-03-15', '2025-03-29', None, 0.0),
        (6, 6, '2025-03-20', '2025-04-03', None, 0.0),
        (7, 7, '2025-03-22', '2025-04-05', None, 0.0),
        (8, 8, '2025-03-25', '2025-04-08', None, 0.0),
        (9, 9, '2025-03-27', '2025-04-10', None, 0.0),
        (10, 10, '2025-03-30', '2025-04-13', None, 0.0)
    ])

    # Populate events table
    c.executemany('''
        INSERT INTO events (event_name, event_description, event_type, targeted_customers, restriction, location, datetime, capacity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Book Club', 'Discussing the latest bestsellers.', 'Discussion', 'Adults', 0, 'Room A', '2025-03-25 18:00', 20),
        ('Art Show', 'Exhibition of local artists.', 'Exhibition', 'All Ages', 0, 'Room B', '2025-03-30 14:00', 50),
        ('Film Screening', 'Classic movie night.', 'Screening', 'Teens', 13, 'Room C', '2025-04-05 19:00', 30),
        ('Coding Workshop', 'Learn Python programming.', 'Workshop', 'Adults', 0, 'Room D', '2025-04-10 10:00', 15),
        ('Story Time', 'Stories for kids.', 'Reading', 'Kids', 0, 'Room E', '2025-04-15 11:00', 25),
        ('Poetry Night', 'Share and listen to poetry.', 'Reading', 'Adults', 0, 'Room F', '2025-04-20 19:00', 30),
        ('Chess Tournament', 'Compete in a chess tournament.', 'Competition', 'All Ages', 0, 'Room G', '2025-04-25 14:00', 20),
        ('Photography Workshop', 'Learn photography basics.', 'Workshop', 'Teens', 13, 'Room H', '2025-04-30 10:00', 15),
        ('Music Night', 'Live music performances.', 'Performance', 'All Ages', 0, 'Room I', '2025-05-05 18:00', 40),
        ('Science Fair', 'Explore science projects.', 'Exhibition', 'Kids', 0, 'Room J', '2025-05-10 12:00', 50)
    ])

    # Populate registered_events table
    c.executemany('''
        INSERT INTO registered_events (event_id, customer_id)
        VALUES (?, ?)
    ''', [
        (1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
        (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)
    ])

    # Populate personnel table
    c.executemany('''
        INSERT INTO personnel (name, dob, address, email, phone, salary, job_role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('John Doe', '1980-01-01', '123 Library St', 'john.doe@example.com', '123-456-7890', 50000, 'Librarian'),
        ('Jane Smith', '1990-02-15', '456 Library St', 'jane.smith@example.com', '987-654-3210', 45000, 'Assistant Librarian'),
        ('Mark Johnson', '1985-03-10', '789 Library St', 'mark.johnson@example.com', '555-123-4567', 0, 'Volunteer'),
        ('Emily Davis', '1995-07-20', '321 Library St', 'emily.davis@example.com', '444-555-6666', 0, 'Volunteer'),
        ('Michael Brown', '1988-11-11', '654 Library St', 'michael.brown@example.com', '333-444-5555', 60000, 'Manager'),
        ('Sarah Connor', '1982-05-12', '987 Library St', 'sarah.connor@example.com', '222-333-4444', 55000, 'Event Coordinator'),
        ('Tom Hardy', '1993-08-25', '654 Library St', 'tom.hardy@example.com', '111-222-3333', 0, 'Volunteer'),
        ('Anna Bell', '1996-09-15', '321 Library St', 'anna.bell@example.com', '999-888-7777', 0, 'Volunteer'),
        ('Chris Evans', '1987-07-04', '123 Library St', 'chris.evans@example.com', '666-555-4444', 70000, 'Director'),
        ('Natalie Portman', '1992-03-22', '456 Library St', 'natalie.portman@example.com', '333-222-1111', 0, 'Volunteer')
    ])

    # Populate event_personnel table
    c.executemany('''
        INSERT INTO event_personnel (event_id, employee_id)
        VALUES (?, ?)
    ''', [
        (1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
        (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)
    ])

    # Populate fines table
    c.executemany('''
        INSERT INTO fines (transaction_id, customer_id, amount_of_fine, fine_status)
        VALUES (?, ?, ?, ?)
    ''', [
        (1, 1, 0.0, 'Paid'), (2, 2, 1.0, 'Paid'), (3, 3, 2.5, 'Unpaid'),
        (4, 4, 0.0, 'Paid'), (5, 5, 0.0, 'Paid'), (6, 6, 0.0, 'Paid'),
        (7, 7, 0.0, 'Paid'), (8, 8, 0.0, 'Paid'), (9, 9, 0.0, 'Paid'),
        (10, 10, 0.0, 'Paid')
    ])

    conn.commit()
    conn.close()
    print("Database tables populated successfully!")

if __name__ == '__main__':
    populate_tables()