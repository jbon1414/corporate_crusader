import openai
from datetime import datetime
import calendar
import re
import streamlit as st
import pandas as pd 
import openai
import re
import streamlit as st


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


def refine_content(post, feedback, api_key, refine_post=True, refine_graphic=True):
    """
    Refine post content and/or graphic concept based on feedback and checkbox selections.
    
    Args:
        post (dict): The post object containing content and graphic info
        feedback (str): User feedback for refinement
        api_key (str): OpenAI API key
        refine_post (bool): Whether to refine the post content
        refine_graphic (bool): Whether to refine the graphic concept
    
    Returns:
        dict: Updated post object with refined content
    """
    try:
        openai.api_key = api_key
        
        # Determine what to refine based on checkboxes
        if refine_post and refine_graphic:
            # Refine both post and graphic
            system_prompt = """You are an expert social media copywriter and graphic designer. 
            Revise both the LinkedIn post content and the graphic concept according to the feedback.
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
            
        elif refine_post and not refine_graphic:
            # Refine only the post content
            system_prompt = """You are an expert social media copywriter. 
            Revise only the LinkedIn post content according to the feedback.
            Maintain the same general message but adjust the tone, style, or focus based on the feedback.
            Do not modify the graphic concept.
            
            Return only the revised post content."""
            
            user_prompt = f"""Original post:
            {post['content']}
            
            Feedback: Make this more {feedback}
            
            Please provide only the revised post content:"""
            
        elif not refine_post and refine_graphic:
            # Refine only the graphic concept
            system_prompt = """You are an expert graphic designer and visual content creator.
            Revise only the graphic concept for a LinkedIn post based on the feedback provided.
            Consider visual elements like style, color scheme, layout, imagery, and overall aesthetic.
            Keep the graphic concept relevant to the post content but adjust the visual approach based on the feedback.
            Do not modify the post content.
            
            Return only the revised graphic concept description."""
            
            user_prompt = f"""Post content (for context):
            {post['content']}
            
            Current graphic concept:
            {post['graphic']}
            
            Feedback for graphic: Make this more {feedback}
            
            Please provide only the revised graphic concept:"""
        
        else:
            # Neither checkbox selected - return original post
            return post
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Parse the response based on what was refined
        revised_text = response.choices[0].message.content.strip()
        
        # Create updated post object
        updated_post = {
            "number": post['number'],
            "date": post['date'],
            "content": post['content'],  # Default to original
            "graphic": post['graphic'],  # Default to original
            "selected": post['selected'],
            "feedback": "",
            "refine_post": False,
            "refine_graphic": False
        }
        
        if refine_post and refine_graphic:
            # Split by GRAPHIC: to separate post content from graphic description
            parts = re.split(r'\n\s*GRAPHIC:\s*\n?', revised_text, flags=re.IGNORECASE)
            
            if len(parts) >= 2:
                updated_post['content'] = parts[0].strip()
                updated_post['graphic'] = parts[1].strip()
            else:
                # If parsing fails, treat as post content only
                updated_post['content'] = revised_text
                
        elif refine_post and not refine_graphic:
            # Only update post content
            updated_post['content'] = revised_text
            
        elif not refine_post and refine_graphic:
            # Only update graphic concept
            updated_post['graphic'] = revised_text
        
        return updated_post
        
    except Exception as e:
        st.error(f"Error refining content: {str(e)}")
        return post

def article_to_posts(article_text=None, website_url=None, num_posts=3, brand_data=None, api_key=None):
    """Generate LinkedIn posts based on an article text and/or website URL."""
    try:
        openai.api_key = api_key
        
        # Validate inputs
        if not article_text and not website_url:
            raise ValueError("Either article_text or website_url must be provided")
        
        # Include brand information in the prompt
        brand_context = f"""
        Brand: {brand_data['name']}
        Brand voice: {brand_data['brand_voice']}
        Overall tone: {brand_data['overall_voice']}
        Brand phrases: {brand_data['brand_phrases']}
        """
        
        # Determine the content source and build the prompt accordingly
        if article_text and website_url:
            # Both provided
            system_prompt = f"""You are an expert content marketer specializing in LinkedIn.
            Based on the article text provided AND the content from the website URL, create exactly {num_posts} LinkedIn posts that highlight key insights or quotes.
            Each post should be standalone, engaging, and encourage readers to engage with the content.
            Vary the style and approach of each post to appeal to different audience segments.
            
            {brand_context}
            
            Make sure the posts align with the brand voice and tone specified above.
            
            IMPORTANT: You must create exactly {num_posts} posts. Number them clearly as POST #1, POST #2, POST #3, etc.
            
            Format each post EXACTLY as:
            
            POST #1:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept that would complement this post and remember that images may be limited, it may have to be a simple graphic or text-based image]
            
            POST #2:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept]
            
            Continue this pattern for all {num_posts} posts.
            """
            
            # Truncate article if too long
            max_article_length = 10000
            if len(article_text) > max_article_length:
                article_text = article_text[:max_article_length] + "... [article truncated]"
            
            user_prompt = f"""Here's the article text to use:
            
            {article_text}
            
            Also, please search for and analyze the content from this URL: {website_url}
            
            Create exactly {num_posts} LinkedIn posts using insights from both sources."""
            
        elif article_text:
            # Only article text provided
            system_prompt = f"""You are an expert content marketer specializing in LinkedIn.
            Based on the article text provided, create exactly {num_posts} LinkedIn posts that highlight key insights or quotes from the article.
            Each post should be standalone, engaging, and encourage readers to engage with the content.
            Vary the style and approach of each post to appeal to different audience segments.
            
            {brand_context}
            
            Make sure the posts align with the brand voice and tone specified above.
            
            IMPORTANT: You must create exactly {num_posts} posts. Number them clearly as POST #1, POST #2, POST #3, etc.
            
            Format each post EXACTLY as:
            
            POST #1:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept that would complement this post and remember that images may be limited, it may have to be a simple graphic or text-based image]
            
            POST #2:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept]
            
            Continue this pattern for all {num_posts} posts.
            """
            
            # Truncate article if too long
            max_article_length = 10000
            if len(article_text) > max_article_length:
                article_text = article_text[:max_article_length] + "... [article truncated]"
            
            user_prompt = f"Here's the article to use for creating exactly {num_posts} LinkedIn posts:\n\n{article_text}"
            
        else:
            # Only website URL provided
            system_prompt = f"""You are an expert content marketer specializing in LinkedIn.
            Search for and analyze the content from the provided URL, then create exactly {num_posts} LinkedIn posts that highlight key insights or quotes from that content.
            Each post should be standalone, engaging, and encourage readers to visit the original article.
            Vary the style and approach of each post to appeal to different audience segments.
            
            {brand_context}
            
            Make sure the posts align with the brand voice and tone specified above.
            
            IMPORTANT: You must create exactly {num_posts} posts. Number them clearly as POST #1, POST #2, POST #3, etc.
            
            Format each post EXACTLY as:
            
            POST #1:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept that would complement this post and remember that images may be limited, it may have to be a simple graphic or text-based image]
            
            POST #2:
            [LinkedIn post copy]
            
            GRAPHIC:
            [Brief description of graphic concept]
            
            Continue this pattern for all {num_posts} posts.
            """
            
            user_prompt = f"Please search for and analyze the content from this URL: {website_url}\n\nThen create exactly {num_posts} LinkedIn posts based on that content."
        
        # Prepare the API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Only include web search tool if we have a website URL
        tools = []
        if website_url:
            tools = [{"type": "web_search_preview"}]
        
        # Make the API call using the Responses API for web search capability
        if tools:
            # Use the new Responses API when web search is needed
            client = openai.OpenAI(api_key=api_key)
            response = client.responses.create(
                model="gpt-4o",  # Use a model that supports web search
                tools=tools,
                input=user_prompt + "\n\nSystem instructions: " + system_prompt,
                temperature=0.7
            )
            content = response.output_text
        else:
            # Use regular chat completions when only article text is provided
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=3000  # Increased to accommodate multiple posts
            )
            content = response.choices[0].message.content
        
        # Debug: Print the raw content to see what's being generated
        print("Raw API Response:")
        print("=" * 50)
        print(content)
        print("=" * 50)
        
        # Parse the generated posts with improved regex
        posts = []
        # Updated pattern to be more flexible with whitespace and formatting
        pattern = r'POST #(\d+):\s*(.*?)(?:\s*GRAPHIC:\s*(.*?))?(?=\s*POST #\d+:|$)'
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            post_num = match.group(1)
            post_content = match.group(2).strip() if match.group(2) else ""
            graphic_desc = match.group(3).strip() if match.group(3) else "Simple, clean graphic that complements the post content"
            
            # Clean up post content - remove any trailing GRAPHIC: text that might have been included
            post_content = re.sub(r'\s*GRAPHIC:\s*.*$', '', post_content, flags=re.DOTALL | re.IGNORECASE).strip()
            
            # Remove markdown formatting (** bold markers)
            post_content = re.sub(r'\*\*(.*?)\*\*', r'\1', post_content)  # Remove **text**
            post_content = re.sub(r'\*(.*?)\*', r'\1', post_content)      # Remove *text*
            post_content = post_content.replace('**', '').replace('*', '') # Remove any remaining asterisks
            
            # Clean up graphic description too
            graphic_desc = re.sub(r'\*\*(.*?)\*\*', r'\1', graphic_desc)
            graphic_desc = re.sub(r'\*(.*?)\*', r'\1', graphic_desc)
            graphic_desc = graphic_desc.replace('**', '').replace('*', '')
            
            posts.append({
                "number": post_num,
                "date": "",  # No date required for article-based posts
                "content": post_content,
                "graphic": graphic_desc,
                "selected": True,
                "feedback": "",
                "post_feedback": "",
                "graphic_feedback": "",
                "refine_post": False,
                "refine_graphic": False
            })
        
        # Debug: Print parsing results
        print(f"Parsed {len(posts)} posts from response")
        for i, post in enumerate(posts):
            print(f"Post {i+1}: {post['content'][:100]}...")
        
        # If no posts were parsed or we got fewer than expected, try alternative parsing
        if len(posts) < num_posts:
            print("Trying alternative parsing method...")
            
            # Try splitting by POST # and processing each section
            alt_posts = []
            post_sections = re.split(r'POST #\d+:', content, flags=re.IGNORECASE)
            
            # Skip the first section (it's before the first POST #)
            for i, section in enumerate(post_sections[1:], 1):
                section = section.strip()
                if section:
                    # Split by GRAPHIC: if present
                    parts = re.split(r'\s*GRAPHIC:\s*', section, flags=re.IGNORECASE)
                    post_content = parts[0].strip()
                    graphic_content = parts[1].strip() if len(parts) > 1 else "Simple, clean graphic that complements the post content"
                    
                    if post_content:
                        # Clean markdown formatting from alternative parsing too
                        post_content = re.sub(r'\*\*(.*?)\*\*', r'\1', post_content)
                        post_content = re.sub(r'\*(.*?)\*', r'\1', post_content)
                        post_content = post_content.replace('**', '').replace('*', '')
                        
                        graphic_content = re.sub(r'\*\*(.*?)\*\*', r'\1', graphic_content)
                        graphic_content = re.sub(r'\*(.*?)\*', r'\1', graphic_content)
                        graphic_content = graphic_content.replace('**', '').replace('*', '')
                        
                        alt_posts.append({
                            "number": str(i),
                            "date": "",
                            "content": post_content,
                            "graphic": graphic_content,
                            "selected": True,
                            "feedback": "",
                            "post_feedback": "",
                            "graphic_feedback": "",
                            "refine_post": False,
                            "refine_graphic": False
                        })
            
            # Use alternative parsing if it found more posts
            if len(alt_posts) > len(posts):
                posts = alt_posts
                print(f"Alternative parsing found {len(posts)} posts")
        
        # If we still don't have enough posts, create placeholder posts
        if len(posts) < num_posts:
            st.warning(f"Only generated {len(posts)} out of {num_posts} requested posts. Check the raw response in the console for debugging.")
            
            # Add placeholder posts if needed
            for i in range(len(posts) + 1, num_posts + 1):
                posts.append({
                    "number": str(i),
                    "date": "",
                    "content": f"Post {i} content was not generated properly. Please try regenerating or refining the content.",
                    "graphic": "Simple, clean graphic that complements the post content",
                    "selected": True,
                    "feedback": "",
                    "post_feedback": "",
                    "graphic_feedback": "",
                    "refine_post": False,
                    "refine_graphic": False
                })
        
        return posts[:num_posts]  # Return only the requested number of posts
        
    except Exception as e:
        st.error(f"Error generating posts from article: {str(e)}")
        return []