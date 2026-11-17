from pathlib import Path
import csv, math, os, random, tempfile
from datetime import datetime
BASE = Path(__file__).resolve().parent
QUESTION_FIELDS = ['category', 'question', 'A', 'B', 'C', 'D', 'answer']
STUDENT_FIELDS = ['student_id', 'name']
RESULT_FIELDS = ['date', 'student_id', 'category', 'correct', 'wrong',
                 'skipped', 'score', 'maximum', 'percentage']
def normalize_id(value):
    student_id = value.strip().upper()
    if not student_id or not student_id.isascii() or not student_id.isalnum():
        raise ValueError('Student ID must contain only English letters (A-Z) and numbers (0-9).')
    return student_id
def normalize_text(value):
    return ' '.join(value.split()).casefold()
def validate_student_records(rows, filename):
    seen_ids = set()
    for line, row in enumerate(rows, 2):
        try:
            sid = normalize_id(row['student_id'])
            if not row['name'].strip():
                raise ValueError('student name cannot be blank')
            if sid in seen_ids:
                raise ValueError(f'duplicate student ID: {sid}')
            seen_ids.add(sid)
            row['student_id'], row['name'] = sid, row['name'].strip()
        except ValueError as error:
            raise ValueError(f'{filename}: line {line}: {error}') from error
    return rows
def question_duplicate_key(row):
    return tuple(normalize_text(row[key]) for key in
                 ('category', 'question', 'A', 'B', 'C', 'D'))
def validate_question_records(rows, filename):
    seen = set()
    for line, row in enumerate(rows, 2):
        if any(not value.strip() for value in row.values()):
            raise ValueError(f'{filename}: line {line}: empty question field.')
        answer = row['answer'].strip().upper()
        if len(answer) != 1 or answer not in 'ABCD':
            raise ValueError(f'{filename}: line {line}: answer must be A, B, C or D.')
        row['category'], row['answer'] = ' '.join(row['category'].split()).title(), answer
        key = question_duplicate_key(row)
        if key in seen:
            raise ValueError(f'{filename}: line {line}: duplicate question content.')
        seen.add(key)
    return rows
def validate_result_records(rows, filename):
    for line, row in enumerate(rows, 2):
        try:
            sid = normalize_id(row['student_id'])
            if not row['category'].strip(): raise ValueError('category cannot be blank')
            datetime.fromisoformat(row['date'])
            correct, wrong, skipped = (int(row[k]) for k in ('correct', 'wrong', 'skipped')); score, maximum = int(row['score']), int(row['maximum'])
            percentage = float(row['percentage'])
            if min(correct, wrong, skipped) < 0:
                raise ValueError('answer counts cannot be negative')
            attempted = correct + wrong + skipped
            if attempted <= 0:
                raise ValueError('attempted question count must be positive')
            if maximum != 4 * attempted:
                raise ValueError('maximum must equal 4 multiplied by attempted count')
            if score != 4 * correct - wrong:
                raise ValueError('score does not match the marking rules')
            if not math.isfinite(percentage):
                raise ValueError('percentage must be a finite number')
            expected = score / maximum * 100
            if not math.isclose(percentage, expected, rel_tol=0, abs_tol=0.011):
                raise ValueError('percentage does not match score and maximum')
            row['student_id'] = sid
        except (ValueError, OverflowError) as error:
            raise ValueError(f'{filename}: line {line}: invalid result: {error}') from error
    return rows
def read_records(filename, fields):
    path = BASE / filename
    try:
        with path.open('r', encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != fields:
                raise ValueError(f'{filename}: incorrect column headings.')
            rows = list(reader)
    except csv.Error as error:
        raise ValueError(f'{filename}: invalid CSV data: {error}') from error
    for line, row in enumerate(rows, 2):
        if set(row) != set(fields):
            raise ValueError(f'{filename}: line {line}: extra or missing columns.')
        if any(value is None for value in row.values()):
            raise ValueError(f'{filename}: line {line}: incomplete record.')
    validators = {'students.txt': validate_student_records,
                  'questions.txt': validate_question_records,
                  'results.txt': validate_result_records}
    return validators[filename](rows, filename) if filename in validators else rows
def write_records_atomically(filename, fields, rows):
    path, temporary_path = BASE / filename, None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='',
                dir=BASE, prefix=f'.{path.name}.', suffix='.tmp', delete=False) as file:
            temporary_path = file.name
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
            file.flush(); os.fsync(file.fileno())
        os.replace(temporary_path, path); temporary_path = None
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)
def append_record(filename, fields, row):
    rows = read_records(filename, fields)
    updated = rows + [{field: str(row[field]) for field in fields}]
    validators = {'students.txt': validate_student_records,
                  'questions.txt': validate_question_records,
                  'results.txt': validate_result_records}
    if filename in validators:
        validators[filename](updated, filename)
    write_records_atomically(filename, fields, updated)
