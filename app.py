from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SECRET_KEY'] = 'some477thing0983'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Bookshelf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    books = db.relationship('Book', backref='bookshelf', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    bookshelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.id'), nullable=True)

class ShoppingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    book = db.relationship('Book', backref='shopping_list_items', lazy=True)

@app.route('/shopping-list/add', methods=['POST'])
def add_to_shopping_list():
    book_ids = request.form.getlist('selected_books')
    for book_id in book_ids:
        shopping_list_item = ShoppingList(book_id=book_id)
        db.session.add(shopping_list_item)
    db.session.commit()
    flash('Books added to shopping list successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/shopping-list', methods=['GET'])
def shopping_list():
    shopping_list_items = ShoppingList.query.all()
    return render_template('shopping_list.html', shopping_list_items=shopping_list_items)

@app.route('/bookshelves', methods=['GET', 'POST'])
def bookshelves():
    if request.method == 'POST':
        name = request.form['name']
        new_bookshelf = Bookshelf(name=name)
        db.session.add(new_bookshelf)
        db.session.commit()
        return redirect(url_for('bookshelves'))
    bookshelves = Bookshelf.query.all()
    return render_template('bookshelves.html', bookshelves=bookshelves)

@app.route('/api/bookshelves', methods=['GET'])
def api_bookshelves():
    bookshelves = Bookshelf.query.all()
    return jsonify([{'id': b.id, 'name': b.name} for b in bookshelves])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        bookshelf_id = request.form['bookshelf']
        bookshelf = Bookshelf.query.get(bookshelf_id) if bookshelf_id else None

        book = Book(title=title, author=author, bookshelf=bookshelf)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')

    title_filter = request.args.get('title', '')
    author_filter = request.args.get('author', '')
    bookshelf_filter = request.args.get('bookshelf', '')

    query = Book.query.join(Bookshelf)

    if title_filter:
        query = query.filter(Book.title.ilike(f"%{title_filter}%"))
    if author_filter:
        query = query.filter(Book.author.ilike(f"%{author_filter}%"))
    if bookshelf_filter:
        query = query.filter(Bookshelf.id == bookshelf_filter)

    books = query.order_by(Book.id.desc()).all()
    bookshelves = Bookshelf.query.all()
    return render_template('index.html', books=books, bookshelves=bookshelves)


@app.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        bookshelf_id = request.form['bookshelf']
        book.bookshelf = Bookshelf.query.get(bookshelf_id) if bookshelf_id else None
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('index'))

    bookshelves = Bookshelf.query.order_by(Bookshelf.id.desc()).all()
    return render_template('edit_book.html', book=book, bookshelves=bookshelves)

@app.route('/add', methods=['GET'])
def add_book_form():
    bookshelves = Bookshelf.query.order_by(Bookshelf.id.desc()).all()
    return render_template('add_book.html', bookshelves=bookshelves)

@app.route('/delete/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

def init_db():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)