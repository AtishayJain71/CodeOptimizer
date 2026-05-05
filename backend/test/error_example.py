"""
Test file with actual runtime errors for testing the Bug Fixer API
"""

# Error 1: NameError - undefined variable
def calculate_total():
    items = [10, 20, 30]
    total = sum(items)
    return total + unknown_variable  # NameError: name 'unknown_variable' is not defined


# Error 2: IndexError - list index out of range
def get_first_item(items):
    return items[10]  # IndexError: list index out of range


# Error 3: TypeError - type mismatch
def divide_numbers(a, b):
    return a / b


# Error 4: KeyError - missing dictionary key
def get_user_name(user_dict):
    return user_dict["name"]  # KeyError: 'name'


# Error 5: AttributeError - missing attribute
class Person:
    def __init__(self, name):
        self.name = name


def get_person_age():
    person = Person("John")
    return person.age  # AttributeError: 'Person' object has no attribute 'age'


# Error 6: ValueError - invalid value
def convert_to_int(value):
    return int(value)  # ValueError: invalid literal for int() with base 10: 'abc'


# Error 7: ZeroDivisionError - division by zero
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count  # ZeroDivisionError: division by zero (if count is 0)


# Error 8: FileNotFoundError - file doesn't exist
def read_config():
    with open("config.json", "r") as f:
        return f.read()  # FileNotFoundError: [Errno 2] No such file or directory: 'config.json'


# Error 9: ImportError - missing import
def process_data():
    import missing_module  # ModuleNotFoundError: No module named 'missing_module'
    return missing_module.process()


# Error 10: RecursionError - infinite recursion
def factorial(n):
    return n * factorial(n - 1)  # RecursionError: maximum recursion depth exceeded


# Test functions to trigger errors
if __name__ == "__main__":
    print("Running test functions - demonstrating various error types...\n")
    
    # Error 1: NameError
    print("1. Testing NameError:")
    try:
        print(calculate_total())
    except NameError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 2: IndexError
    print("2. Testing IndexError:")
    try:
        print(get_first_item([1, 2, 3]))
    except IndexError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 3: TypeError
    print("3. Testing TypeError:")
    try:
        print(divide_numbers("10", 5))
    except TypeError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 4: KeyError
    print("4. Testing KeyError:")
    try:
        print(get_user_name({"age": 30}))
    except KeyError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 5: AttributeError
    print("5. Testing AttributeError:")
    try:
        print(get_person_age())
    except AttributeError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 6: ValueError
    print("6. Testing ValueError:")
    try:
        print(convert_to_int("abc"))
    except ValueError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 7: ZeroDivisionError
    print("7. Testing ZeroDivisionError:")
    try:
        print(calculate_average([]))
    except ZeroDivisionError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 8: FileNotFoundError
    print("8. Testing FileNotFoundError:")
    try:
        print(read_config())
    except FileNotFoundError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 9: ImportError
    print("9. Testing ModuleNotFoundError:")
    try:
        print(process_data())
    except ModuleNotFoundError as e:
        print(f"   ERROR: {e}\n")
    
    # Error 10: RecursionError (limited to avoid actual crash)
    print("10. Testing RecursionError:")
    try:
        import sys
        sys.setrecursionlimit(50)  # Set low limit to trigger quickly
        print(factorial(100))
    except RecursionError as e:
        print(f"   ERROR: {e}\n")
