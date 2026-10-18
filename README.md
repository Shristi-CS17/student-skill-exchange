# Student Skill Exchange Platform — NTCC Project

A simple but polished full-stack web application where students exchange knowledge with each other.

## Technology
- Python Flask
- SQLite
- HTML5 / CSS3
- Bootstrap 5
- JavaScript

## Run in VS Code

1. Open this folder in VS Code.
2. Open Terminal.
3. Create a virtual environment (recommended):
   `python -m venv venv`
4. Activate it:
   - Windows: `venv\Scripts\activate`
5. Install dependencies:
   `pip install -r requirements.txt`
6. Start the application:
   `python app.py`
7. Open: `http://127.0.0.1:5000`

The SQLite database is automatically created the first time the application starts.

## Demo accounts

Student:
- Email: `shristi@gmail.com`
- Password: `student123`

Other demo students:
- `rahul@gmail.com`
- `ananya@gmail.com`
- `arjun@gmail.com`
- Password for all: `student123`

Admin:
- Email: `admin@skillxchange.com`
- Password: `admin123`

## Suggested judge demonstration

1. Register/login as Shristi.
2. Open Skills and show teaching + learning skills.
3. Open Find Matches and explain reciprocal skill matching.
4. Send a learning request to Rahul for Python.
5. Login as Rahul in another browser/incognito window.
6. Accept the request.
7. Login as Shristi and schedule a session.
8. After the session, submit a rating/review.
9. Open Admin Panel and demonstrate platform statistics, students, requests and reviews.

## Core matching logic

The project deliberately uses a simple rule-based algorithm instead of AI:

If Student A wants to learn a skill and Student B can teach that skill,
Student B is suggested as a match.

This makes the system easy to explain in an academic viva and leaves scope for future improvement using a matching score or machine learning.
# student-skill-exchange
A Student Skill Exchange Platform built using Python Flask and SQLite
