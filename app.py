After changing the `create_sample_excel.py` file name to `create.py`, the updated `app.py` file content will be as follows:

```python
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
# from linkedin import linkedin  # Removed because not used and causes error
import openai
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Set Streamlit page configuration
st.set_page_config(
    page_title="B2B Cold Email Generator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        margin-top: 1rem; /* Add top margin for button spacing */
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .company-header {
        background-color: #333333; /* Darker background for better dark mode integration */
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0 4rem 0; /* Increased bottom margin for more space between companies */
        color: #FFFFFF; /* Ensure text is visible */
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #cce5ff;
        color: #004085;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Create exports directory if it doesn't exist
EXPORTS_DIR = "n8n_exports"
if not os.path.exists(EXPORTS_DIR):
    try:
        os.makedirs(EXPORTS_DIR)
    except FileExistsError:
        pass  # Directory was created by another process, we can ignore this error

def scrape_website(url):
    """Scrape company website for relevant information."""
    try:
        # Add a timeout to prevent hanging
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic information
        title = soup.title.string if soup.title else "No title found"
        description_meta = soup.find('meta', {'name': 'description'})
        description = description_meta['content'] if description_meta else "No description found"
        
        # Extract main content from common tags
        paragraphs = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])])
        main_content = paragraphs if paragraphs else "No main content found"
        
        return {
            'title': title,
            'description': description,
            'main_content': main_content[:1500]  # Limit content length, increased slightly
        }
    except requests.exceptions.RequestException as e:
        st.warning(f"Could not scrape website '{url}': {str(e)}")
        return None
    except Exception as e:
        st.warning(f"An unexpected error occurred while scraping '{url}': {str(e)}")
        return None

def generate_cold_email(company_data):
    """Generate personalized cold email using OpenAI."""
    try:
        website_info = company_data.get('website_data', {}) or {}
        site_description = website_info.get('description', '')
        site_content = website_info.get('main_content', '')
        
        prompt = f"""
        You are a professional B2B sales email writer.
        Craft a compelling, personalized cold email for a B2B prospect.
        
        Here's the prospect's information:
        - Company Name: {company_data['company_name']}
        - Head Name: {company_data['head_name']}
        - Head Email: {company_data['head_email']}
        - Company Website: {company_data['website']}
        - LinkedIn URL: {company_data['linkedin_url']}
        
        Additional information from their website:
        - Website Description: {site_description}
        - Website Main Content Snippet: {site_content}
        
        The email should:
        1.  Be concise (max 150 words) and professional yet conversational.
        2.  Show a clear understanding of their business based on the provided data.
        3.  Present a specific, clear value proposition of how your (imaginary) product/service could benefit them.
        4.  End with a clear and actionable call to action.
        5.  Avoid generic phrases and make it highly personalized.
        """
        
        with st.spinner("Generating cold email with AI..."):
            response = openai.ChatCompletion.create(
                model="gpt-4", # Using GPT-4 for better quality
                messages=[
                    {"role": "system", "content": "You are a highly skilled B2B sales email writer, focusing on personalization and clear value."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300 # Ensure conciseness
            )
        
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error generating email: {str(e)}")
        return None

def generate_follow_up(company_data, previous_email, days_since_last_email):
    """Generate follow-up email based on previous communication."""
    try:
        prompt = f"""
        You are a professional B2B sales email writer.
        Create a concise follow-up email for {company_data['head_name']} at {company_data['company_name']}.
        It has been {days_since_last_email} days since the last email.
        
        Previous email:
        {previous_email}
        
        The follow-up should:
        1.  Reference the previous email briefly.
        2.  Add new value, a fresh perspective, or address a potential objection.
        3.  Reiterate a clear call to action.
        4.  Be concise (max 100 words).
        """
        
        with st.spinner("Generating follow-up email..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional B2B sales email writer, skilled in crafting effective follow-ups."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200 # Ensure conciseness
            )
        
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        st.error(f"OpenAI API Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error generating follow-up: {str(e)}")
        return None

def main():
    # Header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/email.png", width=100)
    with col2:
        st.title("📧 B2B Cold Email Generator")
        st.markdown("### Automate personalized cold emails and follow-ups using AI")
    
    # Sidebar with upload and sponsor section
    with st.sidebar:
        st.markdown("### 📤 Upload Data")
        st.markdown("---")
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'], 
                                       help="Upload a CSV or Excel file with your prospect data.")
        
        st.markdown("---")
        st.markdown("### 🎯 Features")
        st.markdown("""
        - 🤖 AI-powered email generation
        - 🌐 Automatic website scraping
        - 📊 Data export to n8n
        - 🔄 Follow-up email generation
        """)
        
        st.markdown("---")
        st.markdown("### 💼 Our Sponsor")
        st.markdown("""
        <div style='text-align: center;'>
            <img src='https://n8n.io/images/n8n-logo.svg' width='150'>
            <p>Check out n8n for workflow automation!</p>
            <a href='https://n8n.io/' target='_blank'>Visit n8n</a>
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.markdown("### 📊 Uploaded Data Preview")
            st.dataframe(df.style.set_properties(**{
                'background-color': '#f0f2f6',
                'color': '#262730',
                'border-color': '#e6e6e6'
            }))
            
            required_columns = ['company_name', 'head_name', 'head_email', 'website', 'linkedin_url']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.markdown("""
                <div class='error-box'>
                    <h4>⚠️ Missing Required Columns</h4>
                    <p>Please ensure your CSV/Excel file has these columns: `company_name`, `head_name`, `head_email`, `website`, `linkedin_url`</p>
                </div>
                """, unsafe_allow_html=True)
                return
            
            st.markdown("### ✉️ Generated Emails & Actions")
            
            for index, row in df.iterrows():
                try:
                    st.markdown(f"""
                    <div class='company-header'>
                        <h3>🏢 {row['company_name']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        with st.spinner(f"🔍 Scraping {row['website']}..."):
                            website_data = scrape_website(row['website'])
                        
                        company_data = {
                            'company_name': row['company_name'],
                            'head_name': row['head_name'],
                            'head_email': row['head_email'],
                            'website': row['website'],
                            'linkedin_url': row['linkedin_url'],
                            'website_data': website_data
                        }
                        
                        with st.expander(f"🌐 View Website Scrape Data for {row['company_name']}"):
                            if website_data:
                                st.json(website_data)
                            else:
                                st.markdown("""
                                <div class='info-box'>
                                    No website data scraped or an error occurred.
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Generate cold email and store in session state first
                        if f"cold_email_{index}" not in st.session_state:
                            with st.spinner(f"🤖 Generating cold email for {row['company_name']}..."):
                                cold_email = generate_cold_email(company_data)
                                if cold_email:
                                    st.session_state[f"cold_email_{index}"] = cold_email
                                else:
                                    st.markdown("""
                                    <div class='error-box'>
                                        Failed to generate cold email.
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # Display the cold email from session state
                        if f"cold_email_{index}" in st.session_state:
                            st.markdown("### 📝 Generated Cold Email")
                            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                            st.text_area("", st.session_state[f"cold_email_{index}"], height=250, key=f"display_cold_email_{index}")
                            st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

                    with col2:
                        st.markdown("### ⚡ Actions", unsafe_allow_html=True)
                        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                        
                        # Follow-up email generation
                        if st.button(f"🔄 Generate Follow-up for {row['company_name']}", key=f"followup_{index}"):
                            if f"cold_email_{index}" in st.session_state:
                                days_since_last = st.number_input("📅 Days since last email", min_value=1, value=7, key=f"days_{index}")
                                follow_up = generate_follow_up(company_data, st.session_state[f"cold_email_{index}"], days_since_last)
                                if follow_up:
                                    st.markdown("### 📨 Generated Follow-up Email")
                                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                                    st.text_area("", follow_up, height=200, key=f"followup_content_{index}")
                                    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
                                    st.session_state[f"follow_up_{index}"] = follow_up
                                else:
                                    st.markdown("""
                                    <div class='error-box'>
                                        Failed to generate follow-up email.
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                <div class='info-box'>
                                    Please generate the cold email first.
                                </div>
                                """, unsafe_allow_html=True)

                        if f"follow_up_{index}" in st.session_state:
                            st.markdown("### 📨 Generated Follow-up Email")
                            st.text_area("", st.session_state[f"follow_up_{index}"], height=200, key=f"followup_content_{index}")

                        # Export to n8n
                        if st.button(f"📤 Export to n8n for {row['company_name']}", key=f"export_{index}"):
                            try:
                                workflow_data = {
                                    'company_data': company_data,
                                    'cold_email': st.session_state.get(f"cold_email_{index}", "No email generated"),
                                    'follow_up_email': st.session_state.get(f"follow_up_{index}", "No follow-up generated"),
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                safe_company_name = "".join(c for c in row["company_name"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                                filename = f'n8n_export_{safe_company_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                                filepath = os.path.join(EXPORTS_DIR, filename)
                                
                                with open(filepath, 'w') as f:
                                    json.dump(workflow_data, f, indent=2)
                                
                                with open(filepath, 'r') as f:
                                    st.download_button(
                                        label="📥 Download JSON for n8n",
                                        data=f.read(),
                                        file_name=filename,
                                        mime="application/json",
                                        key=f"download_{index}"
                                    )
                                
                                st.markdown("""
                                <div class='success-box'>
                                    Data exported successfully!
                                </div>
                                """, unsafe_allow_html=True)
                                
                                with st.expander("📋 How to import into n8n"):
                                    st.markdown("""
                                    To import this data into n8n:
                                    1. 📥 Download the JSON file using the button above
                                    2. 🔧 In n8n, open or create a workflow
                                    3. 📁 Add a **'Read Binary File'** node to read the JSON file
                                        *   *(Optional: If you use the sample n8n workflow I created, you'll paste the JSON content directly into the 'Process Data' Function node.)*
                                    4. 🔄 Connect it to your email sending node
                                    5. 🔐 Ensure your email credentials are set up in n8n
                                    """)
                            except Exception as e:
                                st.markdown(f"""
                                <div class='error-box'>
                                    Error exporting data: {str(e)}
                                </div>
                                """, unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"""
                    <div class='error-box'>
                        Error processing row {index + 1} ({row.get('company_name', 'Unknown Company')}): {str(e)}
                    </div>
                    """, unsafe_allow_html=True)
                    continue
        except Exception as e:
            st.markdown(f"""
            <div class='error-box'>
                Error reading file: {str(e)}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class='info-box'>
                Please ensure your file is in the correct format with all required columns.
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
```

This update reflects the change in the file name from `create_sample_excel.py` to `create.py`.