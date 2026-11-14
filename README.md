# Lunch

A weekly lunch and dinner planner. Plan 14 meals, keep a pantry, build a shopping list, set a budget and your own ingredient prices.

Two ways to run it:

- **Page only.** Open `index.html` or turn on GitHub Pages. Your plan is saved in that browser only.
- **With a database.** `app.py` is a small Flask app that serves the same page, asks for a password, and keeps your plan in SQLite so it follows you across devices.

## Run it locally

    pip install -r requirements.txt
    LUNCH_PASSWORD=pick-one SECRET_KEY=anything LUNCH_INSECURE_COOKIES=1 flask --app app run

Then open http://127.0.0.1:5000/.

## Put it on PythonAnywhere

1. Open a Bash console and run:

       git clone https://github.com/daniel235/Lunch lunch

2. Web tab, Add a new web app, Manual configuration, newest Python.
3. Set Source code to `/home/YOURNAME/lunch`.
4. Click the WSGI configuration file link and replace everything in it with:

       import os, sys
       path = '/home/YOURNAME/lunch'
       if path not in sys.path:
           sys.path.insert(0, path)
       os.environ['LUNCH_PASSWORD'] = 'your-password'
       os.environ['SECRET_KEY'] = 'a-long-random-string'
       from app import app as application

5. Reload the web app. Visit `https://YOURNAME.pythonanywhere.com/lunch/`.

Free accounts need you to press the extend button on the Web tab about once a month.

To update later: Bash console, `cd lunch && git pull`, then Reload.

Your data lives in `data/lunch.db`. The server also keeps the previous save as `state_previous`.
