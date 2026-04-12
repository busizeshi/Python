"""
响应对象
"""
from flask import Flask
from flask import make_response

app = Flask(__name__)


@app.route('/custom_response')
def custom_response():
    response = make_response('This is a custom response', 200)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['X-Custom-Header'] = 'Custom Value'
    return response


if __name__ == '__main__':
    app.run(debug=True)
