from flask import Flask, request, send_from_directory, render_template, send_file, abort
from werkzeug.utils import secure_filename
from music21 import *
import subprocess
import tempfile
import os


app = Flask(__name__, static_url_path='')

# Get the path from environment variable, or use the default for local development
MUSESCORE_PATH = os.environ.get('MUSESCORE_PATH', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')


@app.route("/")
def root():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return abort(400, 'No file part')

    file = request.files['file']
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return abort(400, 'No selected file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, filename)
            file.save(file_path)

            score = converter.parse(file_path)
            for note in score.recurse().notes:
                try:
                    note.addLyric(note.pitch.name)
                except:
                    continue

            music_xml_path = os.path.join(temp_dir, "music.xml")
            music_pdf_path = os.path.join(temp_dir, "music.pdf")

            score.write('musicxml', music_xml_path)
            subprocess.run([MUSESCORE_PATH, music_xml_path, '-o', music_pdf_path])

            return send_file(music_pdf_path, as_attachment=True)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mid', 'midi'}


@app.route('/download')
def download_file():
    return send_from_directory('', 'Result-1.png', as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
