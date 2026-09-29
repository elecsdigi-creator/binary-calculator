from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def to_decimal(val, base):
    """Converts a string of a given base (with optional fractional part) to a decimal float."""
    val = str(val).upper().strip()
    is_negative = False
    
    if val.startswith('-'):
        is_negative = True
        val = val[1:]
        
    if '.' in val:
        int_part, frac_part = val.split('.', 1)
    else:
        int_part, frac_part = val, ""
        
    # Convert integer part
    dec_val = float(int(int_part, base)) if int_part else 0.0
    
    # Convert fractional part
    if frac_part:
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, digit in enumerate(frac_part):
            # Each fractional place is multiplied by base^(-index)
            dec_val += digits.index(digit) * (base ** -(i + 1))
            
    return -dec_val if is_negative else dec_val

def from_decimal(val, base, precision=8):
    """Converts a decimal float to a string of the target base."""
    is_negative = val < 0
    val = abs(float(val))
    
    int_part = int(val)
    frac_part = val - int_part
    
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # 1. Handle Integer Part
    if int_part == 0:
        res_int = "0"
    else:
        res_int = ""
        while int_part > 0:
            res_int = digits[int_part % base] + res_int
            int_part //= base
            
    # 2. Handle Fractional Part
    res_frac = ""
    # Multiply the fraction by the base, extract the whole number, repeat
    while frac_part > 0 and len(res_frac) < precision:
        frac_part *= base
        digit_val = int(frac_part)
        res_frac += digits[digit_val]
        frac_part -= digit_val
        
    # Combine
    result = res_int
    if res_frac:
        result += "." + res_frac
        
    return "-" + result if is_negative else result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    mode = data.get('mode')
    out_base = int(data.get('out_base', 10))

    try:
        if mode == 'convert':
            num1 = data.get('num1')
            base1 = int(data.get('base1'))
            dec_val = to_decimal(num1, base1)
            result = from_decimal(dec_val, out_base)
            
        elif mode == 'arithmetic':
            num1 = to_decimal(data.get('num1'), int(data.get('base1')))
            num2 = to_decimal(data.get('num2'), int(data.get('base2')))
            op = data.get('operator')

            if op == '+': ans = num1 + num2
            elif op == '-': ans = num1 - num2
            elif op == '*': ans = num1 * num2
            elif op == '/': 
                if num2 == 0:
                    return jsonify({'success': False, 'error': 'Division by zero is undefined.'})
                ans = num1 / num2 # Standard floating-point division

            result = from_decimal(ans, out_base)
            
        return jsonify({'success': True, 'result': result})
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid number character for the selected base.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)