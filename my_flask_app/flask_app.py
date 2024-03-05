from flask import Flask, render_template, jsonify
import os
import json
import random
import re
from fuzzywuzzy import fuzz

app = Flask(__name__)

bankpath = "/home/criminalstudy/KHCA/quizbank"
filepath = "/home/criminalstudy/KHCA/allquiz"

question_count = 20

def extract_case_numbers(txt_file_path):
    case_numbers = []
    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
        for line in txt_file:
            # Extract the case number before the comma, if any
            case_number = line.split(',')[0].strip()
            case_numbers.append(case_number)
    return case_numbers

def merge_json_files(directory, txt_directory):
    merged_data = []

    all_case_numbers = []
    for txt_filename in os.listdir(txt_directory):
        if (txt_filename.endswith('.txt')) & ('형사소송법' in txt_filename):
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

def load_data(directory):
    merged_json_data = merge_json_files(directory, bankpath)

    return merged_json_data

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
    
def select_data_with_exact_length(data, target_length):
    selected_data = []
    total_length = 0

    # 데이터를 섞어서 순서에 따른 선택 편향을 제거합니다.
    random.shuffle(data)

    for item in data:
        current_item_length = len(item["A"])
        if total_length + current_item_length <= target_length:
            selected_data.append(item)
            total_length += current_item_length

        if total_length >= target_length:
            break

    # 초과분 처리
    if total_length > target_length:
        # 목표 길이를 초과하면 초과분 만큼의 길이를 가진 항목을 제거
        excess_length = total_length - target_length
        for item in selected_data:
            if len(item["A"]) == excess_length:
                selected_data.remove(item)
                break  # 필요한 경우 여러 항목을 제거해야 한다면, 이 로직을 수정하세요.

    return selected_data


@app.route('/')
def run_quiz(filepath):

    data = load_data(filepath)
    questions = select_data_with_exact_length(data, min(question_count, len(data)))  # Ensure not to exceed total questions
    score = 0
    incorrect_answers = []

    def case_number(text):
        pattern = r'(선고|자)\s*(.*)'
        match = re.search(pattern, text)
        
        if match:
            case_num = match.group(2)
            # 콤마로 첫 부분만 추출
            comma_index = case_num.find(',')
            if comma_index != -1:
                case_num = case_num[:comma_index]
            # 괄호와 괄호 안의 내용 제거
            case_num = re.sub(r'\(.*?\)', '', case_num)
            return case_num.strip()  # 앞뒤 공백 제거
        else:
            return ""

    for i, case in enumerate(questions, start=1):
        print(f"\n문제 {i} / {len(questions)}:")
        question_score = 0  # Initialize score for the question

        print(case['N'])
        for q in case['Q']:
            print(q)
        print("답안 수:", len(case['A']))

        correct_count = 0

        for correct_answer in case['A']:
            user_answer = input("\n답변: ").strip()
            correct = is_correct(user_answer, correct_answer)

            if correct:
                correct_count += 1
                print("정답!\n")
            else:
                print("오답!\n")

        question_score = correct_count / len(case['A'])
        print(f"이 문제의 득점: {question_score:.2f}")
        score += question_score  # Add question score to total score

        # Additional logic for incorrect answers
        if question_score < 1:

            #법원명 / 사건번호
            court = "대법원" if "대법원" in case['N'] else "헌법재판소" if "헌법재판소" in case['N'] else ""
            casenumber = case_number(case['N'])

            #link = "https://casenote.kr/" + court + "/" + casenumber
            link = "https://bigcase.ai/cases/" + court + "/" + casenumber

            incorrect_answers.append((i, case['Q'], case['A'], link))
            print(case['A'], prefix="정답:")
            #format_print(case['R'], prefix="근거:")
            print(f"참조 링크: {link}")
            print("\n")

    # Final score and review incorrect answers
    print('=======================================================')
    print(f"당신의 점수는 {round(score, 2)}/{len(questions)}.")
    print(f"정답률: {score/len(questions) * 100:.2f}%\n")
    
    # Review incorrect answers
    if incorrect_answers:
        print("###오답노트###")
        for i, question, answer, link in incorrect_answers:
            print(f"\n문제 {i}:")
            print(question)
            print(answer, prefix="정답:")
            #format_print(reason, prefix="근거:")
            print(f"참조 링크: {link}")
        print('=======================================================')