# MLB Scouting Tracker

**Stack:** PostgreSQL, Python (Flask), Pandas, HTML/CSS  

## Project Overview
MLB Scouting Tracker is a full-stack relational database application designed to manage baseball players, scouts, and performance metrics. The goal is to calculate professional 20-80 scouting grades using real-world Statcast data (Exit Velocity, Whiff %, xwOBA, etc.) mapped against league averages.

---

## Tech Stack
* **Database:** PostgreSQL (`psycopg2`)
* **Backend:** Python 3, Flask
* **Data Processing:** Pandas, Numpy
* **Frontend:** HTML5, Jinja2 Templating

---

## Prerequisites
Before running, make sure you have the following installed on your machine:
* [Python 3.8+](https://www.python.org/downloads/)
* [PostgreSQL](https://www.postgresql.org/download/) (Make sure the Postgres server is running)
* Git

---

### File Structure
```text
MLB-SCOUTING
├── backend/
│   ├── data/ # raw csv files
│   ├── templates/ # flask/html templates
│   ├── .env # secret credentials
│   ├── app.py # where flask starts
│   ├── calculate_grade.py
│   ├── database.py
│   └── populate.py
├── frontend/
│   ├── public/
│   └── src/
├── .gitignore
├── README.md
└── requirements.txt
```


## Setup & Installation Guide

### 1. Clone the Repository
```bash
git clone [https://github.com/devonddunham/mlb-scouting.git](https://github.com/devonddunham/mlb-scouting.git)
cd mlb-scouting
```

### 2. Install Requirments
```bash
pip install -r requirements.txt
```
### 3. Create .env File
```text
DB_HOST=localhost
DB_NAME=mlb_scouting_db
DB_USER=postgres
DB_PASS=your_super_password
DB_PORT=5432
```

### 4. Inintialize and Populate DB
```bash
python3 database.py
python3 populate.py # this one may take some time
```

### 5. Start Flask App
```bash
# pwd needs to be in backend/
flask run
```

