import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from datetime import datetime # Import datetime

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'  # Change this for production!

# Define DB_FILE relative to this script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'library_data.json')

# --- Database Helper Functions ---

def load_data():
    """Loads data from the JSON database file."""
    if not os.path.exists(DB_FILE):
        # Create default structure if file doesn't exist
        return {"books": {}, "students": {}, "next_book_id": 1, "next_student_id": 101}
    try:
        with open(DB_FILE, 'r') as f:
            # Ensure default keys exist if file is empty or partially formed
            data = json.load(f)
            data.setdefault("books", {})
            data.setdefault("students", {})
            data.setdefault("next_book_id", 1)
            data.setdefault("next_student_id", 101)
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        # Handle corrupted or missing file scenario
        flash("Error loading database. Creating a new one.", "error")
        return {"books": {}, "students": {}, "next_book_id": 1, "next_student_id": 101}

def save_data(data):
    """Saves data to the JSON database file."""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2) # Use indent for readability
    except IOError:
        flash("Error saving data to the database.", "error")

def get_next_id(data, type='book'):
    """Generates the next unique ID for books or students."""
    if type == 'book':
        next_id_num = data.get('next_book_id', 1)
        next_id_str = f"B{next_id_num:03d}" # e.g., B001, B010, B100
        data['next_book_id'] = next_id_num + 1
    else: # student
        next_id_num = data.get('next_student_id', 101)
        next_id_str = f"S{next_id_num:03d}" # e.g., S101, S110, S200
        data['next_student_id'] = next_id_num + 1
    return next_id_str

# --- Context Processor to make 'now' available globally --- 
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow}

# --- Routes ---

@app.route('/')
def index():
    """Home page."""
    data = load_data()
    return render_template('index.html',
                           book_count=len(data.get('books', {})),
                           student_count=len(data.get('students', {})))

# --- Book Routes ---

@app.route('/books')
def list_books():
    """Display list of all books."""
    data = load_data()
    books = data.get('books', {})
    return render_template('books.html', books=books)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    """Add a new book."""
    if request.method == 'POST':
        data = load_data()
        name = request.form.get('name')
        author = request.form.get('author')
        genre = request.form.get('genre')
        shelf = request.form.get('shelf')
        language = request.form.get('language')

        if not all([name, author, genre, shelf, language]):
            flash('All book fields are required!', 'error')
            return redirect(url_for('add_book'))

        book_id = get_next_id(data, 'book')
        data['books'][book_id] = {
            'name': name,
            'book_id': book_id,
            'shelf': shelf,
            'author': author,
            'genre': genre,
            'borrowed_by': None, # New books aren't borrowed
            'language': language
        }
        save_data(data)
        flash(f'Book "{name}" added successfully with ID {book_id}!', 'success')
        return redirect(url_for('list_books'))

    return render_template('add_book.html')

@app.route('/books/remove/<book_id>', methods=['POST'])
def remove_book(book_id):
    """Remove a book."""
    data = load_data()
    book = data['books'].get(book_id)

    if not book:
        flash(f'Book with ID {book_id} not found.', 'error')
    elif book.get('borrowed_by'):
        flash(f'Cannot remove "{book["name"]}". It is currently borrowed by student {book["borrowed_by"]}.', 'error')
    else:
        removed_name = data['books'].pop(book_id)['name']
        save_data(data)
        flash(f'Book "{removed_name}" (ID: {book_id}) removed successfully.', 'success')

    return redirect(url_for('list_books'))

@app.route('/book/<book_id>')
def book_profile(book_id):
    """Show profile for a specific book."""
    data = load_data()
    book = data.get('books', {}).get(book_id)
    if not book:
        abort(404, description="Book not found") # Use abort for not found

    borrower_name = None
    if book.get('borrowed_by'):
        borrower = data.get('students', {}).get(book.get('borrowed_by'))
        if borrower:
            borrower_name = borrower.get('name')

    return render_template('book_profile.html', book=book, borrower_name=borrower_name)


# --- Student Routes ---

@app.route('/students')
def list_students():
    """Display list of all students."""
    data = load_data()
    students = data.get('students', {})
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
def add_student():
    """Add a new student."""
    if request.method == 'POST':
        data = load_data()
        name = request.form.get('name')

        if not name:
            flash('Student name is required!', 'error')
            return redirect(url_for('add_student'))

        student_id = get_next_id(data, 'student')
        data['students'][student_id] = {
            'name': name,
            'student_id': student_id,
            'borrowed_books': [] # New students have no books
        }
        save_data(data)
        flash(f'Student "{name}" added successfully with ID {student_id}!', 'success')
        return redirect(url_for('list_students'))

    return render_template('add_student.html')

@app.route('/students/remove/<student_id>', methods=['POST'])
def remove_student(student_id):
    """Remove a student."""
    data = load_data()
    student = data['students'].get(student_id)

    if not student:
        flash(f'Student with ID {student_id} not found.', 'error')
    elif student.get('borrowed_books'):
        flash(f'Cannot remove "{student["name"]}". They still have borrowed books.', 'error')
    else:
        removed_name = data['students'].pop(student_id)['name']
        save_data(data)
        flash(f'Student "{removed_name}" (ID: {student_id}) removed successfully.', 'success')

    return redirect(url_for('list_students'))

