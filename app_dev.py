import streamlit as st
import os
import pandas as pd
from utils.supabase_conn import SupaBase
from utils.openai import generate_social_posts, article_to_posts, refine_content
from utils.auth_ui import check_authentication
import base64
from datetime import datetime
import json
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Enhanced page configuration
st.set_page_config(
    page_title="Social Media Content Generator", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Force better visibility
if "visibility_mode" not in st.session_state:
    st.session_state.visibility_mode = "enhanced"

# Custom CSS for modern styling with enhanced visibility
st.markdown("""
<style>
    /* Main theme and colors - Dark mode support */
    :root {
        --background-color: #2d2d2d;
        --text-color: #ffffff;
        --secondary-text-color: #cccccc;
        --border-color: #667eea;
    }
    
    .main {
        padding-top: 2rem;
    }
    
    /* Force visibility for containers and text elements */
    .stContainer, .element-container, .stMarkdown, .stMarkdown p, .stMarkdown div {
        color: #ffffff !important;
    }
    
    /* Make sure all text is visible */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #ffffff !important;
    }
    
    /* Make sure text inputs are visible */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        background-color: #3d3d3d !important;
        color: #ffffff !important;
        border: 2px solid #667eea !important;
    }
    
    /* Fix labels */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stNumberInput label, .stSlider label {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Fix markdown content in general */
    .stMarkdown * {
        color: inherit !important;
    }
    
    /* Ensure buttons are visible */
    .stButton > button {
        background-color: #667eea !important;
        color: white !important;
        border: 2px solid #764ba2 !important;
    }
    
    .stButton > button:hover {
        background-color: #764ba2 !important;
        border-color: #667eea !important;
    }
    
    /* Fix code blocks and expanders */
    .stCode, pre, code {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #667eea !important;
    }
    
    .streamlit-expanderHeader {
        background-color: #3d3d3d !important;
        color: #ffffff !important;
        border: 1px solid #667eea !important;
    }
    
    .streamlit-expanderContent {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #667eea !important;
    }
    
    /* Fix dataframes */
    .stDataFrame {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    .stDataFrame table {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
    }
    
    .stDataFrame th, .stDataFrame td {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border-color: #667eea !important;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    /* Social post card styling - Dark mode compatible */
    .social-post-card {
        background: var(--background-color, #1e1e1e);
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        color: var(--text-color, #ffffff);
    }
    
    .social-post-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.5);
        border-color: #764ba2;
    }
    
    .post-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }
    
    .profile-pic {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        margin-right: 12px;
        font-size: 18px;
    }
    
    .post-meta {
        flex: 1;
    }
    
    .brand-name {
        font-weight: 600;
        font-size: 16px;
        color: var(--text-color, #ffffff);
        margin: 0;
    }
    
    .post-time {
        font-size: 12px;
        color: var(--secondary-text-color, #cccccc);
        margin: 2px 0 0 0;
    }
    
    .post-content {
        font-size: 14px;
        line-height: 1.6;
        color: var(--text-color, #ffffff);
        margin: 15px 0;
        white-space: pre-wrap;
    }
    
    .post-engagement {
        display: flex;
        align-items: center;
        padding-top: 15px;
        margin-top: 15px;
        border-top: 2px solid #667eea;
        font-size: 12px;
        color: var(--secondary-text-color, #cccccc);
    }
    
    .engagement-btn {
        display: flex;
        align-items: center;
        margin-right: 20px;
        cursor: pointer;
        padding: 5px 10px;
        border-radius: 6px;
        transition: background-color 0.2s;
    }
    
    .engagement-btn:hover {
        background-color: #f8f9fa;
    }
    
    /* Brand management cards - Dark mode compatible */
    .brand-card {
        background: var(--background-color, #2d2d2d);
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        color: var(--text-color, #ffffff);
    }
    
    /* Metrics and stats */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 10px 0;
        border: 2px solid #764ba2;
    }
    
    /* Success/Error styling */
    .success-card {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .error-card {
        background: linear-gradient(135deg, #e17055 0%, #d63031 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Enhanced Tab styling for better visibility */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
        background: linear-gradient(135deg, #3d3d3d 0%, #4d4d4d 100%) !important;
        border-radius: 8px 8px 0px 0px !important;
        border: 2px solid #667eea !important;
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #764ba2 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #555555 0%, #666666 100%) !important;
        border-color: #764ba2 !important;
    }
    
    /* Tab content area */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: transparent !important;
        color: #ffffff !important;
        padding-top: 20px !important;
    }
    
    /* Form styling - Dark mode compatible */
    .stForm {
        border: 2px solid #667eea !important;
        border-radius: 12px !important;
        padding: 20px !important;
        background: var(--background-color, #2d2d2d) !important;
        color: var(--text-color, #ffffff) !important;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Hide default Streamlit elements */
    .css-1d391kg {
        padding: 0;
    }
    
    .css-18e3th9 {
        padding-top: 0;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo and branding
current_dir = os.path.dirname(__file__)
image_path = os.path.join(current_dir, r'The Glenwood Group-02.png')

if os.path.exists(image_path):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image_path, width=300)

st.markdown("""
<div class="main-header">
    <h1>Social Media Content Generator</h1>
    <p>Create engaging LinkedIn posts</p>
</div>
""", unsafe_allow_html=True)

# Helper functions for enhanced UI
def create_social_post_card(post, brand_name, post_index, tab_prefix=""):
    """Create a visually appealing social media post card that looks like LinkedIn."""
    
    # Get brand initials for profile picture
    brand_initials = ''.join([word[0].upper() for word in brand_name.split()[:2]])
    
    # Format post content with proper spacing and hashtags
    content = post.get('content', '').replace('\\n', '\n')
    
    # Create the HTML card
    card_html = f"""
    <div class="social-post-card">
        <div class="post-header">
            <div class="profile-pic">{brand_initials}</div>
            <div class="post-meta">
                <div class="brand-name">{brand_name}</div>
                <div class="post-time">{post.get('date', 'Today')} • LinkedIn</div>
            </div>
        </div>
        <div class="post-content">{content}</div>
        <div class="post-engagement">
            <div class="engagement-btn">👍 Like</div>
            <div class="engagement-btn">💬 Comment</div>
            <div class="engagement-btn">🔄 Repost</div>
            <div class="engagement-btn">📤 Send</div>
        </div>
    </div>
    """
    
    return card_html

def create_post_metrics():
    """Create engagement metrics for posts."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Engagement Rate</h3>
            <p style="font-size: 24px; margin: 0;">4.2%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>👥 Reach</h3>
            <p style="font-size: 24px; margin: 0;">12.5K</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>❤️ Likes</h3>
            <p style="font-size: 24px; margin: 0;">523</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>💬 Comments</h3>
            <p style="font-size: 24px; margin: 0;">47</p>
        </div>
        """, unsafe_allow_html=True)

def create_enhanced_export_data(posts, brand_name):
    """Create enhanced export data with visual elements."""
    export_data = []
    
    for i, post in enumerate(posts):
        export_data.append({
            "Post Number": f"#{post.get('number', i+1)}",
            "Date": post.get('date', ''),
            "Brand": brand_name,
            "Content": post.get('content', ''),
            "Graphic Concept": post.get('graphic', ''),
            "Character Count": len(post.get('content', '')),
            "Hashtags": len([word for word in post.get('content', '').split() if word.startswith('#')]),
            "Mentions": len([word for word in post.get('content', '').split() if word.startswith('@')]),
            "Estimated Reach": f"{(i+1) * 1200 + 500}-{(i+1) * 1500 + 800}",
            "Best Time to Post": "9:00 AM - 11:00 AM" if i % 2 == 0 else "1:00 PM - 3:00 PM"
        })
    
    return pd.DataFrame(export_data)

def generate_post_image(post_content, brand_name, post_date, output_path=None):
    """Generate a visual image of the post for download."""
    try:
        # Create figure and axis with better error handling
        plt.style.use('default')  # Use default style to avoid theme issues
        fig, ax = plt.subplots(figsize=(8, 10))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 12)
        ax.axis('off')
        
        # Background
        bg_rect = patches.Rectangle((0.5, 0.5), 9, 11, linewidth=1, 
                                   edgecolor='#e1e8ed', facecolor='white')
        ax.add_patch(bg_rect)
        
        # Header section
        header_rect = patches.Rectangle((0.5, 9.5), 9, 2, linewidth=0, 
                                       facecolor='#f8f9fa')
        ax.add_patch(header_rect)
        
        # Profile circle
        profile_circle = patches.Circle((1.5, 10.5), 0.3, facecolor='#667eea', 
                                       edgecolor='white')
        ax.add_patch(profile_circle)
        
        # Brand initials
        brand_initials = ''.join([word[0].upper() for word in brand_name.split()[:2]])
        ax.text(1.5, 10.5, brand_initials, ha='center', va='center', 
                fontsize=12, fontweight='bold', color='white')
        
        # Brand name and date
        ax.text(2.2, 10.7, brand_name, ha='left', va='center', 
                fontsize=14, fontweight='bold')
        ax.text(2.2, 10.3, f"{post_date} • LinkedIn", ha='left', va='center', 
                fontsize=10, color='#666666')
        
        # Post content - limit length to prevent overflow
        content_preview = post_content[:200] + "..." if len(post_content) > 200 else post_content
        wrapped_content = textwrap.fill(content_preview, width=60)
        ax.text(1, 8.5, wrapped_content, ha='left', va='top', 
                fontsize=11, verticalalignment='top')
        
        # Engagement buttons
        ax.text(1, 1.5, "👍 Like    💬 Comment    🔄 Repost    📤 Send", 
                ha='left', va='center', fontsize=10, color='#666666')
        
        # Save or return
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            return output_path
        else:
            # Convert to base64 for web display
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            return img_base64
    except Exception as e:
        # Return None instead of showing error in UI for this optional feature
        print(f"Warning: Could not generate post image: {str(e)}")
        return None

# Initialize session state variables if they don't exist
if 'generated_posts' not in st.session_state:
    st.session_state.generated_posts = []
if 'selected_posts' not in st.session_state:
    st.session_state.selected_posts = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'brands' not in st.session_state:
    st.session_state.brands = []
if 'supabase_client' not in st.session_state:
    st.session_state.supabase_client = None
if 'show_analytics' not in st.session_state:
    st.session_state.show_analytics = False

# Initialize Supabase connection
try:
    if not st.session_state.supabase_client:
        st.session_state.supabase_client = SupaBase()
        # st.sidebar.success("✅ Connected to Supabase")
except Exception as e:
    st.sidebar.error(f"❌ Supabase connection failed: {str(e)}")
    st.sidebar.warning("Make sure your .env file contains DATABASE_URL and SUPABASE_API")
    st.session_state.supabase_client = None

def get_brand_by_id(brand_id, brands_list):
    """Get brand details by ID from the brands list."""
    for brand in brands_list:
        if brand['id'] == brand_id:
            return brand
    return None

# Load brands when the app starts
if st.session_state.supabase_client:
    current_user_id = st.session_state.get('user_id')
    st.session_state.brands = st.session_state.supabase_client.get_brands(current_user_id)

# Check authentication before showing main app
if not check_authentication():
    st.stop()

# Main app interface with enhanced tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Social Calendar Generator", 
    "📄 Article to Posts", 
    "🏢 Brand Management", 
    "📚 Saved Posts"
])

with tab3:
    st.markdown("### 🏢 Brand Management")
    st.markdown("Create and manage brand profiles with detailed voice guidelines for personalized content generation.")
    
    if not st.session_state.supabase_client:
        st.warning("Supabase connection not available. Please check your .env file configuration.")
    else:
        # Refresh brands button
        if st.button("🔄 Refresh Brands"):
            current_user_id = st.session_state.get('user_id')
            st.session_state.brands = st.session_state.supabase_client.get_brands(current_user_id)
            st.rerun()
        
        # Create new brand section with enhanced styling
        st.markdown("#### ➕ Create New Brand")
        st.markdown("Build a detailed brand profile to generate more personalized and on-brand content.")
        
        with st.form("new_brand_form", clear_on_submit=True):
            # Basic Information Section
            st.markdown("##### 📝 Basic Information")
            col1, col2 = st.columns(2)
            
            with col1:
                brand_name = st.text_input("🏷️ Brand Name*", placeholder="e.g., Wienerschnitzel")
                website = st.text_input("🌐 Website", placeholder="https://www.example.com")
            
            with col2:
                linkedin_url = st.text_input("💼 LinkedIn Company Page", placeholder="https://www.linkedin.com/company/your-company")
                brand_phrases = st.text_input("🎯 Key Brand Phrases", placeholder="e.g., Always fresh, Real ingredients, Made to order")
            
            # Brand Voice Section
            st.markdown("##### 🎭 Brand Voice & Personality")
            
            col1, col2 = st.columns(2)
            with col1:
                brand_voice = st.text_area("Brand Voice*", 
                    placeholder="Describe the brand's communication style...\ne.g., Professional but approachable, authoritative in the fast-food space",
                    height=100)
                
                portrayal = st.text_area("Brand Portrayal*", 
                    placeholder="How does the brand present itself to the world?\ne.g., Family-friendly franchise with focus on quality and consistency",
                    height=100)
            
            with col2:
                overall_voice = st.text_area("Overall Tone*", 
                    placeholder="What's the general communication tone?\ne.g., Informative but casual, enthusiastic about franchising opportunities",
                    height=100)
                
                additional_info = st.text_area("Additional Information", 
                    placeholder="Target audience, industry focus, special considerations...",
                    height=100)
            
            # Content Examples Section
            st.markdown("##### 📚 Content Guidelines")
            previous_posts = st.text_area("Example Posts (Optional but Recommended)", 
                placeholder="""Paste 2-3 examples of your best social media posts here. This helps the AI understand your preferred style:

Example:
🚀 Exciting news! We're expanding our franchise opportunities...

💡 Pro tip: Include posts that performed well or represent your ideal tone.""",
                height=120)
            
            # Submit button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🚀 Create Brand Profile", type="primary", use_container_width=True)
            
            if submitted:
                if brand_name and brand_voice and portrayal and overall_voice:
                    brand_data = {
                        "name": brand_name,
                        "brand_voice": brand_voice,
                        "portrayal": portrayal,
                        "overall_voice": overall_voice,
                        "previous_posts": previous_posts,
                        "brand_phrases": brand_phrases,
                        "website": website,
                        "linkedin_url": linkedin_url,
                        "additional_info": additional_info,
                        "user_id": st.session_state.get('user_id')
                    }
                    
                    with st.spinner("Creating brand profile..."):
                        created_brand = st.session_state.supabase_client.create_brand(brand_data)
                        if created_brand:
                            st.markdown(f"""
                            <div class="success-card">
                                <h4>🎉 Success!</h4>
                                <p>Brand '{brand_name}' has been created successfully!</p>
                            </div>
                            """, unsafe_allow_html=True)
                            current_user_id = st.session_state.get('user_id')
                            st.session_state.brands = st.session_state.supabase_client.get_brands(current_user_id)
                            st.balloons()
                            st.rerun()
                        else:
                            st.markdown("""
                            <div class="error-card">
                                <h4>❌ Error</h4>
                                <p>Failed to create brand. Please try again or check your database connection.</p>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("⚠️ Please fill in all required fields (marked with *)")
        
        # Display existing brands with enhanced styling
        st.markdown("#### 📊 Your Brands")
        
        if st.session_state.brands:
            # Brand summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🏢 Total Brands</h4>
                    <p style="font-size: 24px; margin: 0;">{len(st.session_state.brands)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                active_brands = len([b for b in st.session_state.brands if b.get('website')])
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🌐 With Websites</h4>
                    <p style="font-size: 24px; margin: 0;">{active_brands}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                linkedin_brands = len([b for b in st.session_state.brands if b.get('linkedin_url')])
                st.markdown(f"""
                <div class="metric-card">
                    <h4>💼 LinkedIn Connected</h4>
                    <p style="font-size: 24px; margin: 0;">{linkedin_brands}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Brand cards
            for brand in st.session_state.brands:
                brand_initials = ''.join([word[0].upper() for word in brand['name'].split()[:2]])
                
                st.markdown(f"""
                <div class="brand-card">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div class="profile-pic" style="margin-right: 15px;">{brand_initials}</div>
                        <div>
                            <h3 style="margin: 0; color: #ffffff;">{brand['name']}</h3>
                            <p style="margin: 5px 0; color: #cccccc; font-size: 14px;">{brand.get('brand_voice', '')[:100]}...</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"✏️ Edit {brand['name']}", expanded=False):
                    # Create edit form for each brand
                    with st.form(f"edit_brand_form_{brand['id']}"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("##### 📝 Basic Information")
                            edit_name = st.text_input("🏷️ Brand Name", value=brand['name'], key=f"edit_name_{brand['id']}")
                            edit_website = st.text_input("🌐 Website", value=brand['website'] or '', key=f"edit_website_{brand['id']}")
                            edit_linkedin_url = st.text_input("💼 LinkedIn URL", value=brand.get('linkedin_url', '') or '', key=f"edit_linkedin_url_{brand['id']}")
                            
                            st.markdown("##### 🎭 Brand Voice & Personality")
                            edit_voice = st.text_area("Brand Voice", value=brand['brand_voice'] or '', key=f"edit_voice_{brand['id']}", height=80)
                            edit_portrayal = st.text_area("Brand Portrayal", value=brand['portrayal'] or '', key=f"edit_portrayal_{brand['id']}", height=80)
                            edit_overall_voice = st.text_area("Overall Tone", value=brand['overall_voice'] or '', key=f"edit_overall_voice_{brand['id']}", height=80)
                        
                        with col2:
                            st.markdown("##### 📚 Content Guidelines")
                            edit_brand_phrases = st.text_area("Key Phrases", value=brand['brand_phrases'] or '', 
                                                            key=f"edit_brand_phrases_{brand['id']}", height=60,
                                                            help="Signature phrases or taglines")
                            edit_previous_posts = st.text_area("Example Posts", value=brand['previous_posts'] or '', 
                                                             key=f"edit_previous_posts_{brand['id']}", height=100,
                                                             help="Examples of previous social media posts")
                            edit_additional_info = st.text_area("Additional Notes", value=brand['additional_info'] or '', 
                                                              key=f"edit_additional_info_{brand['id']}", height=60)
                        
                        # Form buttons
                        update_submitted = st.form_submit_button("💾 Update Brand", type="primary", use_container_width=True)
                        
                        if update_submitted:
                            if edit_name and edit_voice and edit_portrayal and edit_overall_voice:
                                updated_brand_data = {
                                    "name": edit_name,
                                    "brand_voice": edit_voice,
                                    "portrayal": edit_portrayal,
                                    "overall_voice": edit_overall_voice,
                                    "previous_posts": edit_previous_posts,
                                    "brand_phrases": edit_brand_phrases,
                                    "website": edit_website,
                                    "linkedin_url": edit_linkedin_url,
                                    "additional_info": edit_additional_info
                                }
                                
                                updated_brand = st.session_state.supabase_client.update_brand(brand['id'], updated_brand_data)
                                if updated_brand:
                                    st.success(f"✅ Brand '{edit_name}' updated successfully!")
                                    current_user_id = st.session_state.get('user_id')
                                    st.session_state.brands = st.session_state.supabase_client.get_brands(current_user_id)
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to update brand. Please try again.")
                            else:
                                st.error("⚠️ Please fill in all required fields (Name, Brand Voice, Portrayal, Overall Voice)")
                    
                    # Delete button outside the form
                    if st.button("🗑️ Delete Brand", key=f"delete_button_{brand['id']}", type="secondary"):
                        st.session_state[f"confirm_delete_{brand['id']}"] = True
                        st.rerun()
                
                # Delete confirmation dialog
                if st.session_state.get(f"confirm_delete_{brand['id']}", False):
                    st.warning(f"⚠️ Are you sure you want to delete '{brand['name']}'? This action cannot be undone.")
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button(f"✅ Yes, Delete {brand['name']}", key=f"confirm_delete_yes_{brand['id']}"):
                            current_user_id = st.session_state.get('user_id')
                            if st.session_state.supabase_client.delete_brand(brand['id'], current_user_id):
                                st.success("✅ Brand deleted successfully!")
                                st.session_state.brands = st.session_state.supabase_client.get_brands(current_user_id)
                                st.session_state[f"confirm_delete_{brand['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete brand.")
                    with col_cancel:
                        if st.button("❌ Cancel", key=f"confirm_delete_no_{brand['id']}"):
                            st.session_state[f"confirm_delete_{brand['id']}"] = False
                            st.rerun()
                
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; border: 2px solid #667eea; color: white;">
                <h3>🏢 No Brands Yet</h3>
                <p>Create your first brand profile to start generating personalized content!</p>
                <p style="font-size: 14px; color: #cccccc;">Brands help the AI understand your voice, tone, and messaging preferences.</p>
            </div>
            """, unsafe_allow_html=True)

with tab1:
    st.markdown("### 🚀 Social Media Calendar Generator")
    st.markdown("Generate a complete month's worth of engaging LinkedIn posts tailored to your brand.")
    
    if not st.session_state.supabase_client or not st.session_state.brands:
        st.markdown("""
        <div class="error-card">
            <h4>⚠️ Setup Required</h4>
            <p>Please check your Supabase connection and create at least one brand in the Brand Management tab.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Configuration Section
        st.markdown("#### 📋 Configuration")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Brand selection dropdown
                brand_options = {brand['name']: brand['id'] for brand in st.session_state.brands}
                
                if not brand_options:
                    st.warning("⚠️ No brands found. Please create a brand first in the Brand Management tab.")
                    st.stop()
                
                selected_brand_name = st.selectbox("🏢 Select Brand", options=list(brand_options.keys()))
                selected_brand_id = brand_options[selected_brand_name] if selected_brand_name else None
                current_user_id = st.session_state.get('user_id')
                selected_brand_data = st.session_state.supabase_client.get_brand_by_id(selected_brand_id, current_user_id) if selected_brand_id else None
                
                focus_options = [
                    "🎉 Grand Opening", "🏢 Franchise Focused", "📈 SEO", "📱 Keep Profile Active", 
                    "🚀 Product Launch", "🎯 Promotional", "🌟 Brand Awareness", "👥 Customer Engagement", 
                    "🎨 Other"
                ]
                focus = st.selectbox("🎯 Primary Focus", options=focus_options)
                if "Other" in focus:
                    focus = st.text_input("✏️ Specify custom focus", "")
            
            with col2:
                num_posts = st.slider("📊 Posts per month", min_value=4, max_value=30, value=8, step=2)
                
                # Show estimated posting schedule
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; margin: 10px 0; color: white; border: 2px solid #667eea;">
                    <small><strong>Estimated Schedule:</strong><br>
                    📅 {num_posts} posts = ~{num_posts//4} posts per week<br>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                special_events = st.text_area("🎊 Special Events", 
                    placeholder="e.g., National Hot Dog Day (July 21), Franchise Convention", 
                    height=80)
                
                if not st.session_state.api_key:
                    api_key = st.text_input("🔑 OpenAI API Key", type="password", 
                        help="Your API key is required to generate content")
                else:
                    api_key = st.session_state.api_key
                    st.markdown("✅ API Key loaded from previous session")
        
        # Generation Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate Social Media Calendar", type="primary", use_container_width=True):
                if not api_key:
                    st.error("🔑 Please enter your OpenAI API key")
                elif not selected_brand_data:
                    st.error("🏢 Please select a brand")
                else:
                    st.session_state.api_key = api_key
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    with st.spinner("🎨 Generating personalized posts..."):
                        status_text.text("🧠 Analyzing brand voice...")
                        progress_bar.progress(25)
                        
                        status_text.text("✍️ Creating engaging content...")
                        progress_bar.progress(50)
                        
                        st.session_state.generated_posts = generate_social_posts(
                            selected_brand_data, focus, num_posts, 
                            special_events, api_key
                        )
                        progress_bar.progress(75)
                        
                        status_text.text("🎯 Optimizing for engagement...")
                        st.session_state.selected_posts = st.session_state.generated_posts.copy()
                        progress_bar.progress(100)
                        
                        status_text.text("✅ Posts generated successfully!")
                        
                    st.markdown("""
                    <div class="success-card">
                        <h4>🎉 Success!</h4>
                        <p>Generated {} high-quality LinkedIn posts for {}!</p>
                    </div>
                    """.format(len(st.session_state.generated_posts), selected_brand_name), 
                    unsafe_allow_html=True)
        
        # Display generated posts with enhanced UI
        if st.session_state.generated_posts and selected_brand_name:
            st.markdown("---")
            st.markdown("### 📱 Generated LinkedIn Posts")
            
            # Display mode toggle
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown("Review and customize your posts. Use **Edit Mode** to modify content and apply AI refinements.")
            with col2:
                view_mode = st.selectbox("👁️ View Mode", ["Social Cards", "Edit Mode"], key="calendar_view_mode")
            with col3:
                show_all_selected = st.checkbox("✅ Select All", key="select_all_calendar")
                
            if show_all_selected:
                for i in range(len(st.session_state.generated_posts)):
                    st.session_state.generated_posts[i]['selected'] = True
            
            # Display posts based on view mode
            if view_mode == "Social Cards":
                # Modern card view
                for i, post in enumerate(st.session_state.generated_posts):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display the social post card
                        card_html = create_social_post_card(post, selected_brand_name, i)
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Show graphic concept below the card
                        if post.get('graphic'):
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 15px; border-radius: 8px; margin-top: 10px; border: 2px solid #667eea; color: white;">
                                <strong>🎨 Graphic Concept:</strong><br>
                                <em>{post['graphic']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("#### Post Controls")
                        
                        # Selection checkbox
                        selected = st.checkbox(
                            f"Include Post #{post['number']}", 
                            value=post.get('selected', False), 
                            key=f"card_select_{i}"
                        )
                        st.session_state.generated_posts[i]['selected'] = selected
                        
                        # Post stats
                        st.markdown(f"""
                        <div style="font-size: 12px; color: #666; margin-top: 15px;">
                            📊 <strong>Post Stats:</strong><br>
                            • {len(post.get('content', ''))} characters<br>
                            • {len([w for w in post.get('content', '').split() if w.startswith('#')])} hashtags<br>
                            • {len([w for w in post.get('content', '').split() if w.startswith('@')])} mentions
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
            
            else:
                # Traditional edit mode
                for i, post in enumerate(st.session_state.generated_posts):
                    with st.expander(f"📝 Post #{post['number']} - {post.get('date', 'No Date')}", expanded=True):
                        col1, col2, col3, col4 = st.columns([0.1, 0.5, 0.25, 0.15])
                        
                        with col1:
                            selected = st.checkbox("✅", value=post.get('selected', False), key=f"edit_select_{i}")
                            st.session_state.generated_posts[i]['selected'] = selected
                        
                        with col2:
                            post['content'] = st.text_area("Post Content", post['content'], height=150, key=f"edit_post_{i}")
                            post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"edit_graphic_concept_{i}")
                        
                        with col3:
                            st.markdown("**🤖 AI Refinement**")
                            feedback = st.text_area("Refine as...", placeholder="more casual, professional", key=f"edit_feedback_trad_{i}", height=70)
                            refine_post = st.checkbox("Refine Post", key=f"edit_refine_post_trad_{i}")
                            refine_graphic = st.checkbox("Refine Graphic", key=f"edit_refine_graphic_trad_{i}")
                        
                        with col4:
                            if feedback and (refine_post or refine_graphic):
                                if st.button("🚀 Apply", key=f"edit_apply_{i}"):
                                    with st.spinner("Refining..."):
                                        refined_result = refine_content(
                                            post, feedback, st.session_state.api_key, 
                                            refine_post=refine_post, refine_graphic=refine_graphic
                                        )
                                        st.session_state.generated_posts[i] = refined_result
                                        st.rerun()
            
            # Enhanced Export Section
            st.markdown("---")
            st.markdown("### 📤 Export Options")
            
            selected_posts_count = sum(1 for post in st.session_state.generated_posts if post.get('selected', False))
            
            if selected_posts_count > 0:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4>📊 Ready to Export</h4>
                        <p style="font-size: 24px; margin: 0;">{selected_posts_count} posts</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("💾 Save to Database", type="primary", use_container_width=True):
                        selected_posts = [post for post in st.session_state.generated_posts if post.get('selected', False)]
                        saved_count = 0
                        
                        for post in selected_posts:
                            result = st.session_state.supabase_client.save_posts(
                                brand_id=selected_brand_id,
                                post=post['content'],
                                user_id=st.session_state.get('user_id'),
                                graphic_concept=post['graphic'],
                                type="LinkedIn Calendar Posts",
                                date=post['date']
                            )
                            if result:
                                saved_count += 1
                        
                        st.success(f"✅ Saved {saved_count} posts to database!")
                
                with col3:
                    export_format = st.selectbox("📄 Export Format", ["Enhanced CSV", "Basic CSV", "JSON"])
                
                # Export buttons
                selected_posts = [post for post in st.session_state.generated_posts if post.get('selected', False)]
                
                if export_format == "Enhanced CSV":
                    enhanced_df = create_enhanced_export_data(selected_posts, selected_brand_name)
                    csv_data = enhanced_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📊 Download Enhanced CSV Report",
                        data=csv_data,
                        file_name=f"{selected_brand_name}_social_calendar_enhanced_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                elif export_format == "Basic CSV":
                    basic_data = []
                    for post in selected_posts:
                        basic_data.append({
                            "Date": post.get('date', ''),
                            "Content": post.get('content', ''),
                            "Graphic Concept": post.get('graphic', '')
                        })
                    
                    basic_df = pd.DataFrame(basic_data)
                    csv_data = basic_df.to_csv(index=False)
                    
                    st.download_button(
                        label="📄 Download Basic CSV",
                        data=csv_data,
                        file_name=f"{selected_brand_name}_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                elif export_format == "JSON":
                    json_data = json.dumps(selected_posts, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label="📋 Download JSON",
                        data=json_data,
                        file_name=f"{selected_brand_name}_posts_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # Preview export data
                if st.checkbox("👀 Preview Export Data"):
                    if export_format == "Enhanced CSV":
                        st.markdown("#### 📊 Enhanced Export Preview")
                        st.dataframe(enhanced_df, use_container_width=True)
                    else:
                        st.markdown("#### 📄 Export Preview")
                        st.dataframe(pd.DataFrame(basic_data), use_container_width=True)
            
            else:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); border: 2px solid #f39c12; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                    <h4>📋 No Posts Selected</h4>
                    <p>Select at least one post to enable export options.</p>
                </div>
                """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 📄 Article to LinkedIn Posts")
    st.markdown("Transform any article or webpage into engaging LinkedIn posts that match your brand voice.")
    
    # Input options section with enhanced visibility
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 20px; border-radius: 12px; border: 2px solid #667eea; margin: 20px 0;">
        <h4 style="color: #ffffff; margin: 0 0 10px 0;">📝 Content Input</h4>
        <p style="color: #cccccc; margin: 0;">Provide either article text, a website URL, or both:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        article_text = st.text_area("Article Text", height=300, 
                                   placeholder="Paste the full text of your article here...")
    
    with col_input2:
        website_url = st.text_input("Website URL", 
                                   placeholder="https://example.com/article",
                                   help="Our system can scrape content from most websites")
        
        # Optional: Show URL validation
        if website_url and not website_url.startswith(('http://', 'https://')):
            st.warning("⚠️ URL should start with http:// or https://")

    # Configuration section with enhanced visibility
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 20px; border-radius: 12px; border: 2px solid #667eea; margin: 20px 0;">
        <h4 style="color: #ffffff; margin: 0 0 10px 0;">⚙️ Generation Settings</h4>
        <p style="color: #cccccc; margin: 0;">Configure your post generation preferences:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.supabase_client and st.session_state.brands:
            # Brand selection dropdown
            brand_options = {brand['name']: brand['id'] for brand in st.session_state.brands}
            selected_article_brand_name = st.selectbox("Select Brand", options=list(brand_options.keys()), key="article_brand_select")
            selected_article_brand_id = brand_options[selected_article_brand_name] if selected_article_brand_name else None
            selected_article_brand_data = st.session_state.supabase_client.get_brand_by_id(selected_article_brand_id) if selected_article_brand_id else None
        else:
            st.warning("Create brands in Brand Management tab to use brand-specific styling")
            selected_article_brand_data = None
    
    with col2:
        num_posts = st.number_input("Number of posts to generate", min_value=1, max_value=10, value=3)
    
    with col3:
        if not st.session_state.api_key:
            api_key = st.text_input("OpenAI API Key", type="password", 
                                   help="Your API key is required to generate content",
                                   key="article_tab_api_key")
        else:
            api_key = st.session_state.api_key
            st.info("Using API key from previous tab")
    
    # Generate button with validation
    if st.button("Generate Posts from Article", type="primary"):
        # Validation logic
        if not api_key:
            st.error("Please enter your OpenAI API key")
        elif not article_text and not website_url:
            st.error("Please provide either article text or a website URL")
        elif website_url and not website_url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            st.session_state.api_key = api_key
            
            # Determine what content to use
            content_source = ""
            if article_text and website_url:
                content_source = "both article text and website URL"
            elif article_text:
                content_source = "article text"
            elif website_url:
                content_source = "website URL"
            
            with st.spinner(f"Generating posts from {content_source}..."):
                # Use brand data if selected, otherwise use generic brand data
                brand_data_to_use = selected_article_brand_data if selected_article_brand_data else {
                    'name': 'Generic Brand',
                    'brand_voice': 'Professional and engaging',
                    'overall_voice': 'Informative and approachable',
                    'brand_phrases': ''
                }
                
                # Pass both article_text and website_url to the function
                # The OpenAI function can handle the logic of which to use
                st.session_state.article_posts = article_to_posts(  
                    article_text=article_text if article_text else None,
                    website_url=website_url if website_url else None, 
                    num_posts=num_posts, 
                    brand_data=brand_data_to_use, 
                    api_key=api_key
                )
                
                if st.session_state.article_posts:
                    st.success(f"Successfully generated {len(st.session_state.article_posts)} posts!")
                else:
                    st.error("Failed to generate posts. Please check your inputs and try again.")
    
    # Display article-based posts with enhanced styling
    if 'article_posts' in st.session_state and st.session_state.article_posts:
        st.markdown("---")
        st.markdown("### 📱 Generated LinkedIn Posts from Article")
        
        # Display mode toggle
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown("Review and customize your article-based posts. Use **Edit Mode** to modify content and apply AI refinements.")
        with col2:
            view_mode = st.selectbox("👁️ View Mode", ["Social Cards", "Edit Mode"], key="article_view_mode")
        with col3:
            show_all_selected = st.checkbox("✅ Select All", key="select_all_article")
            
        if show_all_selected:
            for i in range(len(st.session_state.article_posts)):
                st.session_state.article_posts[i]['selected'] = True
        
        # Use the same enhanced display as the main tab
        if view_mode == "Social Cards":
            # Modern card view
            for i, post in enumerate(st.session_state.article_posts):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Display the social post card
                    brand_name = selected_article_brand_data['name'] if selected_article_brand_data else "Generic Brand"
                    card_html = create_social_post_card(post, brand_name, i)
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Show graphic concept below the card
                    if post.get('graphic'):
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 15px; border-radius: 8px; margin-top: 10px; border: 2px solid #667eea; color: white;">
                            <strong>🎨 Graphic Concept:</strong><br>
                            <em>{post['graphic']}</em>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("#### Post Controls")
                    
                    # Selection checkbox
                    selected = st.checkbox(
                        f"Include Post #{post['number']}", 
                        value=post.get('selected', False), 
                        key=f"article_card_select_{i}"
                    )
                    st.session_state.article_posts[i]['selected'] = selected
                    
                    # Post stats
                    st.markdown(f"""
                    <div style="font-size: 12px; color: #cccccc; margin-top: 15px;">
                        📊 <strong>Post Stats:</strong><br>
                        • {len(post.get('content', ''))} characters<br>
                        • {len([w for w in post.get('content', '').split() if w.startswith('#')])} hashtags<br>
                        • {len([w for w in post.get('content', '').split() if w.startswith('@')])} mentions
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
        
        else:
            # Traditional edit mode
            for i, post in enumerate(st.session_state.article_posts):
                with st.expander(f"📝 Article Post #{post['number']}", expanded=True):
                    col1, col2, col3, col4 = st.columns([0.1, 0.5, 0.25, 0.15])
                    
                    with col1:
                        selected = st.checkbox("✅", value=post.get('selected', False), key=f"article_edit_select_{i}")
                        st.session_state.article_posts[i]['selected'] = selected
                    
                    with col2:
                        post['content'] = st.text_area("Post Content", post['content'], height=150, key=f"article_edit_post_{i}")
                        post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"article_edit_graphic_concept_{i}")
                    
                    with col3:
                        st.markdown("**🤖 AI Refinement**")
                        feedback = st.text_area("Refine as...", placeholder="more casual, professional", key=f"article_edit_feedback_trad_{i}", height=70)
                        refine_post = st.checkbox("Refine Post", key=f"article_edit_refine_post_trad_{i}")
                        refine_graphic = st.checkbox("Refine Graphic", key=f"article_edit_refine_graphic_trad_{i}")
                    
                    with col4:
                        if feedback and (refine_post or refine_graphic):
                            if st.button("🚀 Apply", key=f"article_edit_apply_{i}"):
                                with st.spinner("Refining..."):
                                    refined_result = refine_content(
                                        post, feedback, st.session_state.api_key, 
                                        refine_post=refine_post, refine_graphic=refine_graphic
                                    )
                                    st.session_state.article_posts[i] = refined_result
                                    st.rerun()
            
            with col3:
                st.markdown("**Refinement Options**")
                # Single feedback textbox
                article_feedback = st.text_area("Refine as...", placeholder="e.g., more casual, professional, engaging", key=f"article_feedback_{i}", height=70)
                
                # Checkboxes for what to refine
                article_refine_post = st.checkbox("Refine Post Text", key=f"article_refine_post_check_{i}")
                article_refine_graphic = st.checkbox("Refine Graphic", key=f"article_refine_graphic_check_{i}")
                
                # Store the feedback and checkbox states in the post object
                st.session_state.article_posts[i]['feedback'] = article_feedback
                st.session_state.article_posts[i]['refine_post'] = article_refine_post
                st.session_state.article_posts[i]['refine_graphic'] = article_refine_graphic
            
            with col4:
                st.markdown("**Actions**")
                st.write("") # Empty space for alignment
                st.write("") # Empty space for alignment
                
                if article_feedback and (article_refine_post or article_refine_graphic):
                    if st.button("Apply Refinement", key=f"article_refine_{i}"):
                        with st.spinner("Refining content..."):
                            refined_result = refine_content(
                                post, article_feedback, st.session_state.api_key, 
                                refine_post=article_refine_post, refine_graphic=article_refine_graphic
                            )
                            st.session_state.article_posts[i] = refined_result
                            st.rerun()
                else:
                    if not article_feedback:
                        st.info("Enter feedback to refine")
                    elif not (article_refine_post or article_refine_graphic):
                        st.info("Select what to refine")
            
            st.divider()
        
        # Enhanced Export Section for Article Posts
        st.markdown("---")
        st.markdown("### 📤 Export Article Posts")
        
        selected_posts_count = sum(1 for post in st.session_state.article_posts if post.get('selected', False))
        
        if selected_posts_count > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📊 Ready to Export</h4>
                    <p style="font-size: 24px; margin: 0;">{selected_posts_count} posts</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("💾 Save to Database", type="primary", use_container_width=True, key="save_article_posts"):
                    selected_posts = [post for post in st.session_state.article_posts if post.get('selected', False)]
                    saved_count = 0
                    
                    for post in selected_posts:
                        result = st.session_state.supabase_client.save_posts(
                            brand_id=selected_article_brand_id,
                            post=post['content'],
                            user_id=st.session_state.get('user_id'),
                            graphic_concept=post['graphic'],
                            type="LinkedIn Article Posts",
                            date=datetime.now().strftime('%Y-%m-%d')
                        )
                        if result:
                            saved_count += 1
                    
                    st.success(f"✅ Saved {saved_count} article posts to database!")
            
            with col3:
                export_format = st.selectbox("📄 Export Format", ["Enhanced CSV", "Basic CSV", "JSON"], key="article_export_format")
            
            # Export buttons
            selected_posts = [post for post in st.session_state.article_posts if post.get('selected', False)]
            
            if export_format == "Enhanced CSV":
                brand_name = selected_article_brand_data['name'] if selected_article_brand_data else "Generic Brand"
                enhanced_df = create_enhanced_export_data(selected_posts, brand_name)
                csv_data = enhanced_df.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download Enhanced CSV Report",
                    data=csv_data,
                    file_name=f"article_posts_enhanced_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_article_enhanced"
                )
            
            elif export_format == "Basic CSV":
                basic_data = []
                for post in selected_posts:
                    basic_data.append({
                        "Content": post.get('content', ''),
                        "Graphic Concept": post.get('graphic', '')
                    })
                
                basic_df = pd.DataFrame(basic_data)
                csv_data = basic_df.to_csv(index=False)
                
                st.download_button(
                    label="📄 Download Basic CSV",
                    data=csv_data,
                    file_name=f"article_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="download_article_basic"
                )
            
            elif export_format == "JSON":
                json_data = json.dumps(selected_posts, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="📋 Download JSON",
                    data=json_data,
                    file_name=f"article_posts_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_article_json"
                )
            
            # Preview export data
            if st.checkbox("👀 Preview Export Data", key="preview_article_export"):
                if export_format == "Enhanced CSV":
                    st.markdown("#### 📊 Enhanced Export Preview")
                    brand_name = selected_article_brand_data['name'] if selected_article_brand_data else "Generic Brand"
                    enhanced_df = create_enhanced_export_data(selected_posts, brand_name)
                    st.dataframe(enhanced_df, use_container_width=True)
                else:
                    st.markdown("#### 📄 Export Preview")
                    basic_data = []
                    for post in selected_posts:
                        basic_data.append({
                            "Content": post.get('content', ''),
                            "Graphic Concept": post.get('graphic', '')
                        })
                    st.dataframe(pd.DataFrame(basic_data), use_container_width=True)
        
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); border: 2px solid #f39c12; padding: 15px; border-radius: 8px; text-align: center; color: white;">
                <h4>📋 No Posts Selected</h4>
                <p>Select at least one post to enable export options.</p>
            </div>
            """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 📚 Saved Posts Library")
    st.markdown("Browse, search, and manage all your previously generated and saved social media content.")
    
    if not st.session_state.supabase_client or not st.session_state.brands:
        st.markdown("""
        <div class="error-card">
            <h4>⚠️ Setup Required</h4>
            <p>Please check your Supabase connection and create at least one brand in the Brand Management tab.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Brand and filter selection
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            brand_options = {brand['name']: brand['id'] for brand in st.session_state.brands}
            selected_prev_brand_name = st.selectbox("🏢 Select Brand", options=list(brand_options.keys()), key="prev_brand_select")
            selected_prev_brand_id = brand_options[selected_prev_brand_name] if selected_prev_brand_name else None
        
        with col2:
            post_type_filter = st.selectbox("📄 Filter by Type", options=["All Types", "LinkedIn Posts", "LinkedIn Calendar Posts", "LinkedIn Article Posts"])
        
        with col3:
            search_term = st.text_input("🔍 Search Posts", placeholder="Enter keywords...")
        
        # Load posts button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📚 Load Saved Posts", type="primary", use_container_width=True):
                if selected_prev_brand_id:
                    with st.spinner("🔄 Loading saved posts..."):
                        current_user_id = st.session_state.get('user_id')
                        posts = st.session_state.supabase_client.get_posts_by_brand(selected_prev_brand_id, current_user_id)
                        
                        if posts:
                            # Apply filters
                            filtered_posts = posts
                            
                            if post_type_filter != "All Types":
                                filtered_posts = [p for p in filtered_posts if p.get('type', '') == post_type_filter]
                            
                            if search_term:
                                filtered_posts = [p for p in filtered_posts if search_term.lower() in p.get('post', '').lower()]
                            
                            st.session_state.loaded_posts = filtered_posts
                            st.session_state.current_brand_name = selected_prev_brand_name
                        else:
                            st.session_state.loaded_posts = []
                else:
                    st.warning("⚠️ Please select a brand.")
        
        # Display loaded posts
        if 'loaded_posts' in st.session_state and st.session_state.loaded_posts:
            posts = st.session_state.loaded_posts
            brand_name = st.session_state.current_brand_name
            
            # Posts summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📊 Total Posts</h4>
                    <p style="font-size: 24px; margin: 0;">{len(posts)}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_length = sum(len(p.get('post', '')) for p in posts) // len(posts) if posts else 0
                st.markdown(f"""
                <div class="metric-card">
                    <h4>📝 Avg Length</h4>
                    <p style="font-size: 24px; margin: 0;">{avg_length} chars</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                recent_posts = len([p for p in posts if 'Today' in p.get('date', '') or 'yesterday' in p.get('date', '').lower()])
                st.markdown(f"""
                <div class="metric-card">
                    <h4>🕒 Recent Posts</h4>
                    <p style="font-size: 24px; margin: 0;">{recent_posts}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown(f"### 📱 Posts for {brand_name}")
            
            # Display mode selection
            display_mode = st.selectbox("👁️ Display Mode", ["Social Cards", "List View"], key="saved_posts_display")
            
            if display_mode == "Social Cards":
                # Display as social media cards
                for i, post in enumerate(posts):
                    # Create a mock post object for the card function
                    mock_post = {
                        'content': post.get('post', ''),
                        'date': post.get('date', 'Unknown Date'),
                        'graphic': post.get('graphic_concept', '')
                    }
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display social post card
                        card_html = create_social_post_card(mock_post, brand_name, i)
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Show graphic concept if available
                        if post.get('graphic_concept'):
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 15px; border-radius: 8px; margin-top: 10px; border: 2px solid #667eea; color: white;">
                                <strong>🎨 Graphic Concept:</strong><br>
                                <em>{post['graphic_concept']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("#### Post Info")
                        st.markdown(f"**📅 Date:** {post.get('date', 'N/A')}")
                        st.markdown(f"**📄 Type:** {post.get('type', 'N/A')}")
                        st.markdown(f"**👤 User ID:** `{post.get('user_id', 'N/A')}`")
                        
                        # Character count and analysis
                        content_length = len(post.get('post', ''))
                        hashtag_count = len([word for word in post.get('post', '').split() if word.startswith('#')])
                        mention_count = len([word for word in post.get('post', '').split() if word.startswith('@')])
                        
                        st.markdown(f"""
                        <div style="font-size: 12px; color: #cccccc; margin-top: 15px; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 10px; border-radius: 6px; border: 1px solid #667eea;">
                            📊 <strong style="color: #ffffff;">Analysis:</strong><br>
                            • {content_length} characters<br>
                            • {hashtag_count} hashtags<br>
                            • {mention_count} mentions
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Quick actions
                        if st.button("📋 Copy Content", key=f"copy_{i}"):
                            st.code(post.get('post', ''), language=None)
                    
                    st.markdown("---")
            
            else:
                # Traditional list view
                for i, post in enumerate(posts):
                    with st.expander(f"📅 {post.get('date', 'No Date')} | {post.get('type', 'No Type')}", expanded=False):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown("**📝 Post Content:**")
                            # Use a styled container instead of code block for better visibility
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%); padding: 15px; border-radius: 8px; border: 2px solid #667eea; color: white; font-family: monospace; white-space: pre-wrap; margin: 10px 0;">
{post.get('post', '')}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if post.get('graphic_concept'):
                                st.markdown("**🎨 Graphic Concept:**")
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%); padding: 10px; border-radius: 6px; border: 1px solid #667eea; color: #cccccc; font-style: italic; margin: 10px 0;">
                                    {post.get('graphic_concept', '')}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("**📊 Post Details:**")
                            st.markdown(f"**Type:** {post.get('type', 'N/A')}")
                            st.markdown(f"**Date:** {post.get('date', 'N/A')}")
                            st.markdown(f"**User ID:** `{post.get('user_id', 'N/A')}`")
                            
                            # Performance metrics (placeholder)
                            st.markdown(f"""
                            **📈 Estimated Performance:**
                            - Characters: {len(post.get('post', ''))}
                            - Hashtags: {len([w for w in post.get('post', '').split() if w.startswith('#')])}
                            - Mentions: {len([w for w in post.get('post', '').split() if w.startswith('@')])}
                            """)
            
            # Bulk export options
            st.markdown("---")
            st.markdown("### 📤 Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export all as CSV
                export_data = []
                for post in posts:
                    export_data.append({
                        "Date": post.get('date', ''),
                        "Type": post.get('type', ''),
                        "Content": post.get('post', ''),
                        "Graphic Concept": post.get('graphic_concept', ''),
                        "Character Count": len(post.get('post', '')),
                        "Hashtag Count": len([w for w in post.get('post', '').split() if w.startswith('#')]),
                        "Mention Count": len([w for w in post.get('post', '').split() if w.startswith('@')])
                    })
                
                df = pd.DataFrame(export_data)
                csv_data = df.to_csv(index=False)
                
                st.download_button(
                    "📊 Download as CSV",
                    data=csv_data,
                    file_name=f"{brand_name}_saved_posts_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Export as JSON
                json_data = json.dumps(posts, indent=2, ensure_ascii=False, default=str)
                st.download_button(
                    "📋 Download as JSON",
                    data=json_data,
                    file_name=f"{brand_name}_saved_posts_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col3:
                # Analytics summary
                if st.button("📊 Generate Report", use_container_width=True):
                    st.info("📈 Analytics report feature coming soon!")
        
        elif 'loaded_posts' in st.session_state and not st.session_state.loaded_posts:
            st.markdown("""
            <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); border-radius: 12px; border: 2px solid #f39c12; color: white;">
                <h3>📭 No Posts Found</h3>
                <p>No saved posts found for the selected filters.</p>
                <p style="font-size: 14px; color: #cccccc;">Try adjusting your search criteria or create some posts first!</p>
            </div>
            """, unsafe_allow_html=True)

# Analytics Dashboard removed - will be added later with real data

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 5px; color: white; margin-top: 2rem;">
    <p>Powered by The Glenwood Group</p>
</div>
""", unsafe_allow_html=True)