import os
import uuid
import shutil
import yt_dlp
import zipfile
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
BASE_DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

tasks = {}  

def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                z.write(full_path, arcname)

def schedule_deletion(path, delay=1800):
    def delete():
        try:
            if os.path.isfile(path):
                os.remove(path)
                print(f"[Deleted file] {path}")
            elif os.path.isdir(path):
                shutil.rmtree(path)
                print(f"[Deleted folder] {path}")
        except Exception as e:
            print(f"[Failed to delete] {path}: {e}")
    threading.Timer(delay, delete).start()

def run_download(task_id, url, format_choice):
    try:
        unique_id = task_id
        download_folder = os.path.join(BASE_DOWNLOAD_DIR, unique_id)
        os.makedirs(download_folder, exist_ok=True)

        output_template = os.path.join(download_folder, '%(title).100s.%(ext)s')

        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'restrictfilenames': True,
            'ffmpeg_location': r'C:\Users\khush\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin',
        }

        if format_choice == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            ydl_opts.update({
                'format': 'bestvideo[height<=720]+bestaudio[ext=m4a]/best[height<=720]',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        if 'entries' in info:  # Playlist
            zip_filename = f"{unique_id}.zip"
            zip_path = os.path.join(BASE_DOWNLOAD_DIR, zip_filename)
            zip_folder(download_folder, zip_path)
            shutil.rmtree(download_folder)
            tasks[task_id] = {'status': 'done', 'file': zip_filename}
            schedule_deletion(zip_path)
        else:
            files = os.listdir(download_folder)
            if not files:
                raise Exception("No files downloaded.")
            file_path = os.path.join(download_folder, files[0])
            tasks[task_id] = {'status': 'done', 'file': f"{unique_id}/{files[0]}"}
            schedule_deletion(file_path)

    except Exception as e:
        tasks[task_id] = {'status': 'error', 'error': str(e)}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_download():
    url = request.form.get('url')
    format_choice = request.form.get('format')

    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {'status': 'pending'}
    thread = threading.Thread(target=run_download, args=(task_id, url, format_choice))
    thread.start()

    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'status': 'not_found'}), 404
    return jsonify(task)

@app.route('/download/<path:filename>')
def download_file(filename):
    full_path = os.path.join(BASE_DOWNLOAD_DIR, filename)
    if not os.path.isfile(full_path):
        return "File not found", 404
    return send_from_directory(os.path.dirname(full_path), os.path.basename(full_path), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
