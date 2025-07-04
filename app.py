import os
import uuid
import yt_dlp
from flask import Flask,render_template,request,send_from_directory

app=Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    download_url = None

    if request.method == 'POST':
        url = request.form.get('url')
        format_choice = request.form.get('format')

        unique_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}.%(ext)s")

        ydl_opts = {
            'outtmpl': output_template,
            'ffmpeg_location': r'C:\Users\khush\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin' 
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
        elif format_choice == 'mp4':
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
                'merge_output_format': 'mp4',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.download([url])
            
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(unique_id):
                    download_url = f"/download/{file}"
                    break
        except Exception as e:
            return f"Error: {str(e)}"

    return render_template('index.html', download_url=download_url)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)