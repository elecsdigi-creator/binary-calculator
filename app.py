from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def to_decimal(val, base):
    """Converts a string of a given base to a decimal float, AND returns the step-by-step solution."""
    val = str(val).upper().strip()
    is_negative = val.startswith('-')
    if is_negative:
        val = val[1:]
        
    int_part, frac_part = val.split('.', 1) if '.' in val else (val, "")
    
    dec_val = 0.0
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    poly_terms = []
    
    # Process Integer Part
    if int_part:
        for i, char in enumerate(reversed(int_part)):
            val_num = digits.index(char)
            dec_val += val_num * (base ** i)
            poly_terms.append(f"({val_num} × {base}<sup>{i}</sup>)")
            
    # Process Fractional Part
    if frac_part:
        for i, char in enumerate(frac_part):
            val_num = digits.index(char)
            dec_val += val_num * (base ** -(i + 1))
            poly_terms.append(f"({val_num} × {base}<sup>-{(i + 1)}</sup>)")
            
    if is_negative: dec_val = -dec_val
    
    # Generate the solution string for this step
    if base == 10:
        step_str = f"🌸 <b>Operand {val} is already in Base 10.</b>"
    else:
        int_poly = " + ".join(reversed(poly_terms[:len(int_part)])) if int_part else "0"
        frac_poly = " + ".join(poly_terms[len(int_part):]) if frac_part else ""
        full_poly = int_poly + (" + " + frac_poly if frac_poly else "")
        
        step_str = f"🌸 <b>Convert {val} (Base {base}) to Base 10:</b><br>{full_poly} = {abs(dec_val)}"
        if is_negative: step_str += f"<br><i>Apply negative sign:</i> {dec_val}"
        
    return dec_val, step_str

def from_decimal(val, base, precision=8):
    """Converts a decimal float to a string of the target base, AND returns the step-by-step solution."""
    is_negative = val < 0
    val = abs(float(val))
    
    if base == 10:
        val_str = str(int(val)) if val.is_integer() else str(val)
        res_str = ("-" if is_negative else "") + val_str
        return res_str, "✨ <b>Target is Base 10. No further conversion needed.</b>"

    int_part = int(val)
    frac_part = val - int_part
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    steps = [f"✨ <b>Convert {val} (Base 10) to Base {base}:</b>"]
    
    # 1. Handle Integer Part (Repeated Division)
    if int_part == 0:
        res_int = "0"
        steps.append("Integer part is 0.")
    else:
        res_int = ""
        temp_int = int_part
        steps.append("<i>Integer Part (Repeated Division):</i>")
        while temp_int > 0:
            remainder = temp_int % base
            res_int = digits[remainder] + res_int
            steps.append(f"{temp_int} ÷ {base} = {temp_int // base} remainder {remainder} (→ <b>{digits[remainder]}</b>)")
            temp_int //= base
            
    # 2. Handle Fractional Part (Repeated Multiplication)
    res_frac = ""
    if frac_part > 0:
        steps.append("<br><i>Fractional Part (Repeated Multiplication):</i>")
        temp_frac = frac_part
        while temp_frac > 0 and len(res_frac) < precision:
            old_frac = temp_frac
            temp_frac *= base
            digit_val = int(temp_frac)
            res_frac += digits[digit_val]
            steps.append(f"{old_frac} × {base} = {temp_frac} (→ <b>{digits[digit_val]}</b>)")
            temp_frac -= digit_val
            
    result = res_int + ("." + res_frac if res_frac else "")
    if is_negative:
        result = "-" + result
        steps.append(f"<br><i>Apply negative sign:</i> {result}")
        
    return result, "<br>".join(steps)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    mode = data.get('mode')
    out_base = int(data.get('out_base', 10))
    
    solution_steps = []

    try:
        if mode == 'convert':
            num1 = data.get('num1')
            base1 = int(data.get('base1'))
            
            # Step 1: Base X to Base 10
            dec_val, step1 = to_decimal(num1, base1)
            solution_steps.append(step1)
            
            # Step 2: Base 10 to Target Base
            result, step2 = from_decimal(dec_val, out_base)
            solution_steps.append("<br>" + step2)
            
        elif mode == 'arithmetic':
            num1 = data.get('num1')
            base1 = int(data.get('base1'))
            num2 = data.get('num2')
            base2 = int(data.get('base2'))
            op = data.get('operator')

            # Step 1: Convert operands to Base 10
            dec1, step1 = to_decimal(num1, base1)
            dec2, step2 = to_decimal(num2, base2)
            solution_steps.extend([step1, "<br>" + step2])

            # Step 2: Perform Arithmetic
            if op == '+': ans = dec1 + dec2
            elif op == '-': ans = dec1 - dec2
            elif op == '*': ans = dec1 * dec2
            elif op == '/': 
                if dec2 == 0:
                    return jsonify({'success': False, 'error': 'Division by zero is undefined.'})
                ans = dec1 / dec2 

            # Clean up display of .0 for integers
            display1 = int(dec1) if dec1.is_integer() else dec1
            display2 = int(dec2) if dec2.is_integer() else dec2
            display_ans = int(ans) if ans.is_integer() else ans
            
            solution_steps.append(f"<br>🎀 <b>Perform Arithmetic (Base 10):</b><br>{display1} {op} {display2} = {display_ans}")

            # Step 3: Base 10 to Target Base
            result, step3 = from_decimal(ans, out_base)
            solution_steps.append("<br>" + step3)
            
        # Join all HTML steps and send back
        final_solution_html = "<br>".join(solution_steps)
        return jsonify({'success': True, 'result': result, 'steps': final_solution_html})
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid number character for the selected base.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)