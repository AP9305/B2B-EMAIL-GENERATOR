# B2B Cold Email Automation System

This system automates the process of generating and sending personalized cold emails to B2B prospects. It uses AI to analyze company information and create compelling emails, with follow-up capabilities.

## Features

- Upload prospect data via CSV/Excel
- Automated website scraping for company information
- AI-powered personalized email generation
- Follow-up email generation
- Integration with n8n for email automation
- Streamlit-based user interface

## Prerequisites

- Python 3.8+
- n8n instance
- OpenAI API key
- MongoDB (for n8n workflow)

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
EMAIL_FROM=your_email@domain.com
```

## Usage

1. Prepare your input data in CSV or Excel format with the following columns:
   - company_name
   - head_name
   - head_email
   - website
   - linkedin_url

2. Start the Streamlit app:
```bash
streamlit run app.py
```

3. Upload your data file through the Streamlit interface

4. The system will:
   - Scrape company websites for additional information
   - Generate personalized cold emails
   - Allow generation of follow-up emails
   - Export data to n8n for automation

## n8n Workflow Setup

1. Import the `n8n_workflow.json` into your n8n instance
2. Configure the following nodes:
   - Watch Folder: Set the path to monitor for new files
   - Email Send: Configure your email credentials
   - MongoDB: Set up your database connection

3. Activate the workflow

## Input File Format

Your input file should be a CSV or Excel file with the following columns:

| company_name | head_name | head_email | website | linkedin_url |
|-------------|-----------|------------|---------|--------------|
| Company A   | John Doe  | john@a.com | https://... | https://... |
| Company B   | Jane Smith| jane@b.com | https://... | https://... |

## Security Notes

- Never commit your `.env` file
- Keep your API keys secure
- Use environment variables for sensitive data
- Follow email sending best practices and regulations

## Support

For issues and feature requests, please open an issue in the repository.