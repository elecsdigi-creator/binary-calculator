from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# NEW HELPER: Adds commas to large numbers and removes ".0" from integers
def fmt_num(n):
    try:
        f = float(n)
        return f"{int(f):,}" if f.is_integer() else f"{f:,}"
    except:
        return str(n)

def to_decimal(val, base):
    val = str(val).upper().strip()
    is_negative = val.startswith('-')
    if is_negative:
        val = val[1:]
        
    int_part, frac_part = val.split('.', 1) if '.' in val else (val, "")
    
    dec_val = 0.0
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    poly_terms = []
    
    if int_part:
        for i, char in enumerate(reversed(int_part)):
            val_num = digits.index(char)
            dec_val += val_num * (base ** i)
            poly_terms.append(f"({val_num} × {base}<sup>{i}</sup>)")
            
    if frac_part:
        for i, char in enumerate(frac_part):
            val_num = digits.index(char)
            dec_val += val_num * (base ** -(i + 1))
            poly_terms.append(f"({val_num} × {base}<sup>-{(i + 1)}</sup>)")
            
    if is_negative: dec_val = -dec_val
    
    if base == 10:
        step_str = f"<span class='step-header'>🌸 Operand <b>{val}</b> is already in Base 10.</span>"
    else:
        int_poly = " + ".join(reversed(poly_terms[:len(int_part)])) if int_part else "0"
        frac_poly = " + ".join(poly_terms[len(int_part):]) if frac_part else ""
        full_poly = int_poly + (" + " + frac_poly if frac_poly else "")
        
        # Wrapped in a clean math block
        step_str = f"<span class='step-header'>🌸 Convert {val} (Base {base}) to Base 10:</span>"
        step_str += f"<div class='math-block'>{full_poly} <br><br><b>= {fmt_num(abs(dec_val))}</b></div>"
        if is_negative: step_str += f"<div class='math-block'><i>Apply negative sign:</i> <b>{fmt_num(dec_val)}</b></div>"
        
    return dec_val, step_str

def from_decimal(val, base, precision=8):
    is_negative = val < 0
    val = abs(float(val))
    
    if base == 10:
        val_str = str(int(val)) if val.is_integer() else str(val)
        res_str = ("-" if is_negative else "") + val_str
        return res_str, "<span class='step-header'>✨ Target is Base 10. No further conversion needed.</span>"

    int_part = int(val)
    frac_part = val - int_part
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    steps = [f"<span class='step-header'>✨ Convert {fmt_num(val)} (Base 10) to Base {base}:</span>"]
    
    if int_part == 0:
        res_int = "0"
        steps.append("<div class='math-block'>Integer part is 0.</div>")
    else:
        res_int = ""
        temp_int = int_part
        steps.append("<div class='sub-header'>Integer Part (Repeated Division):</div>")
        
        # Creates tabular rows for the division math
        while temp_int > 0:
            remainder = temp_int % base
            res_int = digits[remainder] + res_int
            steps.append(f"<div class='math-row'><span>{fmt_num(temp_int)} ÷ {base} = {fmt_num(temp_int // base)}</span> <span class='rem-box'>Rem: {remainder} <strong>→ {digits[remainder]}</strong></span></div>")
            temp_int //= base
            
    res_frac = ""
    if frac_part > 0:
        steps.append("<div class='sub-header' style='margin-top: 15px;'>Fractional Part (Repeated Multiplication):</div>")
        temp_frac = frac_part
        while temp_frac > 0 and len(res_frac) < precision:
            old_frac = temp_frac
            temp_frac *= base
            digit_val = int(temp_frac)
            res_frac += digits[digit_val]
            steps.append(f"<div class='math-row'><span>{old_frac} × {base} = {fmt_num(temp_frac)}</span> <span class='rem-box'><strong>→ {digits[digit_val]}</strong></span></div>")
            temp_frac -= digit_val
            
    result = res_int + ("." + res_frac if res_frac else "")
    if is_negative:
        result = "-" + result
        steps.append(f"<div class='math-block'><i>Apply negative sign:</i> <b>{result}</b></div>")
        
    return result, "".join(steps)

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
            
            dec_val, step1 = to_decimal(num1, base1)
            solution_steps.append(step1)
            result, step2 = from_decimal(dec_val, out_base)
            solution_steps.append(step2)
            
        elif mode == 'arithmetic':
            num1 = data.get('num1')
            base1 = int(data.get('base1'))
            num2 = data.get('num2')
            base2 = int(data.get('base2'))
            op = data.get('operator')

            dec1, step1 = to_decimal(num1, base1)
            dec2, step2 = to_decimal(num2, base2)
            solution_steps.extend([step1, step2])

            if op == '+': ans = dec1 + dec2
            elif op == '-': ans = dec1 - dec2
            elif op == '*': ans = dec1 * dec2
            elif op == '/': 
                if dec2 == 0:
                    return jsonify({'success': False, 'error': 'Division by zero is undefined.'})
                ans = dec1 / dec2 

            # Formats the math arithmetic block
            solution_steps.append(f"<span class='step-header'>🎀 Perform Arithmetic (Base 10):</span><div class='math-block'>{fmt_num(dec1)} {op} {fmt_num(dec2)} <br><br>= <b>{fmt_num(ans)}</b></div>")

            result, step3 = from_decimal(ans, out_base)
            solution_steps.append(step3)
            
        final_solution_html = "".join(solution_steps)
        return jsonify({'success': True, 'result': result, 'steps': final_solution_html})
        
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid number character for the selected base.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)