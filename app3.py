from flask import Flask, render_template, request, jsonify
import locale
import re
import decimal
import math

app = Flask(__name__)

decimal.getcontext().prec = 28

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
    if len(parts) == 2 and len(parts[1]) > 10:
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
    if len(parts) == 2 and len(parts[1]) > 10:
        return None
    return cleaned

def check_range(num):
    limit = 1_000_000_000_000.000000
    return -limit <= num <= limit

def check_intermediate_range(num):
    limit = 1_000_000_000_000.000000000
    return -limit <= num <= limit

def round_intermediate(num):
    return round(num, 10)

def format_number(num_str):
    try:
        num = float(num_str)
        if num == 0:
            return "0"
        
        formatted = f"{abs(num):.10f}".rstrip('0').rstrip('.')
        
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

def apply_rounding(result, method):
    try:
        num = float(result)
        
        if method == 'mathematical':
            rounded = round(num)
        elif method == 'bankers':
            if abs(num - round(num)) == 0.5:
                rounded = round(num / 2) * 2
            else:
                rounded = round(num)
        elif method == 'truncate':
            rounded = math.trunc(num)
        else:
            rounded = round(num)
        
        return int(rounded)
    except:
        return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        numbers = []
        operations = []
        
        for i in range(1, 5):
            num_str = data.get(f'num{i}', '0')
            num_normalized = normalize_number(num_str)
            if num_normalized is None:
                return jsonify({'error': f'Некорректный формат числа {i}'})
            numbers.append(float(num_normalized))
            
            if not check_range(numbers[i-1]):
                return jsonify({'error': f'Число {i} выходит за допустимый диапазон'})
        
        for i in range(1, 4):
            op = data.get(f'op{i}', 'add')
            operations.append(op)
        
        rounding_method = data.get('rounding', 'mathematical')
        
        if operations[1] == 'divide' and numbers[2] == 0:
            return jsonify({'error': 'Деление на ноль во второй операции'})
        
        if operations[2] == 'divide' and numbers[3] == 0:
            return jsonify({'error': 'Деление на ноль в третьей операции'})
        
        intermediate1 = 0
        if operations[1] == 'add':
            intermediate1 = numbers[1] + numbers[2]
        elif operations[1] == 'subtract':
            intermediate1 = numbers[1] - numbers[2]
        elif operations[1] == 'multiply':
            intermediate1 = numbers[1] * numbers[2]
        elif operations[1] == 'divide':
            intermediate1 = numbers[1] / numbers[2]
        
        intermediate1 = round_intermediate(intermediate1)
        
        if not check_intermediate_range(intermediate1):
            return jsonify({'error': 'Переполнение в промежуточном вычислении'})
        
        intermediate2 = 0
        if operations[0] == 'add':
            intermediate2 = numbers[0] + intermediate1
        elif operations[0] == 'subtract':
            intermediate2 = numbers[0] - intermediate1
        elif operations[0] == 'multiply':
            intermediate2 = numbers[0] * intermediate1
        elif operations[0] == 'divide':
            if intermediate1 == 0:
                return jsonify({'error': 'Деление на ноль в первой операции'})
            intermediate2 = numbers[0] / intermediate1
        
        intermediate2 = round_intermediate(intermediate2)
        
        if not check_intermediate_range(intermediate2):
            return jsonify({'error': 'Переполнение в промежуточном вычислении'})
        
        final_result = 0
        if operations[2] == 'add':
            final_result = intermediate2 + numbers[3]
        elif operations[2] == 'subtract':
            final_result = intermediate2 - numbers[3]
        elif operations[2] == 'multiply':
            final_result = intermediate2 * numbers[3]
        elif operations[2] == 'divide':
            if numbers[3] == 0:
                return jsonify({'error': 'Деление на ноль в третьей операции'})
            final_result = intermediate2 / numbers[3]
        
        final_result = round_intermediate(final_result)
        
        if not check_range(final_result):
            return jsonify({'error': 'Переполнение! Результат выходит за допустимый диапазон'})
        
        final_result_str = f"{final_result:.10f}".rstrip('0').rstrip('.')
        if final_result_str == "-0":
            final_result_str = "0"
        
        formatted_result = format_number(final_result_str)
        rounded_result = apply_rounding(final_result, rounding_method)
        
        normalized_numbers = []
        for i in range(1, 5):
            num_str = data.get(f'num{i}', '0')
            norm = normalize_number(num_str)
            if norm is None:
                norm = "0"
            normalized_numbers.append(norm)
        
        return jsonify({
            'result': formatted_result,
            'rounded_result': str(rounded_result),
            'normalized_numbers': normalized_numbers,
            'operations': operations
        })
        
    except ValueError:
        return jsonify({'error': 'Ошибка преобразования числа'})
    except Exception as e:
        return jsonify({'error': f'Ошибка вычисления: {str(e)}'})

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    app.run(debug=True, host='0.0.0.0', port=5001)