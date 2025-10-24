import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os

BOOK_DB_FILE = "book_db.txt"

class Book:
    def __init__(self, title, authors, isbn, year, cover_url):
        self.title = title
        self.authors = authors
        self.isbn = isbn
        self.year = year
        self.cover_url = cover_url

    def to_csv(self):
        return f"{self.title},{self.authors},{self.isbn},{self.year},{self.cover_url}\n"

def fetch_book_options(title):
    url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}"
    response = requests.get(url)
    data = response.json()
    return data.get("items", [])

def choose_cover(book_data_list):
    picker = tk.Toplevel()
    picker.title("Choose a Cover")
    picker.geometry("800x300")

    selected_url = tk.StringVar()

    def select_cover(url):
        selected_url.set(url)
        picker.destroy()

    canvas = tk.Canvas(picker)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(picker, orient="horizontal", command=canvas.xview)
    scrollbar.pack(side="bottom", fill="x")
    canvas.configure(xscrollcommand=scrollbar.set)

    frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    for i, data in enumerate(book_data_list):
        info = data.get("volumeInfo", {})
        cover_url = info.get("imageLinks", {}).get("thumbnail", "")
        if cover_url:
            try:
                response = requests.get(cover_url)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((80, 120))
                photo = ImageTk.PhotoImage(img)

                btn = tk.Button(frame, image=photo, command=lambda url=cover_url: select_cover(url))
                btn.image = photo
                btn.grid(row=0, column=i, padx=5)
            except Exception as e:
                print("Error loading image:", e)

    frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    picker.wait_window()
    return selected_url.get()

def extract_book_info(data, chosen_cover_url):
    info = data.get("volumeInfo", {})
    title = info.get("title", "Unknown Title")
    authors_list = info.get("authors", [])
    authors = "Various" if len(authors_list) > 1 else (authors_list[0] if authors_list else "Unknown Author")
    isbn = next((id["identifier"] for id in info.get("industryIdentifiers", []) if "ISBN" in id["type"]), "N/A")
    year = info.get("publishedDate", "Unknown").split("-")[0]
    return Book(title, authors, isbn, year, chosen_cover_url)

class BookshelfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Bookshelf")
        self.books = []
        self.images = []

        self.setup_ui()
        self.load_books()

    def setup_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", pady=5)

        self.entry = ttk.Entry(top_frame, width=40)
        self.entry.pack(side="left", padx=5)

        self.add_button = ttk.Button(top_frame, text="Add Book", command=self.add_book)
        self.add_button.pack(side="left", padx=5)

        self.sort_var = tk.StringVar(value="Title")
        sort_menu = ttk.OptionMenu(top_frame, self.sort_var, "Title", "Title", "Author", command=self.sort_books)
        sort_menu.pack(side="right", padx=5)

        self.canvas = tk.Canvas(self.root, width=800, height=500)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Enable mouse and trackpad scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def add_book(self):
        title = self.entry.get()
        if not title:
            return

        book_data_list = fetch_book_options(title)
        if not book_data_list:
            print("No books found.")
            return

        chosen_cover_url = choose_cover(book_data_list)
        if not chosen_cover_url:
            print("No cover selected.")
            return

        selected_data = next((d for d in book_data_list if d.get("volumeInfo", {}).get("imageLinks", {}).get("thumbnail", "") == chosen_cover_url), book_data_list[0])
        book = extract_book_info(selected_data, chosen_cover_url)

        self.books.append(book)
        self.save_books()
        self.display_books()

    def save_books(self):
        with open(BOOK_DB_FILE, "w", encoding="utf-8") as f:
            f.write("Title,Authors,ISBN,Year,CoverURL\n")
            for book in self.books:
                f.write(book.to_csv())

    def load_books(self):
        if not os.path.exists(BOOK_DB_FILE):
            return

        with open(BOOK_DB_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[1:]

        for line in lines:
            parts = line.strip().split(",")
            if len(parts) < 5:
                continue
            title, authors, isbn, year, cover_url = parts
            book = Book(title, authors, isbn, year, cover_url)
            self.books.append(book)

        self.display_books()

    def sort_books(self, method=None):
        if method == "Author":
            self.books.sort(key=lambda b: b.authors.lower())
        #elif method == "Year":
         #   self.books.sort(key=lambda b: b.year)
        else:
            self.books.sort(key=lambda b: b.title.lower())
        self.display_books()

    def delete_book(self, book):
        self.books.remove(book)
        self.save_books()
        self.display_books()

    def display_books(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for index, book in enumerate(self.books):
            row = index // 5
            col = index % 5

            container = ttk.Frame(self.inner_frame, padding=5)
            container.grid(row=row, column=col, padx=10, pady=10)

            if book.cover_url:
                try:
                    response = requests.get(book.cover_url)
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data).resize((80, 120))
                    photo = ImageTk.PhotoImage(img)
                    self.images.append(photo)

                    img_label = ttk.Label(container, image=photo)
                    img_label.pack()
                except Exception as e:
                    print("Error loading image:", e)

            title_label = ttk.Label(container, text=book.title, font=("Arial", 10, "bold"), wraplength=100, justify="center")
            title_label.pack()

            author_label = ttk.Label(container, text=book.authors, font=("Arial", 9), wraplength=100, justify="center")
            author_label.pack()

            isbn_label = ttk.Label(container, text=f"ISBN: {book.isbn}", font=("Arial", 8), foreground="gray", wraplength=100, justify="center")
            isbn_label.pack()

            #year_label = ttk.Label(container, text=f"Year: {book.year}", font=("Arial", 8), foreground="gray", wraplength=100, justify="center")
            #year_label.pack()

            del_button = ttk.Button(container, text="🗑️", command=lambda b=book: self.delete_book(b))
            del_button.pack(pady=2)

if __name__ == "__main__":
    if not os.path.exists(BOOK_DB_FILE):
        with open(BOOK_DB_FILE, "w", encoding="utf-8") as f:
            f.write("Title,Authors,ISBN,Year,CoverURL\n")

    root = tk.Tk()
    app = BookshelfApp(root)
    root.mainloop()
