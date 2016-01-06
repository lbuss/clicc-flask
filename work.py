from flask import Flask, request, redirect, jsonify, url_for
from utils import *
from threading import Thread
from werkzeug import secure_filename
app = Flask(__name__)
from modules.exposure.exposure_mod import ExposureMod as Exposure
from modules.qsar.qsar_mod import QSARmod as QSAR
from modules.lcia.net_prediction import NetPrediction as LCIA
from modules.ft.fate_and_transport_lvl4 import FateAndTransport as FAT

ALLOWED_EXTENSIONS = set(['txt'])
exp = Exposure()
qsar = QSAR()
lcia = LCIA()
fat = FAT()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


@app.route('/run_job', methods=['POST'])
def run_job():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            chem = qsar.run(file)[0]
            chem['MD'] = request.form['MD']
            fat_results = fat.run(chem)
            exposure_results = exp.run(fat_results['exposure_inputs'])
            print chem
            return jsonify({'results':  {
                'exposure': exposure_results,
                'fat': fat_results['fat_outputs'],
                'qsar': chem
                }})
# @app.route('/submit', methods=['POST'])
# def run_job():
#     query = request.form['query']
#     chem = chem_spider.get_chem(query)
#     if chem:
#         results = modules.run(chem)[0]
#         return jsonify(results)
#     else:
#         return 204


# @app.route('/search', methods=['POST'])
# def search_cs():
#     query = request.form['query']
#     # hooks=dict(response=print_url)
#     chem = chem_spider.get_chem(query)
#     return jsonify(chem)

@app.route('/exposure_test', methods=['GET'])
def run_exposure_default_values():
    result = exp.run()
    return jsonify(result)

@app.route('/qsar_test', methods=['GET'])
def run_qsar_default_values():
    result = qsar.run()
    print result
    return jsonify({'parsed_results':result})

@app.route('/lcia_test', methods=['GET'])
def run_lcia_default_values():
    result = lcia.predict()
    return jsonify({'parsed_results':result})

@app.route('/upload_epi_result', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            chems_array = qsar.run(file)
            for chem in chems_array:
                for module in [ft, exp]:
                    chem.update(module.run(chem))

            return jsonify({'parsed_results':chems_array})

@app.route('/test_ft_exposure', methods=['GET'])
def test_ft_exposure():
        fat_outs = fat.run({})
        exposure_results = exp.run(fat_outs)
        return jsonify({'results': exposure_results})



if __name__ == '__main__':
    app.run(debug=True)
