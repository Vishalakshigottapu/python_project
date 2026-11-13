from pathlib import Path
import csv
import random
from datetime import datetime

# All TXT files are stored in the same folder as this program.
BASE = Path(__file__).resolve().parent
QUESTION_FIELDS = ['category', 'question', 'A', 'B', 'C', 'D', 'answer']
STUDENT_FIELDS = ['student_id', 'name']
RESULT_FIELDS = ['date', 'student_id', 'category', 'correct', 'wrong',
                 'skipped', 'score', 'maximum', 'percentage']


def read_records(filename, fields):
    """Read a CSV-formatted TXT file and check its structure."""
    with (BASE / filename).open(encoding='utf-8', newline='') as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != fields:
            raise ValueError(f'{filename}: incorrect column headings.')
        rows = list(reader)
    for row in rows:  # Check each saved record separately.
        if set(row) != set(fields):
            raise ValueError(f'{filename}: extra or missing columns.')
        for value in row.values():
            if value is None:
                raise ValueError(f'{filename}: incomplete record.')
    return rows


def append_record(filename, fields, row):
    """Append one record; validate the existing file before changing it."""
    read_records(filename, fields)
    with (BASE / filename).open('a', encoding='utf-8', newline='') as file:
        csv.DictWriter(file, fieldnames=fields).writerow(row)


def ask(prompt, choices=None):
    while True:
        value = input(prompt).strip()
        if not value:  # Reject empty input.
            print('Please enter a value.')
            continue
        if choices is None:  # Names and question text keep their original case.
            return value
        value = value.upper()  # Accept lowercase menu and answer letters.
        if len(value) == 1 and value in choices:
            return value
        print('Invalid input. Please try again.')


