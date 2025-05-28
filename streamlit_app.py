import streamlit as st
import openai
import pandas as pd
from datetime import datetime
import calendar
import re

st.set_page_config(page_title="Social Media Content Generator", layout="wide")

# Initialize session state variables if they don't exist
if 'generated_posts' not in st.session_state:
    st.session_state.generated_posts = []
if 'selected_posts' not in st.session_state:
    st.session_state.selected_posts = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""


def generate_social_posts(brand, brand_voice, portrayal, focus, posts_per_month, 
                         special_events, overall_voice, last_month_examples, api_key, brand_phrases):
    """Generate social media posts using OpenAI."""
    try:
        openai.api_key = api_key
        
        # Get current month name and year
        now = datetime.now()
        current_month = calendar.month_name[now.month]
        current_year = now.year
        
        # Calculate weekdays in current month to properly distribute posts
        _, num_days = calendar.monthrange(now.year, now.month)
        weekdays = [datetime(now.year, now.month, day).weekday() < 5 for day in range(1, num_days + 1)]
        weekdays_count = sum(weekdays)
        
        # Determine how many posts to generate
        # Double the requested number as specified in requirements
        num_posts = posts_per_month * 2
        
        # Create a tailored prompt
        system_prompt = f"""You are an expert social media copywriter specializing in creating engaging content.
        Generate {num_posts} unique LinkedIn posts for {brand} for {current_month} {current_year}.
        
        Brand voice: {brand_voice}
        How they portray themselves: {portrayal}
        Primary focus: {focus}
        Special events to highlight: {special_events}
        Overall tone/voice: {overall_voice}
        Brand phrases to include when appropriate: {brand_phrases}
        
        Only schedule posts on weekdays. Create posts that are different from these examples:
        {last_month_examples}
        
        For each post, also suggest a graphic concept that would complement the post.

        Format each post as:
        
        POST #X - [Date]:
        [LinkedIn post copy]
        
        GRAPHIC:
        [Brief description of graphic concept]
        """
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate {num_posts} LinkedIn posts for {brand} focusing on {focus}."}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Parse the generated posts
        posts = []
        pattern = r'POST #(\d+) - (.*?):\n(.*?)(?:\n\nGRAPHIC:\n(.*?))?(?=\n\nPOST #|\Z)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            post_num = match.group(1)
            post_date = match.group(2)
            post_content = match.group(3).strip()
            graphic_desc = match.group(4).strip() if match.group(4) else "No graphic suggestion provided."
            
            posts.append({
                "number": post_num,
                "date": post_date,
                "content": post_content,
                "graphic": graphic_desc,
                "selected": True,
                "feedback": ""
            })
        
        return posts
    except Exception as e:
        st.error(f"Error generating posts: {str(e)}")
        return []

def refine_post(post, feedback, api_key):
    """Refine a single post based on feedback."""
    try:
        openai.api_key = api_key
        
        system_prompt = """You are an expert social media copywriter. 
        Revise the provided LinkedIn post according to the feedback.
        Maintain the same general message but adjust the tone, style, or focus based on the feedback.
        Return only the revised post and graphic suggestion without any additional explanations."""
        
        user_prompt = f"""Original post:
        {post['content']}
        
        Original graphic concept:
        {post['graphic']}
        
        Feedback: Make this more {feedback}
        
        Provide the revised post followed by the revised graphic concept, separated by two line breaks."""
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response
        revised_text = response.choices[0].message.content
        parts = revised_text.split("\n\n", 1)
        
        if len(parts) >= 2:
            revised_post = parts[0].strip()
            revised_graphic = parts[1].strip()
        else:
            revised_post = revised_text
            revised_graphic = post['graphic']
        
        return {
            "number": post['number'],
            "date": post['date'],
            "content": revised_post,
            "graphic": revised_graphic,
            "selected": post['selected'],
            "feedback": ""
        }
        
    except Exception as e:
        st.error(f"Error refining post: {str(e)}")
        return post

