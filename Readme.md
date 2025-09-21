The project is built on a modular architecture to separate the user interface, business logic, and data storage. This makes it easier to develop and maintain each part of the application independently.

How the Project Works in Depth
The application workflow is driven by a client-server model. The Streamlit frontend acts as the client, sending requests to the FastAPI backend, which processes the data and interacts with the database and scoring algorithm.

1. User Authentication
When the application starts, it checks the user's session state. If the user isn't logged in, they are presented with a main page offering three options: Sign In, Sign Up, or Admin.

Sign Up: The user fills out a form, and the data is sent to the create_user function in database.py. This function inserts the new user's credentials into the users table.

Sign In & Admin: The user enters their credentials. The login_page function checks these against the users table or the hardcoded admin credentials. A successful login sets the user's role and redirects them to the appropriate dashboard.

2. Job Description Management (Admin)
The admin page provides a link to a separate page for posting new job descriptions.

The admin provides a job title and uploads a file.

The post_jd_page function in main.py sends this data to the /upload_jd endpoint in api.py.

The backend saves the file to the data/jds directory and inserts the job's metadata (role and filename) into the jobs table in the database.

3. Resume Submission and Analysis (Student)
After a student logs in, they see a list of available jobs.

They select a job from the dropdown menu and upload their resume.

The student_page function sends the resume and job description filename to the /upload_resume endpoint in api.py.

The backend saves the resume file and then calls the score_resume function from scoring.py.

The score_resume function performs a multi-faceted analysis:

It extracts text from both the resume and the job description.

It calculates a hard match score by comparing shared keywords.

It calculates a semantic score using the Sentence-Transformers library to measure the contextual similarity of the documents.

It calculates a content bonus based on the number of relevant skills, projects, and certifications found in the resume.

These three scores are combined and scaled to produce a final relevance score.

The backend then stores the analysis results in the resumes table and sends the data back to the frontend.

The student's page displays the final verdict (Strong, Moderate, or Weak Match) and a bulleted list of any missing skills, certifications, and projects.

This detailed architecture ensures a secure, efficient, and user-friendly experience for both students and administrators.