@app.route('/student/<student_id>')
def student_profile(student_id):
    """Show profile for a specific student."""
    data = load_data()
    student = data.get('students', {}).get(student_id)
    if not student:
        abort(404, description="Student not found")

    borrowed_book_details = []
    for book_id in student.get('borrowed_books', []):
        book = data.get('books', {}).get(book_id)
        if book:
            borrowed_book_details.append({'id': book_id, 'name': book.get('name', 'Unknown Title')})
        else:
             borrowed_book_details.append({'id': book_id, 'name': f'Unknown Book (ID: {book_id})'})


    return render_template('student_profile.html', student=student, borrowed_book_details=borrowed_book_details)


# --- Issue/Return Routes ---

@app.route('/issue', methods=['GET', 'POST'])
def issue_book():
    """Issue a book to a student."""
    data = load_data()
    # Books available for borrowing
    available_books = {bid: b for bid, b in data.get('books', {}).items() if not b.get('borrowed_by')}
    # Students who can borrow (less than 2 books)
    eligible_students = {sid: s for sid, s in data.get('students', {}).items() if len(s.get('borrowed_books', [])) < 2}

    if request.method == 'POST':
        book_id = request.form.get('book_id')
        student_id = request.form.get('student_id')

        book = data.get('books', {}).get(book_id)
        student = data.get('students', {}).get(student_id)

        # --- Validations ---
        if not book_id or not student_id:
            flash('Both Book and Student must be selected.', 'error')
        elif not book:
            flash(f'Selected book (ID: {book_id}) not found.', 'error')
        elif not student:
             flash(f'Selected student (ID: {student_id}) not found.', 'error')
        elif book.get('borrowed_by'):
            flash(f'Book "{book["name"]}" is already borrowed.', 'error')
        elif len(student.get('borrowed_books', [])) >= 2:
            flash(f'Student "{student["name"]}" has already borrowed the maximum (2) books.', 'error')
        else:
            # --- Perform Issue ---
            book['borrowed_by'] = student_id
            student.setdefault('borrowed_books', []).append(book_id) # Ensure list exists
            save_data(data)
            flash(f'Book "{book["name"]}" issued to "{student["name"]}" successfully.', 'success')
            return redirect(url_for('book_profile', book_id=book_id)) # Redirect to book profile

        # If POST fails validation, reload the form with current selections if possible
        return render_template('issue_book.html',
                               available_books=available_books,
                               eligible_students=eligible_students,
                               selected_book=book_id,
                               selected_student=student_id)

    # --- GET Request ---
    return render_template('issue_book.html',
                           available_books=available_books,
                           eligible_students=eligible_students)


@app.route('/return', methods=['GET', 'POST'])
def return_book():
    """Return a borrowed book."""
    data = load_data()
    # Books currently borrowed
    borrowed_books = {bid: b for bid, b in data.get('books', {}).items() if b.get('borrowed_by')}

    if request.method == 'POST':
        book_id = request.form.get('book_id')
        book = data.get('books', {}).get(book_id)

        # --- Validations ---
        if not book_id:
            flash('A book must be selected to return.', 'error')
        elif not book:
            flash(f'Selected book (ID: {book_id}) not found.', 'error')
        elif not book.get('borrowed_by'):
            flash(f'Book "{book["name"]}" is not currently borrowed.', 'error')
        else:
            # --- Perform Return ---
            student_id = book.get('borrowed_by')
            student = data.get('students', {}).get(student_id)

            book['borrowed_by'] = None # Set book as available
            if student and book_id in student.get('borrowed_books', []):
                student['borrowed_books'].remove(book_id) # Remove from student's list

            save_data(data)
            flash(f'Book "{book["name"]}" returned successfully.', 'success')
            return redirect(url_for('list_books')) # Redirect to book list

        # If POST fails validation, reload the form
        return render_template('return_book.html', borrowed_books=borrowed_books, selected_book=book_id)

    # --- GET Request ---
    return render_template('return_book.html', borrowed_books=borrowed_books)

# --- Search Route ---
@app.route('/search')
def search():
    query = request.args.get('query', '').strip().lower()
    search_type = request.args.get('type', 'book') # Default to searching books
    results = []
    data = load_data()

    if not query:
        flash("Please enter a search term.", "info")
        return render_template('search_results.html', query=query, results=results, search_type=search_type)

    if search_type == 'book':
        for book_id, book in data.get('books', {}).items():
            if query in book.get('name', '').lower() or \
               query in book.get('author', '').lower() or \
               query in book.get('genre', '').lower() or \
               query == book_id.lower():
                 results.append(book)
    elif search_type == 'student':
        for student_id, student in data.get('students', {}).items():
             if query in student.get('name', '').lower() or \
                query == student_id.lower():
                 results.append(student)

    return render_template('search_results.html', query=query, results=results, search_type=search_type)

# --- Error Handling ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error=e), 404

# --- Run the App ---
if __name__ == '__main__':
    # Ensure the path uses the correct separator for the OS if needed, 
    # but os.path.join handles this.
    print(f"Database file path: {DB_FILE}") # Optional: print path for debugging
    app.run(host='0.0.0.0', debug=True) # debug=True for development, remove for production