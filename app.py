import os
import uuid
import shutil
import yt_dlp
import zipfile
from flask import Flask, render_template, request, send_from_directory, redirect, url_for

app = Flask(__name__)

BASE_DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

def zip_folder(folder_path, zip_path):
    # Zip all files in folder_path into zip_path.
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, start=folder_path)
                z.write(full_path, arcname)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        format_choice = request.form.get('format')

        unique_id = str(uuid.uuid4())[:8]
        download_folder = os.path.join(BASE_DOWNLOAD_DIR, unique_id)
        os.makedirs(download_folder, exist_ok=True)

        output_template = os.path.join(download_folder, '%(title).100s.%(ext)s')

        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'restrictfilenames': True,  # sanitize filenames
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
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                'merge_output_format': 'mp4',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            if 'entries' in info:  # playlist detected
                zip_filename = f"{unique_id}.zip"
                zip_path = os.path.join(BASE_DOWNLOAD_DIR, zip_filename)
                zip_folder(download_folder, zip_path)
                shutil.rmtree(download_folder)
                download_url = f"/download/{zip_filename}"
            else:
                files = os.listdir(download_folder)
                if not files:
                    raise Exception("No files downloaded.")
                download_url = f"/download/{unique_id}/{files[0]}"

            return redirect(url_for('index', download_url=download_url))
        except Exception as e:
            return redirect(url_for('index', error=str(e)))

    download_url = request.args.get('download_url')
    error = request.args.get('error')
    return render_template('index.html', download_url=download_url, error=error)

@app.route('/download/<path:filename>')
def download_file(filename):
    full_path = os.path.join(BASE_DOWNLOAD_DIR, filename)
    if not os.path.isfile(full_path):
        return "File not found!", 404
    dir_path = os.path.dirname(full_path)
    file_name_only = os.path.basename(full_path)
    return send_from_directory(dir_path, file_name_only, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
