import subprocess

def install_requirements(requirements: str):
    """
    Install the provided pip requirements.

    Args:
        requirements (str): A string containing requirements, formatted as pip freeze output.
    """
    for line in requirements.strip().split('\n'):
        package = line.split('==')[0]  # Get the package name without the version
        version = line.split('==')[1]  # Get the specific version
        try:
            print(f"Installing {package}=={version}...")
            subprocess.check_call(['pip', 'install', f'{package}=={version}'])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}=={version}: {e}")
    print("All installations complete.")

# Example usage
requirements_text = """
Flask==3.0.3
requests==2.32.3
flasgger==0.9.7.1
Flask-Caching==2.3.0
"""

#install_requirements(requirements_text)

from flask import Flask, jsonify, send_from_directory, request, render_template_string
import os
import json
import threading
import time
import random
import requests
from flasgger import Swagger, swag_from
from flask_caching import Cache


# Initialize Flask app
app = Flask(__name__)
swagger = Swagger(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Configuration: Set this to True to update on startup
UPDATE_ON_STARTUP = True

# Directory setup
comic_dir = 'xkcd_comics'
json_file_path = os.path.join(comic_dir, 'xkcd_metadata.json')

# Last update status
last_update = {
    "status": "idle",
    "time": None
}
update_lock = threading.Lock()


def ensure_setup():
    """Ensure xkcd_comics directory and metadata file exist, and trigger update if necessary."""
    # Ensure the comics directory exists
    if not os.path.exists(comic_dir):
        os.makedirs(comic_dir)
        print(f"Created directory: {comic_dir}")

    # Ensure the metadata JSON file exists
    if not os.path.exists(json_file_path):
        with open(json_file_path, 'w') as json_file:
            json.dump([], json_file)
        print(f"Created empty metadata file: {json_file_path}")

    # Trigger update if either was missing
    if not comics_metadata:
        print("Triggering update as metadata was missing or empty.")
        update_comics()

# Load metadata
def load_metadata():
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            return json.load(json_file)
    return []

comics_metadata = load_metadata()

def fetch_comic(comic_num=None):
    """Fetch a single comic by its number and save its image and metadata."""
    base_url = 'https://xkcd.com'
    url = f'{base_url}/{comic_num}/info.0.json' if comic_num else f'{base_url}/info.0.json'
    
    response = requests.get(url)
    if response.status_code != 200:
        return None
    
    data = response.json()
    comic_num = data['num']
    title = data['title']
    caption = data['alt']
    img_url = data['img']
    
    img_filename = f"xkcd_{comic_num}.png"
    img_path = os.path.join(comic_dir, img_filename)
    
    # Download and save the image
    img_response = requests.get(img_url, stream=True)
    if img_response.status_code == 200:
        with open(img_path, 'wb') as img_file:
            for chunk in img_response.iter_content(1024):
                img_file.write(chunk)
    
    # Store metadata
    return {
        "comic_number": comic_num,
        "file_name": img_filename,
        "title": title,
        "caption": caption
    }

def update_comics():
    """Update comics in a background thread."""
    global last_update
    with update_lock:
        if last_update['status'] == 'updating':
            return
        last_update['status'] = 'updating'
        last_update['time'] = time.strftime("%Y-%m-%d %H:%M:%S")
    
        existing_comic_numbers = {comic['comic_number'] for comic in comics_metadata}
        latest_comic_data = fetch_comic()
        if not latest_comic_data:
            last_update['status'] = 'failed'
            return
        
        latest_comic_number = latest_comic_data['comic_number']
        new_comics = []

        for comic_num in range(1, latest_comic_number + 1):
            if comic_num not in existing_comic_numbers:
                comic_data = fetch_comic(comic_num)
                if comic_data:
                    new_comics.append(comic_data)

        if new_comics:
            comics_metadata.extend(new_comics)
            with open(json_file_path, 'w') as json_file:
                json.dump(comics_metadata, json_file, indent=4)
        
        last_update['status'] = 'idle'

@app.route('/api/comics/navigate', methods=['GET'])
def navigate_comics():
    """Navigate to the next or previous comic based on current comic number."""
    current = int(request.args.get('current', 1))
    direction = request.args.get('direction', 'next')
    
    if direction == 'next':
        next_comic = next((comic for comic in comics_metadata if comic['comic_number'] > current), None)
    else:
        next_comic = next((comic for comic in reversed(comics_metadata) if comic['comic_number'] < current), None)
    
    if next_comic:
        return jsonify(next_comic)
    return jsonify({"error": "No more comics in this direction"}), 404

@app.route('/api/comics/<int:comic_number>/image', methods=['GET'])
def get_comic_image(comic_number):
    """Retrieve the image file for a specific comic."""
    img_filename = f"xkcd_{comic_number}.png"
    img_path = os.path.join(comic_dir, img_filename)
    if os.path.exists(img_path):
        return send_from_directory(comic_dir, img_filename)
    return jsonify({"error": "Image not found"}), 404

@app.route('/api/comics/random', methods=['GET'])
def get_random_comic():
    """Retrieve a random comic."""
    if not comics_metadata:
        return jsonify({"error": "No comics available"}), 404
    comic = random.choice(comics_metadata)
    return jsonify(comic)

@app.route('/api/comics', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'List all comics metadata',
            'examples': {
                'application/json': [
                    {
                        "comic_number": 1,
                        "file_name": "xkcd_1.png",
                        "title": "Barrel - Part 1",
                        "caption": "Don't we all."
                    }
                ]
            }
        }
    }
})
def get_comics():
    """Retrieve all comic metadata."""
    return jsonify(comics_metadata)

