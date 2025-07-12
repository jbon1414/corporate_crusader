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
        Generate exactly {num_posts} unique LinkedIn posts for {brand_data['name']} for {current_month} {current_year}.
        
        Brand voice: {brand_data['brand_voice']}
        How they portray themselves: {brand_data['portrayal']}
        Primary focus: {focus}
        Special events to highlight: {special_events}
        Overall tone/voice: {brand_data['overall_voice']}
        Brand phrases to include when appropriate: {brand_data['brand_phrases']}
        Website: {brand_data.get('website', 'N/A')}
        
        Only schedule posts on weekdays. Create posts that are different from these examples:
        {brand_data['previous_posts']}
        
        IMPORTANT: Format each post EXACTLY as shown below. Use this exact format for ALL {num_posts} posts:

        POST #1 - [Weekday, Month Day, Year]:
        [LinkedIn post content here]

        GRAPHIC:
        [Brief description of graphic concept and remember that images may be limited, it may have to be a simple graphic or text-based image]

        POST #2 - [Weekday, Month Day, Year]:
        [LinkedIn post content here]

        GRAPHIC:
        [Brief description of graphic concept and remember that images may be limited, it may have to be a simple graphic or text-based image]

        Continue this pattern for all {num_posts} posts. Make sure each post is clearly separated and numbered consecutively.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate exactly {num_posts} LinkedIn posts for {brand_data['name']} focusing on {focus}. Use the exact format specified in the system prompt."}
            ],
            temperature=0.7,
            max_tokens=3000  # Increased token limit for more posts
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Debug: Print the raw content to help troubleshoot
        # st.write("**Debug - Raw AI Response:**")
        # st.text(content[:500] + "..." if len(content) > 500 else content)
        
        # Parse the generated posts with improved regex
        posts = []
        
        # Split by POST # to handle formatting variations
        post_sections = re.split(r'\n*POST #(\d+)', content)[1:]  # Skip first empty element
        
        for i in range(0, len(post_sections), 2):
            if i + 1 < len(post_sections):
                post_num = post_sections[i].strip()
                post_content = post_sections[i + 1].strip()
                
                # Extract date and content
                lines = post_content.split('\n')
                
                # Find the date line (should contain " - " after POST #)
                date_line = ""
                content_start = 0
                
                for idx, line in enumerate(lines):
                    if ' - ' in line and any(month in line for month in calendar.month_name[1:]):
                        date_line = line.split(' - ', 1)[1] if ' - ' in line else line
                        content_start = idx + 1
                        break
                    elif line.strip() and not line.startswith('POST #'):
                        # If no clear date found, use first non-empty line as date
                        date_line = line.strip()
                        content_start = idx + 1
                        break
                
                # Extract post content and graphic
                remaining_content = '\n'.join(lines[content_start:])
                
                # Split by GRAPHIC: to separate post content from graphic description
                parts = re.split(r'\n\s*GRAPHIC:\s*\n?', remaining_content, flags=re.IGNORECASE)
                
                post_text = parts[0].strip()
                graphic_desc = parts[1].strip() if len(parts) > 1 else "No graphic suggestion provided."
                
                # Clean up any remaining POST # references in the content
                post_text = re.sub(r'^POST #\d+.*?\n', '', post_text, flags=re.MULTILINE).strip()
                
                posts.append({
                    "number": post_num,
                    "date": date_line,
                    "content": post_text,
                    "graphic": graphic_desc,
                    "selected": True,
                    "feedback": "",
                    "post_feedback": "",
                    "graphic_feedback": ""
                })
        
        # If parsing failed, try alternative method
        if len(posts) == 0:
            st.warning("Primary parsing failed, trying alternative method...")
            
            # Alternative parsing: split by double newlines and look for patterns
            sections = content.split('\n\n')
            current_post = {}
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                # Check if this is a post header
                post_match = re.match(r'POST #(\d+)\s*-\s*(.*?):', section)
                if post_match:
                    # Save previous post if exists
                    if current_post and 'content' in current_post:
                        posts.append({
                            "number": current_post.get('number', str(len(posts) + 1)),
                            "date": current_post.get('date', ''),
                            "content": current_post.get('content', ''),
                            "graphic": current_post.get('graphic', 'No graphic suggestion provided.'),
                            "selected": True,
                            "feedback": "",
                            "post_feedback": "",
                            "graphic_feedback": ""
                        })
                    
                    # Start new post
                    current_post = {
                        'number': post_match.group(1),
                        'date': post_match.group(2),
                        'content': '',
                        'graphic': ''
                    }
                elif section.upper().startswith('GRAPHIC:'):
                    current_post['graphic'] = section[8:].strip()
                elif 'content' in current_post:
                    if current_post['content']:
                        current_post['content'] += '\n\n' + section
                    else:
                        current_post['content'] = section
            
            # Don't forget the last post
            if current_post and 'content' in current_post:
                posts.append({
                    "number": current_post.get('number', str(len(posts) + 1)),
                    "date": current_post.get('date', ''),
                    "content": current_post.get('content', ''),
                    "graphic": current_post.get('graphic', 'No graphic suggestion provided.'),
                    "selected": True,
                    "feedback": "",
                    "post_feedback": "",
                    "graphic_feedback": ""
                })
        
        st.success(f"Successfully parsed {len(posts)} posts out of expected {num_posts}")
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
        
        Return the response in this exact format:
        
        [Revised post content]
        
        GRAPHIC:
        [Revised graphic concept]
        """
        
        user_prompt = f"""Original post:
        {post['content']}
        
        Original graphic concept:
        {post['graphic']}
        
        Feedback: Make this more {feedback}"""
        
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
        
        # Split by GRAPHIC: to separate post content from graphic description
        parts = re.split(r'\n\s*GRAPHIC:\s*\n?', revised_text, flags=re.IGNORECASE)
        
        if len(parts) >= 2:
            revised_post = parts[0].strip()
            revised_graphic = parts[1].strip()
        else:
            revised_post = revised_text.strip()
            revised_graphic = post['graphic']
        
        return {
            "number": post['number'],
            "date": post['date'],
            "content": revised_post,
            "graphic": revised_graphic,
            "selected": post['selected'],
            "feedback": "",
            "post_feedback": "",
            "graphic_feedback": ""
        }
        
    except Exception as e:
        st.error(f"Error refining post: {str(e)}")
        return post


def refine_graphic(post, feedback, api_key):
    """Refine only the graphic concept based on feedback."""
    try:
        openai.api_key = api_key
        
        system_prompt = """You are an expert graphic designer and visual content creator.
        Revise only the graphic concept for a LinkedIn post based on the feedback provided.
        Consider visual elements like style, color scheme, layout, imagery, and overall aesthetic.
        Keep the graphic concept relevant to the post content but adjust the visual approach based on the feedback.
        
        Return only the revised graphic concept description - do not include the post content.
        """
        
        user_prompt = f"""Post content (for context):
        {post['content']}
        
        Current graphic concept:
        {post['graphic']}
        
        Feedback for graphic: Make this more {feedback}
        
        Please provide only the revised graphic concept:"""
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Return just the refined graphic concept
        refined_graphic = response.choices[0].message.content.strip()
        
        return refined_graphic
        
    except Exception as e:
        st.error(f"Error refining graphic: {str(e)}")
        return post['graphic']
    

def article_to_posts(article_text, website, num_posts, brand_data, api_key):
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
        {website}
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
        max_article_length = 8000
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
                "feedback": "",
                "post_feedback": "",
                "graphic_feedback": ""
            })
        
        return posts
    except Exception as e:
        st.error(f"Error generating posts from article: {str(e)}")
        return []
