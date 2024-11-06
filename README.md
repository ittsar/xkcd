# XKCD Viewer Application

This is a Flask-based web application for viewing and managing XKCD comics. It provides an interactive interface to browse, view, and update comics from the XKCD website.

## Features

-   **View XKCD Comics**: Browse comics interactively with navigation controls.
-   **Search and Jump to Comics**: Jump directly to a specific comic by entering its number.
-   **Random Comic**: View a random comic at the click of a button.
-   **Update Comics**: Automatically fetch the latest comics or trigger updates manually.
-   **Swagger API Documentation**: Interactively explore the application's API endpoints.
-   **Cache Management**: Improve performance with caching for frequently accessed data.

## Requirements

### Python Packages

Install the required Python packages using `pip`:

`pip install Flask requests flasgger Flask-Caching` 

Alternatively, use the provided `install_requirements` function in `xkcd.py`:

`requirements_text = """
Flask==3.0.3
requests==2.32.3
flasgger==0.9.7.1
Flask-Caching==2.3.0
"""
install_requirements(requirements_text)` 

## Setup

1.  Clone this repository or copy the `xkcd.py` file to your project.
2.  Ensure you have Python 3.7+ installed.
3.  Create the required `xkcd_comics` directory and metadata file by running the app. They will be generated automatically if missing.

## Usage

Run the application with:

`python xkcd.py` 

### Access the Application:

-   **Comic Viewer**: http://localhost:5000/
-   **Update Status Page**: http://localhost:5000/update
-   **Swagger API Docs**: http://localhost:5000/apidocs/

### API Endpoints

Method

Endpoint

Description

GET

`/api/comics`

Retrieve metadata for all comics.

GET

`/api/comics/<comic_number>`

Get metadata for a specific comic.

GET

`/api/comics/<comic_number>/image`

Get the image for a specific comic.

GET

`/api/comics/random`

Retrieve metadata for a random comic.

GET

`/api/comics/navigate`

Navigate to the next/previous comic.

POST

`/api/update`

Trigger a manual update of comics.

GET

`/api/status`

Get the last update time and status.

## Features in Detail

### 1. **Comic Viewer**

-   View comics interactively.
-   Navigate using `Next`, `Previous`, or `Random` buttons.
-   Jump to a specific comic using the input box.

### 2. **Update Comics**

-   Automatically fetch the latest XKCD comics.
-   Manual updates via the `/update` page.

### 3. **Swagger Documentation**

Explore the API interactively at `/apidocs`.

### 4. **Cache Management**

-   Cached responses for improved performance.

## Future Enhancements

-   **Database Integration**: Store metadata in a database (e.g., SQLite).
-   **Improved UI**: Enhance the frontend with pagination and better design.
-   **Real-time Updates**: Show progress during updates using WebSocket.