@app.route('/api/comics/<int:comic_number>', methods=['GET'])
@swag_from({
    'parameters': [
        {
            'name': 'comic_number',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'The comic number to retrieve metadata for.'
        }
    ],
    'responses': {
        200: {
            'description': 'Comic metadata',
            'examples': {
                'application/json': {
                    "comic_number": 1,
                    "file_name": "xkcd_1.png",
                    "title": "Barrel - Part 1",
                    "caption": "Don't we all."
                }
            }
        },
        404: {
            'description': 'Comic not found'
        }
    }
})
@cache.cached(timeout=300)
def get_comic(comic_number):
    """Retrieve metadata for a specific comic by its number."""
    # Ensure the metadata contains the requested comic_number
    comic = next((comic for comic in comics_metadata if comic['comic_number'] == comic_number), None)
    if comic:
        return jsonify(comic)
    return jsonify({"error": "Comic not found"}), 404


@app.route('/api/update', methods=['POST'])
@swag_from({
    'responses': {
        202: {
            'description': 'Update started'
        },
        400: {
            'description': 'Update already in progress'
        }
    }
})
def trigger_update():
    """Trigger the update process asynchronously.
    ---
    tags:
      - Comics
    responses:
      202:
        description: Update started.
      400:
        description: Update already in progress.
    """
    if last_update['status'] == 'updating':
        return jsonify({"status": "Update already in progress"}), 400
    threading.Thread(target=update_comics).start()
    return jsonify({"status": "Update started"}), 202

@app.route('/api/status', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Get last update status and time',
            'examples': {
                'application/json': {
                    "status": "idle",
                    "time": "2024-11-06 12:00:00"
                }
            }
        }
    }
})
def get_status():
    """Retrieve the last update time and status.
    ---
    tags:
      - Status
    responses:
      200:
        description: Last update status and time.
    """
    return jsonify(last_update)


@app.route('/')
def comic_viewer():
    """Render the comic viewer with direct URL navigation."""
    viewer_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>XKCD Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
            }
            .comic {
                max-width: 600px;
                margin: 20px auto;
            }
            .navigation {
                margin-top: 20px;
            }
            img {
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1 id="title">XKCD Viewer</h1>
        <div class="comic">
            <img loading="lazy" id="comic-img" src="" alt="Comic" title="" />
        </div>
        <div class="navigation">
            <button onclick="navigate('prev')">Previous</button>
            <button onclick="loadRandomComic()">Random</button>
            <button onclick="navigate('next')">Next</button>
        </div>
        <div class="navigation">
            <input type="number" id="comic-input" placeholder="Enter comic number" />
            <button onclick="jumpToComic()">Go</button>
            <script>
                function jumpToComic() {
                    const comicNumber = document.getElementById('comic-input').value;
                    loadComic(comicNumber);
                }
            </script>
        </div>
        <script>
            let currentComic = 1;

            function loadComic(comicNumber) {
                fetch(`/api/comics/${comicNumber}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('title').textContent = `${data.title} (Comic #${data.comic_number})`;
                        const comicImg = document.getElementById('comic-img');
                        comicImg.src = `/api/comics/${data.comic_number}/image`;
                        comicImg.title = data.caption; // Caption as tooltip
                        currentComic = data.comic_number;
                        window.history.pushState({}, '', `/?comic=${data.comic_number}`);
                    });
            }

            function loadRandomComic() {
                fetch('/api/comics/random')
                    .then(response => response.json())
                    .then(data => {
                        loadComic(data.comic_number);
                    });
            }

            function navigate(direction) {
                fetch(`/api/comics/navigate?current=${currentComic}&direction=${direction}`)
                    .then(response => response.json())
                    .then(data => {
                        loadComic(data.comic_number);
                    });
            }

            window.onload = () => {
                const urlParams = new URLSearchParams(window.location.search);
                const comicNumber = urlParams.get('comic') || currentComic;
                loadComic(comicNumber);
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(viewer_template)

@app.route('/update')
def update_page():
    """Render the update status and control page."""
    page_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Update Status</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
            }
            .status {
                margin: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Update Status</h1>
        <div class="status">
            <p>Last Update Time: <span id="last-update-time"></span></p>
            <p>Update Status: <span id="update-status"></span></p>
        </div>
        <button onclick="triggerUpdate()">Trigger Update</button>

        <script>
            function fetchStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('last-update-time').textContent = data.time || 'Never';
                        document.getElementById('update-status').textContent = data.status;
                    });
            }

            function triggerUpdate() {
                fetch('/api/update', { method: 'POST' })
                    .then(response => response.json())
                    .then(() => fetchStatus())
                    .catch(err => console.error(err));
            }

            window.onload = fetchStatus;
        </script>
    </body>
    </html>
    """
    return render_template_string(page_template)

if __name__ == '__main__':
    ensure_setup()
    if UPDATE_ON_STARTUP:
        threading.Thread(target=update_comics).start()
    app.run(debug=True, host='0.0.0.0')
