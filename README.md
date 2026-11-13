# Online Examination System 
ONLINE EXAMINATION MANAGEMENT SYSTEM

REQUIREMENTS AND START
Python 3.8 or newer; no extra packages required.
Extract the ZIP into one folder. Keep all files together.
Open a terminal in that folder and run:
    python exam_system.py
On Windows, you can also try:
    py exam_system.py

FILES
exam_system.py  - beginner-friendly Python source (206 physical lines)
questions.txt   - 15 questions across Python, Mathematics and General Knowledge
students.txt    - registered student IDs and names (initially header only)
results.txt     - saved exam attempts (initially header only)
sample_run.txt  - verified example showing console inputs and outputs
verification.txt - line count, test checks and observed score

USAGE
1. Register a student with a unique alphanumeric ID and a name.
2. Take an exam using the registered ID. Choose a numbered category and
   a question count. Questions are selected randomly without repetition
   within that attempt. Separate attempts may contain the same questions.
3. Answer using A, B, C or D (lowercase also works), or S to skip.
   Invalid answers are retried and do not consume a question.
4. View result history using the student ID.
5. Add questions using the menu. The correct answer must be A/B/C/D.
6. Exit using option 5. Ctrl+C or end-of-input also ends the session.

SCORING
Correct: +4. Wrong: -1. Skipped: 0.
Maximum = question count multiplied by 4.
Percentage = score / maximum multiplied by 100.
Scores and percentages can be negative. No pass/fail threshold is imposed.
A completed attempt shows totals and the correct answer for each question.
Result history shows all saved attempts and their average percentage
(each attempt has equal weight, regardless of question count).

TXT FILE FORMAT AND HANDLING
The TXT files contain CSV records with a header. Python's csv module handles
commas and quotation marks in fields. Do not change the header names/order.
Keep one CSV record per line when editing manually. Prefer menu-based entry.
Records are stored beside the Python program, regardless of your current
terminal folder. The folder must be writable. Missing student/results files
are recreated with headers. Keep questions.txt: a missing or malformed bank
produces an error message. Do not edit record files while the program runs.
If saving a completed result fails, it remains displayed with a NOT saved
message so you can record it manually. No automatic recovery is provided.

COURSE CONCEPTS
The ExaminationSystem class demonstrates OOP and methods. Lists hold records,
dictionaries map fields and menu actions, and random.sample selects questions.
Functions, loops, conditionals, exceptions and TXT file handling are included.

SAMPLE AND VERIFICATION
The sample uses a fixed question order for reproducibility; normal execution
uses random selection. It registers S001, selects three Python questions,
retries Z, answers B/A/S, saves 3/12 (25.00%), and displays result history.
Tests used temporary data. The delivered student/results files are clean.

SCOPE
An educational local console simulation of an examination system. It has no
web server, login/password protection, invigilation, or separate admin role.
Anyone running it can add questions and read local TXT records. Use sample
or classroom data appropriate for this simple project.
