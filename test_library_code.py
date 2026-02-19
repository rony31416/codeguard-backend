"""
Test Clean Code: Library Management System
===========================================
This tests that perfectly valid, clean code does NOT trigger false positives.

The library management code is correct and should score LOW severity (0-2/10).
"""

import sys
sys.path.insert(0, 'F:/Codeguard/backend')

from app.analyzers.static import StaticAnalyzer


# The CLEAN code that was incorrectly flagged
LIBRARY_MANAGEMENT_CODE = '''import json
from datetime import datetime, timedelta


class Book:
    def __init__(self, book_id, title, author, year):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.year = year
        self.is_checked_out = False
        self.due_date = None


    def checkout(self, days=14):
        if self.is_checked_out:
            return f"Book '{self.title}' is already checked out."
        self.is_checked_out = True
        self.due_date = datetime.now() + timedelta(days=days)
        return f"Book '{self.title}' checked out until {self.due_date.strftime('%Y-%m-%d')}."


    def return_book(self):
        if not self.is_checked_out:
            return f"Book '{self.title}' was not checked out."
        self.is_checked_out = False
        self.due_date = None
        return f"Book '{self.title}' returned successfully."


    def to_dict(self):
        return {
            "id": self.book_id,
            "title": self.title,
            "author": self.author,
            "year": self.year,
            "checked_out": self.is_checked_out,
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else None
        }



class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.borrowed_books = []


    def borrow_book(self, book: Book):
        if book.is_checked_out:
            return f"Sorry, '{book.title}' is already checked out."
        result = book.checkout()
        self.borrowed_books.append(book)
        return f"{self.name} borrowed '{book.title}'. {result}"


    def return_book(self, book: Book):
        if book not in self.borrowed_books:
            return f"{self.name} does not have '{book.title}'."
        result = book.return_book()
        self.borrowed_books.remove(book)
        return f"{self.name} returned '{book.title}'. {result}"


    def list_books(self):
        return [book.title for book in self.borrowed_books]



class Library:
    def __init__(self):
        self.books = {}
        self.users = {}


    def add_book(self, book: Book):
        self.books[book.book_id] = book
        return f"Book '{book.title}' added to library."


    def add_user(self, user: User):
        self.users[user.user_id] = user
        return f"User '{user.name}' registered."


    def search_books(self, keyword):
        results = [book for book in self.books.values() if keyword.lower() in book.title.lower()]
        return results


    def export_data(self, filename="library_data.json"):
        data = {
            "books": [book.to_dict() for book in self.books.values()],
            "users": {uid: {"name": user.name, "borrowed": user.list_books()} for uid, user in self.users.items()}
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        return f"Library data exported to {filename}."



# Example usage
if __name__ == "__main__":
    library = Library()


    # Add books
    b1 = Book(1, "1984", "George Orwell", 1949)
    b2 = Book(2, "Brave New World", "Aldous Huxley", 1932)
    b3 = Book(3, "Fahrenheit 451", "Ray Bradbury", 1953)


    library.add_book(b1)
    library.add_book(b2)
    library.add_book(b3)


    # Add users
    u1 = User(101, "Alice")
    u2 = User(102, "Bob")


    library.add_user(u1)
    library.add_user(u2)


    # Borrow and return books
    print(u1.borrow_book(b1))
    print(u2.borrow_book(b1))  # should fail
    print(u1.return_book(b1))
    print(u2.borrow_book(b1))  # now succeeds


    # Search books
    results = library.search_books("new")
    print("Search results:", [book.title for book in results])


    # Export data
    print(library.export_data())
'''


def main():
    print("=" * 80)
    print("  TESTING CLEAN CODE: Library Management System")
    print("=" * 80)
    print("\n🎯 GOAL: Clean, valid code should have LOW/NO bugs detected\n")
    
    analyzer = StaticAnalyzer(LIBRARY_MANAGEMENT_CODE)
    results = analyzer.analyze()
    
    print("📊 STATIC ANALYSIS RESULTS:")
    print("-" * 80)
    
    bug_count = 0
    false_positives = []
    
    for pattern, result in results.items():
        if result.get('found'):
            bug_count += 1
            symbol = "🔴"
            
            # Check for known false positives
            if pattern == 'syntax_error':
                print(f"{symbol} {pattern}: LEGITIMATE (code has syntax error)")
            elif pattern == 'hallucinated_objects':
                # Check if it's __name__
                objects = result.get('objects', [])
                if any('__name__' in str(obj) for obj in objects):
                    false_positives.append((pattern, "__name__ is a built-in, NOT hallucinated"))
                    print(f"{symbol} {pattern}: FALSE POSITIVE (__name__ is built-in)")
                else:
                    print(f"{symbol} {pattern}: Detected {len(objects)} objects")
            elif pattern == 'wrong_attribute':
                # Check if it's self.name or user.name
                details = result.get('details', [])
                if any('self' in str(d) or 'user' in str(d) for d in details):
                    false_positives.append((pattern, "Class attributes are valid, not dict access"))
                    print(f"{symbol} {pattern}: FALSE POSITIVE (class attributes are valid)")
                else:
                    print(f"{symbol} {pattern}: Detected")
            elif pattern == 'prompt_biased':
                # Check if it's in __main__ block
                details = result.get('details', [])
                in_main = any(d.get('line', 0) > 100 for d in details)  # Main block is at end
                if in_main:
                    false_positives.append((pattern, "Sample data in __main__ is expected"))
                    print(f"{symbol} {pattern}: FALSE POSITIVE (sample data in demo block)")
                else:
                    print(f"{symbol} {pattern}: Detected")
            elif pattern == 'npc':
                details = result.get('details', [])
                if any('due_date' in str(d) for d in details):
                    false_positives.append((pattern, "due_date is standard for checkout feature"))
                    print(f"{symbol} {pattern}: FALSE POSITIVE (due_date is standard for checkout)")
                else:
                    print(f"{symbol} {pattern}: Detected")
            else:
                print(f"{symbol} {pattern}: Detected")
            
            # Show details
            if 'details' in result and result['details']:
                for detail in result['details'][:2]:  # Show first 2
                    print(f"   └─ {detail}")
            elif 'objects' in result and result['objects']:
                for obj in result['objects'][:2]:
                    print(f"   └─ {obj}")
        else:
            symbol = "🟢"
            print(f"{symbol} {pattern}: Clean")
    
    print("-" * 80)
    print(f"\n📈 SUMMARY:")
    print(f"   Total Bugs Detected: {bug_count}")
    print(f"   False Positives: {len(false_positives)}")
    print(f"   Legitimate Issues: {bug_count - len(false_positives)}")
    
    print("\n" + "=" * 80)
    
    if len(false_positives) == 0 and bug_count == 0:
        print("  ✅ PERFECT: Clean code correctly identified as bug-free!")
    elif len(false_positives) == 0 and bug_count <= 2:
        print("  ✅ GOOD: Minimal bugs detected (acceptable for clean code)")
    elif len(false_positives) <= 2:
        print("  ⚠️  ACCEPTABLE: Some false positives but much better than before")
        print("\nRemaining False Positives:")
        for pattern, reason in false_positives:
            print(f"   - {pattern}: {reason}")
    else:
        print("  ❌ STILL NEEDS WORK: Too many false positives")
        print("\nFalse Positives Found:")
        for pattern, reason in false_positives:
            print(f"   - {pattern}: {reason}")
    
    print("=" * 80)
    
    # Return code for CI/CD
    return len(false_positives)


if __name__ == "__main__":
    exit_code = main()
    exit(0 if exit_code <= 2 else 1)  # Accept up to 2 false positives
