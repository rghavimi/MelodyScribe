from flask import Flask, request, render_template, send_file, abort
from werkzeug.utils import secure_filename
from flask_talisman import Talisman
from music21 import *
import subprocess
import tempfile
import logging
import sys
import os

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='')

# Enforces security protocols (e.g. http -> https, etc.)
Talisman(app, content_security_policy=None)

MAX_FILENAME_SIZE = 40
MELODY_SCRIBE_COPYRIGHT = "© 2023 MelodyScribe"

# Get the path from environment variable, or use the default for local development
PDF_TO_MUSIC_PATH = os.environ.get('PDF_TO_MUSIC_PATH', '/Applications/PDFtoMusic Pro.app/Contents/MacOS/PDFtoMusic')
MUSESCORE_PATH = os.environ.get('MUSESCORE_PATH', '/Applications/MuseScore 3.app/Contents/MacOS/mscore')
HEADLESS_MODE_ENABLED = os.environ.get('HEADLESS_MODE_ENABLED', False)

if HEADLESS_MODE_ENABLED:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


@app.route("/")
def root():
    return render_template('index.html')


@app.route('/robots.txt')
def serve_robots_txt():
    return send_file('static/robots.txt', mimetype='text/plain')


@app.route("/privacy-policy")
def serve_privacy_policy():
    return render_template('privacy-policy.html')


@app.route('/predict', methods=['POST'])
def predict():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return abort(400, 'No file part')

    file = request.files['file']
    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return abort(400, 'No selected file')

    if is_midi(file.filename):
        return convert_midi_to_annotated_pdf(file)
    else:
        return convert_pdf_to_annotated_pdf(file)


def convert_midi_to_annotated_pdf(file):
    if not is_midi(file.filename):
        return abort(400, 'Must be a .mid or .midi file.')

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        score = converter.parse(file_path)
        filename_without_extension = os.path.splitext(file.filename)[0][:MAX_FILENAME_SIZE]
        music_xml_path = os.path.join(temp_dir, "music.xml")

        annotate_music_xml(score, filename_without_extension, music_xml_path)

        music_pdf_path = os.path.join(temp_dir, f"{filename_without_extension}.pdf")
        subprocess.run([MUSESCORE_PATH, music_xml_path, '-o', music_pdf_path])

        return send_file(music_pdf_path, as_attachment=True)


def convert_pdf_to_annotated_pdf(file):
    if not is_pdf(file.filename):
        return abort(400, 'Must be a .mid or .midi file.')

    filename = secure_filename(file.filename)
    filename_without_extension = os.path.splitext(file.filename)[0][:MAX_FILENAME_SIZE]
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join('/app/', filename)
        file.save(file_path)

        music_xml_path = os.path.join('/app/', f"{filename_without_extension}.xml")
        subprocess.run([PDF_TO_MUSIC_PATH, file_path, '-o', music_xml_path], capture_output=True, text=True)
        score = converter.parse(music_xml_path)

        annotate_music_xml(score, filename_without_extension, music_xml_path)

        music_pdf_path = os.path.join('/app/', f"{filename_without_extension}.pdf")
        subprocess.run([MUSESCORE_PATH, music_xml_path, '-o', music_pdf_path])

        return send_file(music_pdf_path, as_attachment=True)


def annotate_music_xml(score, filename_without_extension, music_xml_path):
    # Set the title in the score's metadata
    score_metadata = metadata.Metadata()
    score_metadata.title = filename_without_extension
    score_metadata.copyright = MELODY_SCRIBE_COPYRIGHT
    score.metadata = score_metadata

    for element in score.recurse():
        if isinstance(element, note.Note):
            # For single notes, add the pitch name as a lyric
            element.addLyric(element.pitch.name)
        elif isinstance(element, chord.Chord):
            # For chords, concatenate the names of all notes in the chord
            chord_notes = '\n'.join(note.name for note in element.notes)
            element.addLyric(chord_notes)

    score.write('musicxml', music_xml_path)


def convert_pdf_to_musicxml(pdf_path, output_path):
    command = [PDF_TO_MUSIC_PATH, pdf_path, '-o', output_path]
    subprocess.run(command)


def is_midi(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'mid', 'midi'}


def is_pdf(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf'}


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
