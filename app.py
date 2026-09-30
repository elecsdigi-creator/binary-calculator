# Pulls in the Flask tools needed to run a web server, read incoming data, send JSON responses, and load your HTML file
from flask import Flask, request, jsonify, render_template

# Initializes the actual web application instance
app = Flask(__name__)

def to_decimal(val, base):
    """Converts a string of a given base (with optional fractional part) to a decimal float."""
    # Cleans the input by making it uppercase and removing stray spaces
    val = str(val).upper().strip()
    is_negative = False
    
    # Checks if the number is negative, flags it, and temporarily removes the minus sign to do the math
    if val.startswith('-'):
        is_negative = True
        val = val[1:]
        
    # Checks for a decimal point. If found, splits the string into an integer part and a fractional part
    if '.' in val:
        int_part, frac_part = val.split('.', 1)
    else:
        int_part, frac_part = val, ""
        
    # Uses Python's built-in converter to translate the integer part from its original base into base-10
    dec_val = float(int(int_part, base)) if int_part else 0.0
    
    # If there are decimal places, it loops through each character
    if frac_part:
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, digit in enumerate(frac_part):
            # Finds the character's value (e.g., 'A' = 10) and multiplies it by base^(-index), adding to the total
            dec_val += digits.index(digit) * (base ** -(i + 1))
            
    # Restores the negative sign if one was flagged earlier
    return -dec_val if is_negative else dec_val

def from_decimal(val, base, precision=8):
    """Converts a decimal float to a string of the target base."""
    is_negative = val < 0
    val = abs(float(val))
    
    # Splits the float back into whole and fractional pieces
    int_part = int(val)
    frac_part = val - int_part
    
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    # 1. Handle Integer Part
    if int_part == 0:
        res_int = "0"
    else:
        res_int = ""
        # Repeatedly divides the whole number by the target base, using the remainder to look up the correct character
        while int_part > 0:
            res_int = digits[int_part % base] + res_int
            int_part //= base
            
    # 2. Handle Fractional Part
    res_frac = ""
    # Repeatedly multiplies the fraction by the target base, plucking off the resulting whole numbers
    while frac_part > 0 and len(res_frac) < precision:
        frac_part *= base
        digit_val = int(frac_part)
        res_frac += digits[digit_val]
        frac_part -= digit_val
        
    # Glues the two halves together to build the final string
    result = res_int
    if res_frac:
        result += "." + res_frac
        
    return "-" + result if is_negative else result

# When someone visits the main page, this serves the My Melody frontend
@app.route('/')
def index():
    return render_template('index.html')

# Creates the API endpoint that the JavaScript talks to when the user click the "Calculate" button
@app.route('/calculate', methods=['POST'])
def calculate():
    # Grabs the package of data (mode, numbers, bases) sent from the frontend
    data = request.json
    mode = data.get('mode')
    out_base = int(data.get('out_base', 10))

    try:
        if mode == 'convert':
            # Translates the single number to base-10, then runs it straight through from_decimal
            num1 = data.get('num1')
            base1 = int(data.get('base1'))
            dec_val = to_decimal(num1, base1)
            result = from_decimal(dec_val, out_base)
            
        elif mode == 'arithmetic':
            # Translates both operands to base-10 first
            num1 = to_decimal(data.get('num1'), int(data.get('base1')))
            num2 = to_decimal(data.get('num2'), int(data.get('base2')))
            op = data.get('operator')

            # Performs standard Python addition, subtraction, multiplication, or division
            if op == '+': ans = num1 + num2
            elif op == '-': ans = num1 - num2
            elif op == '*': ans = num1 * num2
            elif op == '/': 
                # A safety check that returns an error instead of crashing if a user tries to divide by zero
                if num2 == 0:
                    return jsonify({'success': False, 'error': 'Division by zero is undefined.'})
                ans = num1 / num2 

            # Takes the mathematical answer and converts it to the requested output base
            result = from_decimal(ans, out_base)
            
        return jsonify({'success': True, 'result': result})
    except ValueError:
        # If a user types an invalid character (like 'A' in Binary), this catches the internal crash and sends a friendly error
        return jsonify({'success': False, 'error': 'Invalid number character for the selected base.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# A Python rule that means "only run the server if I run this file directly"
# When deployed to Render, Gunicorn ignores this line and takes over the hosting itself
if __name__ == '__main__':
    app.run(debug=True)