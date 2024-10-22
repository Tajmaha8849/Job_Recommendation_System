from flask import Flask, request, render_template, redirect, url_for
import fitz  # PyMuPDF for PDF extraction
import requests
import os
from dotenv import load_dotenv
import re

# Load API credentials from .env
load_dotenv()
ADZUNA_APP_ID = os.getenv('ADZUNA_APP_ID')
ADZUNA_API_KEY = os.getenv('ADZUNA_API_KEY')

app = Flask(__name__)

# Route to upload resume
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        resume = request.files['resume']
        if resume and resume.filename.endswith('.pdf'):
            skills = extract_skills_from_pdf(resume)
            return redirect(url_for('get_jobs', skills=skills))
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

# Extract skills from PDF resume
def extract_skills_from_pdf(resume):
    text = ""
    with fitz.open(stream=resume.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    
    # Predefined skills (you can expand this list)
    predefined_skills = ['Python', 'Java', 'SQL', 'Flask', 'JavaScript', 'C++', 'HTML', 'CSS', 'Django', 'React', 'Node.js', 'AWS', 'Azure']
    
    # Normalize text to lower case for matching
    text_lower = text.lower()

    # Find skills using regular expressions
    found_skills = [skill for skill in predefined_skills if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower)]
    
    return ", ".join(found_skills) if found_skills else "No skills found"

# Route to fetch and display recommended jobs
@app.route('/jobs')
def get_jobs():
    skills = request.args.get('skills', '')
    jobs = fetch_jobs_from_adzuna(skills)
    job_count = len(jobs)  # Get the total number of jobs found
    return render_template('jobs.html', jobs=jobs, count=job_count)

# Function to fetch jobs from Adzuna API
def fetch_jobs_from_adzuna(skills):
    # Split the skills into a list
    skill_list = skills.split(', ')
    
    # Use a set to avoid duplicate jobs
    job_set = set()

    for skill in skill_list:
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        params = {
            'app_id': ADZUNA_APP_ID,
            'app_key': ADZUNA_API_KEY,
            'results_per_page': 10,
            'what': skill,
        }
        response = requests.get(url, params=params)

        if response.status_code == 200:
            results = response.json().get('results', [])
            for job in results:
                # Use job title and company as a unique identifier for jobs
                job_key = (job.get('title'), job.get('company', {}).get('display_name', 'N/A'))
                job_set.add(job_key)  # Add to set to avoid duplicates

    # Convert the set back to a list and format the output
    jobs = [
        {
            'title': title,
            'company_name': company,
            'url': job.get('redirect_url'),  # Use the redirect URL directly
            'tags': skills.split(', ')
        }
        for title, company in job_set
    ]
    
    return jobs

if __name__ == '__main__':
    app.run(debug=True)
