from flask import Flask, render_template, jsonify
import os
import json
import random

app = Flask(__name__)

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

@app.route('/')
def print_all ():
    data = load_data(filepath)
    if data:
        return jsonify(data)
    else:
        return jsonify({"error": "No items found"}), 404