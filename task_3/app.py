from flask import Flask, request, Response

app = Flask(__name__)

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

def lcm(x, y):
    return x * y // gcd(x, y)

@app.route('/kamzinanazgul_outlook_com', methods=['GET'])
def compute_lcm():
    x = request.args.get('x')
    y = request.args.get('y')

    # Проверка: оба должны быть неотрицательными целыми
    if not (x and y and x.isdigit() and y.isdigit()):
        return Response("NaN", mimetype='text/plain')

    x = int(x)
    y = int(y)

    result = lcm(x, y)
    return Response(str(result), mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)