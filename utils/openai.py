import openai
from datetime import datetime
import calendar
import re
import streamlit as st
import pandas as pd 


def generate_social_posts(brand_data, focus, posts_per_month, 
                         special_events, api_key):
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
        
        # Create a tailored prompt using brand data
        system_prompt = f"""You are an expert social media copywriter specializing in creating engaging content.
        Generate {num_posts} unique LinkedIn posts for {brand_data['name']} for {current_month} {current_year}.
        
        Brand voice: {brand_data['brand_voice']}
        How they portray themselves: {brand_data['portrayal']}
        Primary focus: {focus}
        Special events to highlight: {special_events}
        Overall tone/voice: {brand_data['overall_voice']}
        Brand phrases to include when appropriate: {brand_data['brand_phrases']}
        Website: {brand_data.get('website', 'N/A')}
        
        Only schedule posts on weekdays. Create posts that are different from these examples:
        {brand_data['previous_posts']}
        
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
                {"role": "user", "content": f"Generate {num_posts} LinkedIn posts for {brand_data['name']} focusing on {focus}."}
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
    

def article_to_posts(article_text, num_posts, brand_data, api_key):
    """Generate LinkedIn posts based on an article."""
    try:
        openai.api_key = api_key
        
        # Include brand information in the prompt
        brand_context = f"""
        Brand: {brand_data['name']}
        Brand voice: {brand_data['brand_voice']}
        Overall tone: {brand_data['overall_voice']}
        Brand phrases: {brand_data['brand_phrases']}
        """
        
        system_prompt = f"""You are an expert content marketer specializing in LinkedIn.
        Based on the article provided, create {num_posts} LinkedIn posts that highlight key insights or quotes from the article.
        Each post should be standalone, engaging, and encourage readers to read the full article.
        Vary the style and approach of each post to appeal to different audience segments.
        
        {brand_context}
        
        Make sure the posts align with the brand voice and tone specified above.
        
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