class ExaminationSystem:  # A class groups the exam's related operations.
    def __init__(self):
        # Create writable record files if missing; questions.txt is supplied.
        for filename, fields in [('students.txt', STUDENT_FIELDS),
                                 ('results.txt', RESULT_FIELDS)]:
            if not (BASE / filename).exists():
                with (BASE / filename).open('w', encoding='utf-8', newline='') as file:
                    csv.DictWriter(file, fieldnames=fields).writeheader()

    def register(self):
        students = read_records('students.txt', STUDENT_FIELDS)
        student_id = ask('Student ID (letters/numbers): ').upper()
        if not student_id.isalnum():
            raise ValueError('Student ID must contain only letters and numbers.')
        for student in students:
            if student['student_id'].upper() == student_id:
                raise ValueError('That ID is already registered.')
        name = ask('Full name: ')
        append_record('students.txt', STUDENT_FIELDS,
                      {'student_id': student_id, 'name': name})
        print(f'Registered {name} with ID {student_id}.')

    def questions(self):
        rows = read_records('questions.txt', QUESTION_FIELDS)
        if not rows:
            raise ValueError('The question bank is empty.')
        for row in rows:
            for value in row.values():
                if not value.strip():
                    raise ValueError('Question bank contains an empty field.')
            if row['answer'] not in 'ABCD' or len(row['answer']) != 1:
                raise ValueError('Question bank answers must be A, B, C or D.')
        return rows

    def add_question(self):
        row = {'category': ask('Category: ').title(),
               'question': ask('Question: ')}
        for option in 'ABCD':
            row[option] = ask(f'Option {option}: ')
        row['answer'] = ask('Correct answer (A/B/C/D): ', 'ABCD')
        append_record('questions.txt', QUESTION_FIELDS, row)
        print('Question saved.')

    def take_exam(self):
        student_id = ask('Registered student ID: ').upper()
        students = read_records('students.txt', STUDENT_FIELDS)
        student = None  # No matching student has been found yet.
        for record in students:
            if record['student_id'].upper() == student_id:
                student = record
                break
        if student is None:
            raise ValueError('Student not found. Register first.')
        questions = self.questions()
        categories = []
        for question in questions:
            if question['category'] not in categories:
                categories.append(question['category'])
        categories.sort()  # Keep category numbers in alphabetical order.
        for number, category in enumerate(categories, 1):
            print(f'{number}. {category}')
        choice = int(ask('Category number: '))
        if not 1 <= choice <= len(categories):
            raise ValueError('Category number is out of range.')
        category = categories[choice - 1]  # List positions start at zero.
        pool = []  # Collect questions from the chosen category only.
        for question in questions:
            if question['category'] == category:
                pool.append(question)
        count = int(ask(f'Number of questions (1-{len(pool)}): '))
        if not 1 <= count <= len(pool):
            raise ValueError('Question count is out of range.')
        selected = random.sample(pool, count)  # Random choice without repeats.
        correct = wrong = skipped = 0
        review = []
        print('\nRules: correct +4, wrong -1, skip 0. Enter S to skip.')
        for number, question in enumerate(selected, 1):
            print(f'\n{number}. {question["question"]}')
            for option in 'ABCD':
                print(f'  {option}. {question[option]}')
            answer = ask('Answer (A/B/C/D/S): ', 'ABCDS')
            if answer == 'S':
                skipped += 1
            elif answer == question['answer']:
                correct += 1
            else:
                wrong += 1
            review.append((question, answer))
        score = correct * 4 - wrong  # Add 4 per correct answer; subtract 1 per wrong.
        percentage = score / (count * 4) * 100
        result = {  # Each key matches a column in results.txt.
            'date': datetime.now().isoformat(timespec='seconds'),
            'student_id': student_id, 'category': category,
            'correct': correct, 'wrong': wrong, 'skipped': skipped,
            'score': score, 'maximum': count * 4,
            'percentage': f'{percentage:.2f}'
        }
        print(f'\nRESULT: {student["name"]} ({student_id}) | {category}')
        print(f'Correct: {correct} | Wrong: {wrong} | Skipped: {skipped}')
        print(f'Score: {score}/{count * 4} | Percentage: {percentage:.2f}%')
        for number, (question, answer) in enumerate(review, 1):
            print(f'{number}. Your answer: {answer}; correct: {question["answer"]}')
        try:
            append_record('results.txt', RESULT_FIELDS, result)
            print('Result saved to results.txt.')
        except (OSError, ValueError, csv.Error) as error:
            print(f'Result displayed but NOT saved: {error}')

    def summary(self):
        student_id = ask('Student ID for result history: ').upper()
        rows = read_records('results.txt', RESULT_FIELDS)
        results = []
        for row in rows:
            if row['student_id'] == student_id:
                results.append(row)
        if not results:
            print('No saved results for this ID.')
            return
        for row in results:
            print(f'{row["date"]} | {row["category"]} | '
                  f'{row["score"]}/{row["maximum"]} | {row["percentage"]}%')
        total = 0
        for row in results:
            total += float(row['percentage'])
        average = total / len(results)  # Each attempt has equal weight.
        print(f'Attempts: {len(results)} | Average percentage: {average:.2f}%')

    def run(self):
        while True:
            print('\nONLINE EXAMINATION MANAGEMENT SYSTEM')
            print('1. Register student\n2. Take exam\n3. Result history')
            print('4. Add question\n5. Exit')
            choice = ask('Choose (1-5): ', '12345')
            if choice == '5':
                print('Goodbye!')
                break
            try:
                if choice == '1':
                    self.register()
                elif choice == '2':
                    self.take_exam()
                elif choice == '3':
                    self.summary()
                elif choice == '4':
                    self.add_question()
            except (OSError, ValueError, csv.Error) as error:
                print(f'Error: {error}')


if __name__ == '__main__':
    try:
        ExaminationSystem().run()
    except (EOFError, KeyboardInterrupt):
        print('\nSession ended. Completed saved records remain available.')
    except OSError as error:
        print(f'Cannot open record files: {error}')
