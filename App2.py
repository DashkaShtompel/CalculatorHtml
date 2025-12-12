from flask import Flask, render_template, request, jsonify
import locale
import re
import math

app = Flask(__name__)

def validate_number_format(num_str):
    if not num_str:
        return True
    temp = num_str.strip()
    if temp.count('.') > 1 or temp.count(',') > 1:
        return False
    if temp.count('-') > 1:
        return False
    if '-' in temp and temp[0] != '-':
        return False
    temp = temp.replace(',', '.')
    parts = temp.split('.')
    if len(parts) > 2:
        return False
    if len(parts) == 2 and len(parts[1]) > 6:
        return False
    integer_part = parts[0].replace('-', '').replace(' ', '')
    if not integer_part.replace(' ', '').isdigit():
        return False
    if len(parts) == 2 and not parts[1].isdigit():
        return False
    if '  ' in num_str:
        return False
    temp_no_spaces = num_str.replace(' ', '')
    if re.search(r'[^\d.,\-]', temp_no_spaces):
        return False
    return True

def normalize_number(num_str):
    if not num_str:
        return "0"
    if not validate_number_format(num_str):
        return None
    normalized = num_str.strip().replace(',', '.')
    normalized = normalized.replace(' ', '')
    if normalized and normalized[0] == '-':
        cleaned = '-' + re.sub(r'[^\d.]', '', normalized[1:])
    else:
        cleaned = re.sub(r'[^\d.]', '', normalized)
    if cleaned in ['', '.', '-', '-.']:
        return "0"
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    if len(parts) == 2 and len(parts[1]) > 6:
        return None
    return cleaned

def check_range(num):
    limit = 1_000_000_000_000.000000
    return -limit <= num <= limit

def format_number(num_str):
    try:
        num = float(num_str)
        if num == 0:
            return "0"
        
        formatted = f"{abs(num):.6f}".rstrip('0').rstrip('.')
        
        parts = formatted.split('.')
        integer_part = parts[0]
        
        integer_with_spaces = ""
        for i, digit in enumerate(reversed(integer_part)):
            if i > 0 and i % 3 == 0:
                integer_with_spaces = ' ' + integer_with_spaces
            integer_with_spaces = digit + integer_with_spaces
        
        result = integer_with_spaces
        if len(parts) > 1 and parts[1]:
            result += '.' + parts[1]
        elif '.' in formatted:
            result += '.0'
        
        if num < 0:
            result = '-' + result
        
        return result
    except:
        return num_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        num1_str = data.get('num1', '0')
        num2_str = data.get('num2', '0')
        operation = data.get('operation', 'add')
        
        num1_normalized = normalize_number(num1_str)
        num2_normalized = normalize_number(num2_str)
        
        if num1_normalized is None or num2_normalized is None:
            return jsonify({'error': 'Некорректный формат числа'})
        
        num1 = float(num1_normalized)
        num2 = float(num2_normalized)
        
        if not (check_range(num1) and check_range(num2)):
            return jsonify({
                'error': 'Число выходит за допустимый диапазон (±1 000 000 000 000.000000)'
            })
        
        if operation == 'add':
            result = num1 + num2
        elif operation == 'subtract':
            result = num1 - num2
        elif operation == 'multiply':
            result = num1 * num2
        elif operation == 'divide':
            if num2 == 0:
                return jsonify({'error': 'Деление на ноль невозможно'})
            result = round(num1 / num2, 6)
            result = float(f"{result:.6f}")
        else:
            return jsonify({'error': 'Неизвестная операция'})
        
        if not check_range(result):
            return jsonify({
                'error': 'Переполнение! Результат выходит за допустимый диапазон'
            })
        
        result_str = str(result)
        if result_str.endswith('.0'):
            result_str = result_str[:-2]
        
        formatted_result = format_number(result_str)
        
        return jsonify({
            'result': formatted_result,
            'normalized_num1': num1_normalized,
            'normalized_num2': num2_normalized
        })
        
    except ValueError:
        return jsonify({'error': 'Ошибка преобразования числа'})
    except Exception:
        return jsonify({'error': 'Ошибка сервера'})

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    app.run(debug=True, host='0.0.0.0', port=5001)