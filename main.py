import streamlit as st
import time
from pathlib import Path
from typing import Optional
import base64
from io import BytesIO
from matcher import screen_candidate, read_resume, parse_job_description, parse_resume, match_resume_with_job

# Page configuration
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
def load_css():
    st.markdown("""
    <style>
        /* Main container styling */
        .main {
            padding: 0 2rem;
        }
        
        /* Header styling */
        .header-container {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem 3rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .header-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }
        
        /* Card styling */
        .card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e8ecf1;
            margin-bottom: 1.5rem;
            transition: transform 0.2s;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }
        
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #1e3c72;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Score display */
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto;
            background: conic-gradient(
                from 0deg,
                #4CAF50 var(--score),
                #e0e0e0 var(--score)
            );
            position: relative;
        }
        
        .score-inner {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            background: white;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .score-number {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1e3c72;
        }
        
        .score-label {
            font-size: 0.8rem;
            color: #666;
            font-weight: 500;
        }
        
        /* Verdict badges */
        .badge-strong {
            background: #4CAF50;
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            font-size: 0.9rem;
        }
        
        .badge-moderate {
            background: #FFA726;
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            font-size: 0.9rem;
        }
        
        .badge-not {
            background: #ef5350;
            color: white;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-weight: 600;
            display: inline-block;
            font-size: 0.9rem;
        }
        
        /* Skill tags */
        .skill-tag {
            background: #e3f2fd;
            color: #1e3c72;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            margin: 0.2rem;
            display: inline-block;
            border: 1px solid #bbdefb;
        }
        
        .skill-tag-missing {
            background: #ffebee;
            color: #c62828;
            border-color: #ffcdd2;
        }
        
        .skill-tag-match {
            background: #e8f5e9;
            color: #2e7d32;
            border-color: #c8e6c9;
        }
        
        /* Section divider */
        .section-divider {
            border: none;
            border-top: 2px solid #e8ecf1;
            margin: 2rem 0;
        }
        
        /* Upload area */
        .upload-area {
            border: 2px dashed #bbdefb;
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            background: #f8f9fa;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #1e3c72;
            background: #f0f4ff;
        }
        
        /* Status messages */
        .status-success {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        
        .status-error {
            background: #ffebee;
            color: #c62828;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ef5350;
        }
        
        /* Info boxes */
        .info-box {
            background: #e3f2fd;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            border-left: 4px solid #1e3c72;
            margin: 1rem 0;
        }
        
        /* Metrics */
        .metric-card {
            text-align: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1e3c72;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #666;
            margin-top: 0.2rem;
        }
        
        /* Responsive columns */
        @media (max-width: 768px) {
            .header-title {
                font-size: 1.8rem;
            }
            .card {
                padding: 1rem;
            }
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #bbdefb;
            border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #1e3c72;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'job_text' not in st.session_state:
        st.session_state.job_text = ""
    if 'resume_file' not in st.session_state:
        st.session_state.resume_file = None

def get_verdict_badge(verdict: str):
    verdict_lower = verdict.lower()
    if 'strong' in verdict_lower or 'excellent' in verdict_lower:
        return '<span class="badge-strong">✅ Strong Fit</span>'
    elif 'moderate' in verdict_lower or 'good' in verdict_lower:
        return '<span class="badge-moderate">⚠️ Moderate Fit</span>'
    else:
        return '<span class="badge-not">❌ Not Suitable</span>'

def display_results(results):
    match_data = results['match']
    job_data = results['job']
    resume_data = results['resume']
    
    # Main results container
    st.markdown("---")
    st.markdown("## 📊 Screening Results")
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{match_data['match_score']:.1f}%</div>
            <div class="metric-label">Match Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        skills_count = len(match_data.get('matching_skills', []))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{skills_count}</div>
            <div class="metric-label">Matching Skills</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        missing_count = len(match_data.get('missing_skills', []))
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{missing_count}</div>
            <div class="metric-label">Missing Skills</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        exp_met = "✅" if match_data['experience_requirement_met'] else "❌"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{exp_met}</div>
            <div class="metric-label">Experience Requirement</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Verdict
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0;">
        <h3>Verdict</h3>
        {get_verdict_badge(match_data['verdict'])}
    </div>
    """, unsafe_allow_html=True)
    
    # Two-column layout for details
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 🎯 Matching Skills")
        skills = match_data.get('matching_skills', [])
        if skills:
            skill_html = "".join([f'<span class="skill-tag skill-tag-match">✅ {s}</span> ' for s in skills])
            st.markdown(skill_html, unsafe_allow_html=True)
        else:
            st.info("No matching skills found")
        
        st.markdown("### 📋 Required Skills")
        required_skills = job_data.get('required_skills', [])
        if required_skills:
            skill_html = "".join([f'<span class="skill-tag">{s}</span> ' for s in required_skills])
            st.markdown(skill_html, unsafe_allow_html=True)
        else:
            st.info("No skills listed")
    
    with col_right:
        st.markdown("### ⚠️ Missing Skills")
        missing_skills = match_data.get('missing_skills', [])
        if missing_skills:
            skill_html = "".join([f'<span class="skill-tag skill-tag-missing">❌ {s}</span> ' for s in missing_skills])
            st.markdown(skill_html, unsafe_allow_html=True)
        else:
            st.success("All required skills are present! 🎉")
        
        st.markdown("### 🎓 Preferred Skills")
        preferred_skills = job_data.get('preferred_skills', [])
        if preferred_skills:
            skill_html = "".join([f'<span class="skill-tag">⭐ {s}</span> ' for s in preferred_skills])
            st.markdown(skill_html, unsafe_allow_html=True)
        else:
            st.info("No preferred skills listed")
    
    # Detailed sections in expandable format
    with st.expander("📄 Job Description Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Job Role:**")
            st.write(job_data.get('job_role', 'Not specified'))
            st.markdown("**Minimum Experience:**")
            st.write(f"{job_data.get('minimum_experience', 0)} years")
            st.markdown("**Educational Requirements:**")
            for edu in job_data.get('educational_requirements', []):
                st.write(f"• {edu}")
        with col2:
            st.markdown("**Responsibilities:**")
            for resp in job_data.get('responsibilities', [])[:5]:
                st.write(f"• {resp}")
            if len(job_data.get('responsibilities', [])) > 5:
                st.write(f"... and {len(job_data['responsibilities']) - 5} more")
    
    with st.expander("👤 Candidate Resume Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Name:**")
            st.write(resume_data.get('name', 'Not provided'))
            st.markdown("**Email:**")
            st.write(resume_data.get('email', 'Not provided'))
            st.markdown("**Total Experience:**")
            st.write(f"{resume_data.get('total_experience_year', 0):.1f} years")
        with col2:
            st.markdown("**Skills:**")
            for skill in resume_data.get('skills', [])[:10]:
                st.write(f"• {skill}")
            if len(resume_data.get('skills', [])) > 10:
                st.write(f"... and {len(resume_data['skills']) - 10} more")
            st.markdown("**Education:**")
            for edu in resume_data.get('education', [])[:3]:
                st.write(f"• {edu}")

