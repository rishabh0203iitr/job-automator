"""All prompt templates for AI operations."""

SCORE_SYSTEM = """You are an expert career advisor and job matching specialist.
Analyze job listings against candidate profiles to determine fit."""

SCORE_PROMPT = """Rate how well this job matches the candidate profile on a scale of 0-100.

## Candidate Profile
- Name: {name}
- Title: {title}
- Experience: {years_experience} years
- Skills: {skills}
- Location preference: {location}

## Job Listing
- Title: {job_title}
- Company: {job_company}
- Location: {job_location}
- Salary: {job_salary}
- Description:
{job_description}

## Instructions
Respond with ONLY valid JSON in this exact format:
{{"score": <0-100>, "reasons": "<2-3 sentence explanation of the score>"}}

Consider: skill match, experience level, location compatibility, role relevance, and growth potential."""

TAILOR_SYSTEM = """You are an expert resume writer who tailors resumes for specific job applications.
You maintain truthfulness while optimizing keyword matching and relevance."""

TAILOR_PROMPT = """Tailor this resume for the following job posting. Keep all information truthful
but reorganize, reword, and emphasize relevant experience and skills.

## Original Resume
{resume_text}

## Target Job
Title: {job_title}
Company: {job_company}
Description:
{job_description}

## Instructions
Return the tailored resume content. Maintain the same format but:
1. Reorder bullet points to highlight relevant experience first
2. Add relevant keywords from the job description naturally
3. Quantify achievements where possible
4. Keep it concise and impactful
5. Do NOT fabricate any experience or skills"""

COVER_LETTER_SYSTEM = """You are an expert cover letter writer who creates compelling,
personalized cover letters for job applications."""

COVER_LETTER_PROMPT = """Write a cover letter for this job application.

## Candidate
- Name: {name}
- Current/Target Title: {title}
- Skills: {skills}
- Experience: {years_experience} years

## Resume Summary
{resume_text}

## Target Job
- Title: {job_title}
- Company: {job_company}
- Description:
{job_description}

## Instructions
Write a professional cover letter that:
1. Opens with a compelling hook (not "I am writing to apply...")
2. Connects specific experience to job requirements
3. Shows knowledge of the company
4. Conveys enthusiasm without being generic
5. Keeps it under 300 words
6. Ends with a clear call to action"""

COLD_EMAIL_SYSTEM = """You are an expert at writing cold emails to hiring managers
that get responses. You write concise, personalized, value-driven emails."""

COLD_EMAIL_PROMPT = """Write a cold email to a hiring manager about this job opportunity.

## Candidate
- Name: {name}
- Title: {title}
- Key Skills: {skills}

## Recipient
- Name: {recipient_name}
- Title: {recipient_title}
- Company: {company}

## Job Details
- Title: {job_title}
- Description summary:
{job_description}

## Instructions
Write a cold email that:
1. Has a compelling subject line
2. Opens with something specific about the company (not generic flattery)
3. Briefly states relevant value proposition (2-3 sentences max)
4. Includes a soft call to action
5. Total length: under 150 words
6. Tone: professional but human

Respond in this format:
SUBJECT: <subject line>
---
<email body>"""

EXTRACT_JOB_FROM_POST = """Extract job information from this social media post.

## Post
Author: {author}
Content:
{content}

## Instructions
Extract any job-related information and respond with JSON:
{{"title": "<job title or empty>", "company": "<company or empty>",
  "location": "<location or empty>", "url": "<application url or empty>",
  "summary": "<brief summary of the opportunity>"}}

If this doesn't appear to be a job posting, set all fields to empty strings."""
