"""
This is a test file with intentional bugs and code quality issues
for testing the CodeOptimizer code review API
"""

import os
import json
from typing import Dict, List


# Bug 1: Unhandled exception - file might not exist
def load_user_data(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


# Bug 2: SQL Injection vulnerability
def get_user_by_email(email, db_connection):
    query = "SELECT * FROM users WHERE email = '" + email + "'"
    cursor = db_connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


# Performance Issue: O(n²) when it could be O(n)
def find_duplicates(items: List[int]) -> List[int]:
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates


# Bug 3: Infinite recursion risk
def calculate_factorial(n):
    if n == 1:
        return 1
    else:
        return n * calculate_factorial(n - 1)  # No base case for n <= 0


# Bug 4: Mutable default argument
def add_item_to_list(item, list_items=[]):
    list_items.append(item)
    return list_items


# Performance Issue: Inefficient string concatenation
def build_large_string():
    result = ""
    for i in range(10000):
        result += str(i) + ", "
    return result


# Code Quality: No docstring, unclear purpose
def process(x, y, z):
    a = x * 2
    b = y + 5
    c = a + b
    d = c / z
    return d


# Security: Hardcoded credentials
def connect_to_database():
    username = "admin"
    password = "password123"
    db_url = "192.168.1.100:5432"
    # Connect to database
    return f"Connected to {db_url} as {username}"


# Bug 5: Global variable mutation
global_counter = 0

def increment_counter():
    global global_counter
    global_counter += 1
    return global_counter


# Code Quality: Too many parameters (God function)
def create_user_profile(name, email, phone, address, city, state, zip_code, 
                       country, age, gender, occupation, salary, education):
    user = {
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'state': state,
        'zip_code': zip_code,
        'country': country,
        'age': age,
        'gender': gender,
        'occupation': occupation,
        'salary': salary,
        'education': education
    }
    return user


# Bug 6: Missing error handling with external API
def fetch_data_from_api(url):
    import requests
    response = requests.get(url)
    return response.json()  # No timeout, no error handling


# Performance: Creating unnecessary copies
def process_large_list(lst: List[int]) -> int:
    temp_copy = lst.copy()
    temp_copy2 = temp_copy.copy()
    temp_copy3 = temp_copy2.copy()
    return sum(temp_copy3)


# Code Quality: Inconsistent naming and magic numbers
def calc_age(dob):
    from datetime import datetime
    today = datetime.now()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age


# Bug 7: Type inconsistency
def divide_numbers(a, b):
    return a / b  # No type checking, b could be string


# Unused imports (already imported os and json at top)
import sys
import warnings


print("This test file contains multiple intentional bugs for API testing")