def main():
    # Load CSS
    load_css()
    init_session_state()
    
    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">
            📄 AI Resume Screener
            <span style="font-size: 0.8rem; opacity: 0.8; font-weight: 400;">
                Powered by AI
            </span>
        </div>
        <div class="header-subtitle">
            Intelligent resume screening and job matching using advanced AI
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown("""
        <div class="card">
            <div class="card-title">📋 Job Description</div>
        </div>
        """, unsafe_allow_html=True)
        
        job_input = st.text_area(
            "Paste job description here",
            height=300,
            placeholder="Enter the complete job description including role, responsibilities, requirements, and qualifications...",
            key="job_text_area",
            value=st.session_state.job_text
        )
        
        if st.button("📝 Load Sample JD", type="secondary"):
            sample_jd = """
            Senior Software Engineer - Backend

            About the Role:
            We are looking for a highly skilled Senior Software Engineer with expertise in Python and cloud technologies.

            Key Responsibilities:
            - Design and develop scalable backend services using Python and FastAPI
            - Implement microservices architecture and RESTful APIs
            - Optimize database queries and ensure high performance
            - Lead technical discussions and mentor junior developers
            - Collaborate with cross-functional teams to deliver features

            Required Skills:
            - 5+ years of experience in backend development
            - Strong proficiency in Python
            - Experience with FastAPI or Django
            - Working knowledge of Docker and Kubernetes
            - Experience with AWS or Azure cloud platforms
            - Strong understanding of SQL and NoSQL databases

            Preferred Skills:
            - Experience with TypeScript
            - Knowledge of CI/CD pipelines
            - Familiarity with Redis or similar caching solutions

            Educational Requirements:
            - Bachelor's degree in Computer Science or related field
            - Master's degree is a plus
            """
            st.session_state.job_text = sample_jd
            st.rerun()
        
        st.caption("💡 Tip: For best results, include clear sections for responsibilities, required skills, and experience requirements")
    
    with col_right:
        st.markdown("""
        <div class="card">
            <div class="card-title">📎 Resume Upload</div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload candidate's resume",
            type=['pdf', 'docx'],
            help="Supported formats: PDF, DOCX",
            key="resume_uploader"
        )
        
        if uploaded_file:
            st.markdown(f"""
            <div class="status-success">
                ✅ File uploaded: <strong>{uploaded_file.name}</strong><br>
                📊 Size: {uploaded_file.size / 1024:.1f} KB
            </div>
            """, unsafe_allow_html=True)
            st.session_state.resume_file = uploaded_file
    
    # Process button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        process_btn = st.button(
            "🚀 Analyze Resume Match",
            type="primary",
            use_container_width=True,
            disabled=not (job_input and uploaded_file)
        )
    
    # Info box
    if not (job_input and uploaded_file):
        st.markdown("""
        <div class="info-box">
            📌 Please provide both the job description and a resume to begin screening.
        </div>
        """, unsafe_allow_html=True)
    
    # Process the analysis
    if process_btn and job_input and uploaded_file:
        try:
            with st.spinner("🔄 Analyzing resume against job description..."):
                # Progress simulation
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("📄 Parsing job description...")
                progress_bar.progress(20)
                time.sleep(0.5)
                
                status_text.text("📝 Extracting resume information...")
                progress_bar.progress(40)
                time.sleep(0.5)
                
                status_text.text("🔍 Matching skills and experience...")
                progress_bar.progress(60)
                time.sleep(0.5)
                
                status_text.text("📊 Calculating match score...")
                progress_bar.progress(80)
                time.sleep(0.5)
                
                # Run the screening
                results = screen_candidate(
                    job_description=job_input,
                    resume_content=uploaded_file.getvalue(),
                    resume_filename=uploaded_file.name
                )
                
                status_text.text("✅ Analysis complete!")
                progress_bar.progress(100)
                time.sleep(0.3)
                
                # Store results in session state
                st.session_state.results = results
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Screening completed successfully!")
                
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            st.session_state.results = None
    
    # Display results if available
    if st.session_state.results:
        display_results(st.session_state.results)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem; padding: 1rem;">
            Made with ❤️ using Streamlit & AI
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()