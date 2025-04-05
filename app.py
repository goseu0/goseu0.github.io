from flask import Flask, render_template, request, redirect, url_for, session
import random
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션 사용을 위해 필요

# ______________________________________________________
# 🔸 시작 화면: data 폴더 내 시험 JSON 목록 보여주기
@app.route('/')
def index():
    data_dir = 'data'
    files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    exams = [os.path.splitext(f)[0] for f in files]  # .json 제거
    return render_template('index.html', exams=exams)

# ______________________________________________________
# 🔸 아마도? 거시기 그 만드는거일껄?
@app.route('/create', methods=['GET', 'POST'])
def create_exam():
    if request.method == 'POST':
        exam_name = request.form['exam_name']
        data = request.form['data']
        filename = f"data/{exam_name}.json"

        try:
            json_data = json.loads(data)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            return redirect(url_for('index'))
        except Exception as e:
            return f"저장 실패: {e}"

    # GET 방식일 때 템플릿 렌더
    return render_template('create_exam.html')



# ______________________________________________________
# 🔸 선택된 시험 JSON 파일을 기반으로 퀴즈 시작
@app.route('/start/<exam_name>')
def start_exam(exam_name):
    data_path = f'data/{exam_name}.json'
    if not os.path.exists(data_path):
        return f"<h2>{exam_name} 시험 데이터를 찾을 수 없습니다.</h2>"

    with open(data_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    question_order = list(range(len(questions)))
    random.shuffle(question_order)

    session['questions'] = questions
    session['question_order'] = question_order
    session['current_index'] = 0
    session['answers'] = []
    session['exam_name'] = exam_name

    return redirect(url_for('quiz', qid=1))

# ______________________________________________________
# 🔸 퀴즈 페이지
@app.route('/quiz/<int:qid>', methods=['GET', 'POST'])
def quiz(qid):
    if 'question_order' not in session or 'questions' not in session:
        return redirect(url_for('index'))

    questions = session['questions']
    question_order = session['question_order']
    current_index = session.get('current_index', 0)

    if current_index >= len(question_order):
        return redirect(url_for('complete'))

    question_index = question_order[current_index]
    question = questions[question_index]

    if request.method == 'POST':
        selected = int(request.form['choice'])
        correct = selected == question['answer']

        answers = session['answers']
        answers.append({
            'subject': question['subject'],
            'correct': correct
        })
        session['answers'] = answers

        session['current_index'] = current_index + 1

        return render_template('quiz.html',
                               question=question,
                               selected=selected,
                               correct=correct,
                               show_answer=True,
                               total=len(questions),
                               current_idx=current_index)

    return render_template('quiz.html',
                           question=question,
                           selected=None,
                           correct=None,
                           show_answer=False,
                           total=len(questions),
                           current_idx=current_index)

# ______________________________________________________
# 🔸 채점 결과 페이지
@app.route('/complete')
def complete():
    if 'answers' not in session:
        return redirect(url_for('index'))

    answers = session['answers']
    subject_scores = {}
    subject_counts = {}

    for item in answers:
        subject = item['subject']
        is_correct = item['correct']

        subject_scores.setdefault(subject, 0)
        subject_counts.setdefault(subject, 0)

        subject_counts[subject] += 1
        if is_correct:
            subject_scores[subject] += 1

    subject_results = []
    total_score = 0
    total_count = 0
    failed_subject = False

    for subject in subject_scores:
        correct = subject_scores[subject]
        total = subject_counts[subject]
        score = round((correct / total) * 100)
        subject_results.append({
            'subject': subject,
            'score': score
        })

        total_score += score
        total_count += 1

        if score < 40:
            failed_subject = True

    average_score = round(total_score / total_count)
    passed = average_score >= 60 and not failed_subject

    return render_template('complete.html',
                           subject_results=subject_results,
                           average_score=average_score,
                           passed=passed)

# ______________________________________________________
# 🔸 초기화 (처음으로 돌아가기)
@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

# ______________________________________________________
# 🔸 앱 실행
if __name__ == '__main__':
    app.run(debug=True)
