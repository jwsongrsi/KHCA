from flask import Flask, request, render_template, session, redirect, url_for
import os
import json
import random
import re
from fuzzywuzzy import fuzz

app = Flask(__name__)
app.secret_key = 'wnsdnjs9712*' 

bankpath = "/home/criminalstudy/KHCA/quizbank"
filepath = "/home/criminalstudy/KHCA/allquiz"

def extract_case_numbers(txt_file_path):
    case_numbers = []
    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
        for line in txt_file:
            # Extract the case number before the comma, if any
            case_number = line.split(',')[0].strip()
            case_numbers.append(case_number)
    return case_numbers

def merge_json_files(directory, txt_directory, selected_cases):
    merged_data = []

    all_case_numbers = []
    for txt_filename in os.listdir(txt_directory):
        if (txt_filename.endswith('.txt')) & (txt_filename.replace(".txt", "") in selected_cases): 
            txt_file_path = os.path.join(txt_directory, txt_filename)          
            case_numbers = extract_case_numbers(txt_file_path)
            
            all_case_numbers.extend(case_numbers)
    
    # Remove duplicates
    all_case_numbers = list(set(all_case_numbers))

    # Now iterate through JSON files and filter based on the compiled case numbers
    for filename in os.listdir(directory):
        if filename.endswith('.json'):  
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Filter data based on case numbers being included in 'N'
                filtered_data = [
                    item for item in data 
                    if any(case_number in item['N'] for case_number in all_case_numbers) 
                    and item.get('Q')  # Check if 'Q' is not empty
                    and any(q.strip() for q in item.get('Q'))  # Ensure 'Q' contains non-empty strings
                ]
                merged_data.extend(filtered_data)

    return merged_data

def is_similar(user_answer, correct_answer):
    similarity = fuzz.ratio(user_answer, correct_answer)
    return similarity

def is_correct(user_answer, correct_answer):

    if user_answer == 'o':
        user_answer = '적극'

    if user_answer == 'x':
        user_answer = '소극'

    if correct_answer.startswith("원칙적 소극") and user_answer == "소극":
        return True
    if correct_answer.startswith("원칙적 적극") and user_answer == "적극":
        return True
    
    if correct_answer.startswith("한정 소극") and user_answer == "소극":
        return True
    if correct_answer.startswith("한정 적극") and user_answer == "적극":
        return True
    
    try:
        similarity = is_similar(user_answer, correct_answer)  
        print(similarity)    
        if similarity >= 75:
            return True
    except:
        return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    selected_cases = request.form.getlist('standard_cases')  # 체크박스 선택값을 리스트로 받음
    num_questions = int(request.form['num_questions'])  # 문항 수 받기
    password = request.form['password']  # 비밀번호 받기

    data = merge_json_files(filepath, bankpath, selected_cases)

    if len(data) < num_questions:
        questions = data
    else:
        questions = random.sample(data, num_questions)

    session['questions'] = questions
    session['current_question'] = 0  # 현재 질문의 인덱스
    session['answers'] = []  # 사용자의 답변을 저장할 리스트

    return redirect(url_for('show_question'))

@app.route('/show_question', methods=['GET', 'POST'])
def show_question():
    question_id = session.get('current_question')
    questions = session.get('questions')
    
    if question_id is None or question_id >= len(questions):
        return redirect(url_for('quiz_complete'))  # 모든 질문이 완료되면 다른 페이지로 리다이렉트

    question = questions[question_id]
    return render_template('quiz.html', question_id=question_id+1, question=question)

@app.route('/next_question', methods=['POST'])
def next_question():
    answer = request.form['answer']
    session['answers'].append(answer)  # 사용자의 답변 저장
    session['current_question'] += 1  # 다음 질문으로 이동
    
    return redirect(url_for('show_question'))

@app.route('/quiz_complete')
def quiz_complete():
    # 퀴즈 완료 처리, 예: 사용자의 답변을 평가하거나 결과 페이지를 보여줍니다.
    return "퀴즈 완료! 당신의 답변은: " + ", ".join(session['answers'])