def article_to_posts(article_text, num_posts, api_key):
    """Generate LinkedIn posts based on an article."""
    try:
        openai.api_key = api_key
        
        system_prompt = f"""You are an expert content marketer specializing in LinkedIn.
        Based on the article provided, create {num_posts} LinkedIn posts that highlight key insights or quotes from the article.
        Each post should be standalone, engaging, and encourage readers to read the full article.
        Vary the style and approach of each post to appeal to different audience segments. 
        
        Format each post as:
        
        POST #X:
        [LinkedIn post copy]
        
        GRAPHIC:
        [Brief description of graphic concept that would complement this post]
        """
        
        # Truncate article if too long to fit in context
        max_article_length = 6000
        if len(article_text) > max_article_length:
            article_text = article_text[:max_article_length] + "... [article truncated]"
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here's the article to use for creating LinkedIn posts:\n\n{article_text}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Parse the generated posts
        posts = []
        pattern = r'POST #(\d+):\n(.*?)(?:\n\nGRAPHIC:\n(.*?))?(?=\n\nPOST #|\Z)'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            post_num = match.group(1)
            post_content = match.group(2).strip()
            graphic_desc = match.group(3).strip() if match.group(3) else "No graphic suggestion provided."
            
            posts.append({
                "number": post_num,
                "date": "",  # No date required for article-based posts
                "content": post_content,
                "graphic": graphic_desc,
                "selected": True,
                "feedback": ""
            })
        
        return posts
    except Exception as e:
        st.error(f"Error generating posts from article: {str(e)}")
        return []

# Main app interface
st.title("Social Media Content Generator")

tab1, tab2 = st.tabs(["Social Calendar Generator", "Article to LinkedIn Posts"])

with tab1:
    st.header("Social Media Calendar Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        brand = st.text_input("Brand Name", placeholder="e.g., Wienerschnitzel")
        brand_voice = st.text_area("Brand Voice", placeholder="e.g., Professional but approachable, authoritative in the fast-food space")
        portrayal = st.text_area("How they portray themselves", placeholder="e.g., Family-friendly franchise with focus on quality and consistency")
        focus = st.selectbox("Primary Focus", 
                            ["Grand Opening", "Franchise Focused", "SEO", "Keep Profile Active", 
                             "Product Launch", "Promotional", "Brand Awareness", "Customer Engagement", 
                             "Other"])
        if focus == "Other":
            focus = st.text_input("Specify focus", "")
    
    with col2:
        posts_per_month = st.number_input("How many posts per month?", min_value=1, max_value=30, value=6)
        special_events = st.text_area("Special Events to highlight", placeholder="e.g., National Hot Dog Day (July 21), Franchise Convention")
        overall_voice = st.text_area("Overall tone/voice", placeholder="e.g., Informative but casual, enthusiastic about franchising opportunities")
        last_month_examples = st.text_area("Examples of last month's posts", placeholder="Paste a few examples of previous posts here to avoid duplication")
        brand_phrases = st.text_area("Brand Phrases (optional)", placeholder="e.g., Always fresh, Real ingredients, Made to order")
    
    api_key = st.text_input("OpenAI API Key", type="password", help="Your API key is required to generate content")
    
    if st.button("Generate Social Media Calendar"):
        if not api_key:
            st.error("Please enter your OpenAI API key")
        else:
            st.session_state.api_key = api_key
            with st.spinner("Generating posts..."):
                st.session_state.generated_posts = generate_social_posts(
                    brand, brand_voice, portrayal, focus, posts_per_month, 
                    special_events, overall_voice, last_month_examples, api_key, brand_phrases
                )
                st.session_state.selected_posts = st.session_state.generated_posts.copy()
    
    # Display generated posts
    if st.session_state.generated_posts:
        st.subheader("Generated LinkedIn Posts")
        st.write("Select the posts you want to keep, provide feedback, or refine them.")
        
        for i, post in enumerate(st.session_state.generated_posts):
            col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.2, 0.1])
            
            with col1:
                selected = st.checkbox(f"#{post['number']}", value=post['selected'], key=f"select_{i}")
                st.session_state.generated_posts[i]['selected'] = selected
            
            with col2:
                st.markdown(f"**Date: {post['date']}**")
                post['content'] = st.text_area("Post", post['content'], height=150, key=f"post_{i}")
                post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"graphic_{i}")

            
            with col3:
                feedback = st.text_area("Refine as...", placeholder="e.g., casual, formal, fun", key=f"feedback_{i}",  height=100)
                st.session_state.generated_posts[i]['feedback'] = feedback
            
            with col4:
                if feedback:
                    if st.button("Refine", key=f"refine_{i}"):
                        with st.spinner("Refining post..."):
                            refined_post = refine_post(post, feedback, st.session_state.api_key)
                            st.session_state.generated_posts[i] = refined_post
                            st.rerun()
            
            st.divider()
        
        if st.button("Export Selected Posts"):
            # Filter selected posts
            selected_posts = [post for post in st.session_state.generated_posts if post['selected']]
            
            if not selected_posts:
                st.warning("No posts selected for export.")
            else:
                # Create a DataFrame for export
                export_data = []
                for post in selected_posts:
                    export_data.append({
                        "Date": post['date'],
                        "Post Content": post['content'],
                        "Graphic Concept": post['graphic']
                    })
                
                df = pd.DataFrame(export_data)
                
                # Convert to CSV for download
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{brand}_social_calendar.csv",
                    mime="text/csv"
                )
                
                # Also display as a table
                st.subheader("Selected Posts for Export")
                st.dataframe(df)