def ask(prompt, choices=None):
    while True:
        value = input(prompt).strip()
        if not value:
            print('Please enter a value.')
            continue
        if choices is None:
            return value
        value = value.upper()
        if len(value) == 1 and value in choices:
            return value
        print('Invalid input. Please try again.')
class ExaminationSystem:
    def __init__(self):
        for filename, fields in [('students.txt', STUDENT_FIELDS),
                                 ('results.txt', RESULT_FIELDS)]:
            if not (BASE / filename).exists():
                write_records_atomically(filename, fields, [])
    def register(self):
        students = read_records('students.txt', STUDENT_FIELDS)
        sid = normalize_id(ask('Student ID (letters/numbers): '))
        if any(item['student_id'] == sid for item in students):
            raise ValueError('That ID is already registered.')
        name = ask('Full name: ')
        append_record('students.txt', STUDENT_FIELDS, {'student_id': sid, 'name': name})
        print(f'Registered {name} with ID {sid}.')
    def questions(self):
        rows = read_records('questions.txt', QUESTION_FIELDS)
        if not rows:
            raise ValueError('The question bank is empty.')
        return rows
    def add_question(self):
        row = {'category': ' '.join(ask('Category: ').split()).title(),
               'question': ask('Question: ')}
        for option in 'ABCD':
            row[option] = ask(f'Option {option}: ')
        row['answer'] = ask('Correct answer (A/B/C/D): ', 'ABCD')
        append_record('questions.txt', QUESTION_FIELDS, row)
        print('Question saved.')
    def take_exam(self):
        sid = normalize_id(ask('Registered student ID: '))
        students = read_records('students.txt', STUDENT_FIELDS)
        student = next((item for item in students if item['student_id'] == sid), None)
        if student is None:
            raise ValueError('Student not found. Register first.')
        all_questions = self.questions()
        category_names = {normalize_text(q['category']): q['category'] for q in all_questions}; categories = sorted(category_names.values(), key=str.casefold)
        print('\nAvailable categories:')
        for number, name in enumerate(categories, 1):
            print(f'{number}. {name}')
        try:
            choice = int(ask('Category number: '))
        except ValueError as error:
            raise ValueError('Enter a valid category number.') from error
        if not 1 <= choice <= len(categories):
            raise ValueError('Category number is out of range.')
        category = categories[choice - 1]
        pool = [q for q in all_questions if normalize_text(q['category']) == normalize_text(category)]
        try:
            count = int(ask(f'Number of questions (1-{len(pool)}): '))
        except ValueError as error:
            raise ValueError('Enter a valid question count.') from error
        if not 1 <= count <= len(pool):
            raise ValueError('Question count is out of range.')
        selected = random.sample(pool, count); correct = wrong = skipped = 0; review = []
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
        score, maximum = correct * 4 - wrong, count * 4; percentage = score / maximum * 100
        result = {'date': datetime.now().isoformat(timespec='seconds'),
                  'student_id': sid, 'category': category, 'correct': correct,
                  'wrong': wrong, 'skipped': skipped, 'score': score,
                  'maximum': maximum, 'percentage': f'{percentage:.2f}'}
        print(f'\nRESULT: {student["name"]} ({sid}) | {category}')
        print(f'Correct: {correct} | Wrong: {wrong} | Skipped: {skipped}')
        print(f'Score: {score}/{maximum} | Percentage: {percentage:.2f}%')
        print('\nANSWER REVIEW')
        for number, (question, answer) in enumerate(review, 1):
            chosen = 'Skipped' if answer == 'S' else answer
            print(f'{number}. Your answer: {chosen}; correct answer: {question["answer"]}')
        try:
            append_record('results.txt', RESULT_FIELDS, result)
            print('Result saved to results.txt.')
        except (OSError, ValueError, csv.Error) as error:
            print(f'Result displayed but NOT saved: {error}')
    def summary(self):
        sid = normalize_id(ask('Student ID for result history: '))
        students = read_records('students.txt', STUDENT_FIELDS)
        if not any(item['student_id'] == sid for item in students):
            raise ValueError('Student not found.')
        rows = read_records('results.txt', RESULT_FIELDS); results = [row for row in rows if row['student_id'] == sid]
        if not results:
            print('No saved results for this ID.')
            return
        print(f'\nRESULT HISTORY FOR {sid}')
        for row in results:
            print(f'{row["date"]} | {row["category"]} | {row["score"]}/{row["maximum"]} | '
                  f'{row["percentage"]}% | Correct: {row["correct"]} | '
                  f'Wrong: {row["wrong"]} | Skipped: {row["skipped"]}')
        average = sum(float(row['percentage']) for row in results) / len(results); print(f'Attempts: {len(results)} | Average percentage (equal weight per attempt): {average:.2f}%')
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