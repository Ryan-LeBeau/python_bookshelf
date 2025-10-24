# python_bookshelf
A simple program I made to digitize my bookshelf, including cover art, author, and ISBN number using google books API

To adding a new book, enter the title and click 'Add Book'. This will open another window where you can select from various cover arts, if the book has had several printings, you can select the one that matches your shelf (though some options are missing, I know that the Jim Tierney covers for Children of Dune and God Emperor of Dune don't pop up). 

Book data is stored in a .txt file the program creates and is placed in the current working directory the program is run in. If it is moved, the program will create a new empty one.

To install required packages: pip install pillow requests