with tab2:
    st.header("Article to LinkedIn Posts")
    
    article_text = st.text_area("Paste your article here", height=300, 
                               placeholder="Paste the full text of your article here...")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_posts = st.number_input("Number of posts to generate", min_value=1, max_value=10, value=3)
    
    with col2:
        if not st.session_state.api_key:
            api_key = st.text_input("OpenAI API Key", type="password", 
                                   help="Your API key is required to generate content",
                                   key="article_tab_api_key")
        else:
            api_key = st.session_state.api_key
            st.info("Using API key from previous tab")
    
    if st.button("Generate Posts from Article"):
        if not api_key:
            st.error("Please enter your OpenAI API key")
        elif not article_text:
            st.error("Please paste your article text")
        else:
            st.session_state.api_key = api_key
            with st.spinner("Generating posts from article..."):
                st.session_state.article_posts = article_to_posts(article_text, num_posts, api_key)
    
    # Display article-based posts
    if 'article_posts' in st.session_state and st.session_state.article_posts:
        st.subheader("Generated LinkedIn Posts from Article")
        
        for i, post in enumerate(st.session_state.article_posts):
            col1, col2, col3, col4 = st.columns([0.1, 0.6, 0.2, 0.1])
            
            with col1:
                selected = st.checkbox(f"#{post['number']}", value=post['selected'], key=f"article_select_{i}")
                st.session_state.article_posts[i]['selected'] = selected
            
            with col2:
                post['content'] = st.text_area("Post", post['content'], height=150, key=f"post_{i}")
                post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"graphic_{i}")

            
            with col3:
                feedback = st.text_area("Refine as...", placeholder="e.g., casual, formal, fun", key=f"article_feedback_{i}", height=100)
                st.session_state.article_posts[i]['feedback'] = feedback
            
            with col4:
                if feedback:
                    if st.button("Refine", key=f"article_refine_{i}"):
                        with st.spinner("Refining post..."):
                            refined_post = refine_post(post, feedback, st.session_state.api_key)
                            st.session_state.article_posts[i] = refined_post
                            st.rerun()
            
            st.divider()
        
        if st.button("Export Selected Article Posts"):
            # Filter selected posts
            selected_posts = [post for post in st.session_state.article_posts if post['selected']]
            
            if not selected_posts:
                st.warning("No posts selected for export.")
            else:
                # Create a DataFrame for export
                export_data = []
                for post in selected_posts:
                    export_data.append({
                        "Post Content": post['content'],
                        "Graphic Concept": post['graphic']
                    })
                
                df = pd.DataFrame(export_data)
                
                # Convert to CSV for download
                csv = df.to_csv(index=False)
                st.download_butto(
                    label="Download CSV",
                    data=csv,
                    file_name="article_linkedin_posts.csv",
                    mime="text/csv"
                )
                
                # Also display as a table
                st.subheader("Selected Posts for Export")
                st.dataframe(df)

# Footer
st.markdown("---")
st.markdown("Social Media Content Generator")

