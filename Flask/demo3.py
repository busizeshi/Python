"""
请求对象
"""
from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    return f'Hello, {username}!'

if __name__ == '__main__':
    app.run(debug=True)