
from flask import Flask, render_template
app = Flask(__name__)


@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/pilot')
def pilot():
    return render_template('indexMQTT.html')

@app.route('/spectator')
def spectator():
    return render_template('spectator.html')

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
