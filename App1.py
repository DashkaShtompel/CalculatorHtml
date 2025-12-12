from flask import Flask, render_template, request, jsonify
import locale
import re

app = Flask(__name__)

def normalize_number(num_str):
    if not num_str:
        return "0"
    normalized = num_str.strip().replace(',', '.')
    if normalized and normalized[0] == '-':
        cleaned = '-' + re.sub(r'[^\d.]', '', normalized[1:])
    else:
        cleaned = re.sub(r'[^\d.]', '', normalized)
    if cleaned in ['', '.', '-', '-.']:
        return "0"
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = parts[0] + '.' + ''.join(parts[1:])
    return cleaned

def check_range(num):
    limit = 1_000_000_000_000.000000
    return -limit <= num <= limit

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
        else:
            return jsonify({'error': 'Неизвестная операция'})
        
        if not check_range(result):
            return jsonify({
                'error': 'Переполнение! Результат выходит за допустимый диапазон'
            })
        
        result_str = f"{result:.6f}".rstrip('0').rstrip('.')
        if result_str == "-0":
            result_str = "0"
            
        return jsonify({
            'result': result_str,
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