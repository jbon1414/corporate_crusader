import streamlit as st
import os
import pandas as pd
from utils.supabase_conn import SupaBase
from utils.openai import generate_social_posts, article_to_posts, refine_post, refine_graphic

st.set_page_config(page_title="Social Media Content Generator", layout="wide")

current_dir = os.path.dirname(__file__)
image_path = os.path.join(current_dir, r'The Glenwood Group-02.png')
st.image(image_path, width=400)

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
    st.session_state.brands = st.session_state.supabase_client.get_brands()

# Main app interface
st.title("Social Media Content Generator")

tab1, tab2, tab3, tab4 = st.tabs(["Brand Management", "Social Calendar Generator", "Article to LinkedIn Posts", "Previous Saved Posts"])

with tab1:
    st.header("Brand Management")
    
    if not st.session_state.supabase_client:
        st.warning("Supabase connection not available. Please check your .env file configuration.")
    else:
        # Refresh brands button
        if st.button("🔄 Refresh Brands"):
            st.session_state.brands = st.session_state.supabase_client.get_brands()
            st.rerun()
        
        # Create new brand section
        st.subheader("Create New Brand")
        
        with st.form("new_brand_form"):
            brand_name = st.text_input("Brand Name*", placeholder="e.g., Wienerschnitzel")
            brand_voice = st.text_area("Brand Voice*", placeholder="e.g., Professional but approachable, authoritative in the fast-food space")
            portrayal = st.text_area("How they portray themselves*", placeholder="e.g., Family-friendly franchise with focus on quality and consistency")
            overall_voice = st.text_area("Overall tone/voice*", placeholder="e.g., Informative but casual, enthusiastic about franchising opportunities")
            previous_posts = st.text_area("Examples of previous posts", placeholder="Paste a few examples of previous posts here")
            brand_phrases = st.text_area("Brand Phrases", placeholder="e.g., Always fresh, Real ingredients, Made to order")
            website = st.text_input("Website", placeholder="https://www.example.com")
            additional_info = st.text_area("Additional Information", placeholder="Any other relevant brand information")
            
            submitted = st.form_submit_button("Create Brand")
            
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
                        "additional_info": additional_info
                    }
                    
                    created_brand = st.session_state.supabase_client.create_brand(brand_data)
                    if created_brand:
                        st.success(f"Brand '{brand_name}' created successfully!")
                        st.session_state.brands = st.session_state.supabase_client.get_brands()
                        st.rerun()
                    else:
                        st.error("Failed to create brand. Please try again.")
                else:
                    st.error("Please fill in all required fields (marked with *)")
        
        # Display existing brands with edit functionality
        st.subheader("Existing Brands")
        
        if st.session_state.brands:
            for brand in st.session_state.brands:
                with st.expander(f"📊 {brand['name']}"):
                    # Create edit form for each brand
                    with st.form(f"edit_brand_form_{brand['id']}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            edit_name = st.text_input("Brand Name", value=brand['name'], key=f"edit_name_{brand['id']}")
                            edit_voice = st.text_area("Brand Voice", value=brand['brand_voice'] or '', key=f"edit_voice_{brand['id']}")
                            edit_portrayal = st.text_area("Portrayal", value=brand['portrayal'] or '', key=f"edit_portrayal_{brand['id']}")
                            edit_overall_voice = st.text_area("Overall Voice", value=brand['overall_voice'] or '', key=f"edit_overall_voice_{brand['id']}")
                            edit_previous_posts = st.text_area("Previous Posts", value=brand['previous_posts'] or '', key=f"edit_previous_posts_{brand['id']}")
                            edit_brand_phrases = st.text_area("Brand Phrases", value=brand['brand_phrases'] or '', key=f"edit_brand_phrases_{brand['id']}")
                            edit_website = st.text_input("Website", value=brand['website'] or '', key=f"edit_website_{brand['id']}")
                            edit_additional_info = st.text_area("Additional Info", value=brand['additional_info'] or '', key=f"edit_additional_info_{brand['id']}")
                        
                        with col2:
                            st.write("**Actions**")
                            update_submitted = st.form_submit_button("💾 Update Brand")
                            
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
                                        "additional_info": edit_additional_info
                                    }
                                    
                                    updated_brand = st.session_state.supabase_client.update_brand(brand['id'], updated_brand_data)
                                    if updated_brand:
                                        st.success(f"Brand '{edit_name}' updated successfully!")
                                        st.session_state.brands = st.session_state.supabase_client.get_brands()
                                        st.rerun()
                                    else:
                                        st.error("Failed to update brand. Please try again.")
                                else:
                                    st.error("Please fill in all required fields")
                    
                    # Delete button outside the form
                    if st.button("🗑️ Delete Brand", key=f"delete_{brand['id']}"):
                        if st.session_state.supabase_client.delete_brand(brand['id']):
                            st.success("Brand deleted successfully!")
                            st.session_state.brands = st.session_state.supabase_client.get_brands()
                            st.rerun()
                        else:
                            st.error("Failed to delete brand.")
        else:
            st.info("No brands created yet. Create your first brand above!")

with tab2:
    st.header("Social Media Calendar Generator")
    
    if not st.session_state.supabase_client or not st.session_state.brands:
        st.warning("Please check your Supabase connection and create at least one brand in the Brand Management tab.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            # Brand selection dropdown
            brand_options = {brand['name']: brand['id'] for brand in st.session_state.brands}
            selected_brand_name = st.selectbox("Select Brand*", options=list(brand_options.keys()))
            selected_brand_id = brand_options[selected_brand_name] if selected_brand_name else None
            selected_brand_data = st.session_state.supabase_client.get_brand_by_id(selected_brand_id) if selected_brand_id else None
            
            focus = st.selectbox("Primary Focus", 
                                ["Grand Opening", "Franchise Focused", "SEO", "Keep Profile Active", 
                                 "Product Launch", "Promotional", "Brand Awareness", "Customer Engagement", 
                                 "Other"])
            if focus == "Other":
                focus = st.text_input("Specify focus", "")
        
        with col2:
            num_posts = st.number_input("How many posts per month?", min_value=1, max_value=30, value=6)
            special_events = st.text_area("Special Events to highlight", placeholder="e.g., National Hot Dog Day (July 21), Franchise Convention")
            api_key = st.text_input("OpenAI API Key", type="password", help="Your API key is required to generate content")
        
        if st.button("Generate Social Media Calendar"):
            if not api_key:
                st.error("Please enter your OpenAI API key")
            elif not selected_brand_data:
                st.error("Please select a brand")
            else:
                st.session_state.api_key = api_key
                with st.spinner("Generating posts..."):
                    st.session_state.generated_posts = generate_social_posts(
                        selected_brand_data, focus, num_posts, 
                        special_events, api_key
                    )
                    st.session_state.selected_posts = st.session_state.generated_posts.copy()
        
        # Display generated posts
        if st.session_state.generated_posts:
            st.subheader("Generated LinkedIn Posts")
            st.write("Select the posts you want to keep, provide feedback, or refine them.")
            
            for i, post in enumerate(st.session_state.generated_posts):
                # Create 5 columns: checkbox, content area, post refinement, graphic refinement, actions
                col1, col2, col3, col4, col5 = st.columns([0.05, 0.45, 0.15, 0.15, 0.2])
                
                with col1:
                    selected = st.checkbox(f"#{post['number']}", value=post['selected'], key=f"select_{i}")
                    st.session_state.generated_posts[i]['selected'] = selected
                
                with col2:
                    st.markdown(f"**Date: {post['date']}**")
                    post['content'] = st.text_area("Post", post['content'], height=150, key=f"post_{i}")
                    post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"graphic_{i}")
                
                with col3:
                    st.markdown("**Refine Post**")
                    post_feedback = st.text_area("Refine post as...", placeholder="e.g., casual, formal, fun", key=f"post_feedback_{i}", height=70)
                    st.session_state.generated_posts[i]['post_feedback'] = post_feedback
                    
                    if post_feedback:
                        if st.button("Refine Post", key=f"refine_post_{i}"):
                            with st.spinner("Refining post..."):
                                refined_post = refine_post(post, post_feedback, st.session_state.api_key)
                                st.session_state.generated_posts[i] = refined_post
                                st.rerun()
                
                with col4:
                    st.markdown("**Refine Graphic**")
                    graphic_feedback = st.text_area("Refine graphic as...", placeholder="e.g., minimalist, colorful, corporate", key=f"graphic_feedback_{i}", height=70)
                    st.session_state.generated_posts[i]['graphic_feedback'] = graphic_feedback
                    
                    if graphic_feedback:
                        if st.button("Refine Graphic", key=f"refine_graphic_{i}"):
                            with st.spinner("Refining graphic concept..."):
                                refined_graphic = refine_graphic(post, graphic_feedback, st.session_state.api_key)
                                st.session_state.generated_posts[i]['graphic'] = refined_graphic
                                st.rerun()
                
                with col5:
                    st.markdown("**Actions**")
                    # Keep legacy feedback field for backward compatibility
                    legacy_feedback = st.text_area("General feedback", placeholder="General refinement", key=f"legacy_feedback_{i}", height=70)
                    st.session_state.generated_posts[i]['feedback'] = legacy_feedback
                    
                    if legacy_feedback:
                        if st.button("Refine Both", key=f"refine_both_{i}"):
                            with st.spinner("Refining post and graphic..."):
                                refined_post = refine_post(post, legacy_feedback, st.session_state.api_key)
                                st.session_state.generated_posts[i] = refined_post
                                st.rerun()
                
                st.divider()
            
            if st.button("Export Selected Posts"):
                # Filter selected posts
                selected_posts = [post for post in st.session_state.generated_posts if post['selected']]
                
                if not selected_posts:
                    st.warning("No posts selected for export.")
                else:
                    # Save selected posts to Supabase
                    saved_count = 0
                    for post in selected_posts:
                        result = st.session_state.supabase_client.save_posts(
                            brand_id=selected_brand_id,
                            post=post['content'],
                            user_id=None,
                            graphic_concept=post['graphic'],
                            type="LinkedIn Posts",
                            date=post['date']
                        )
                        if result:
                            saved_count += 1
                    st.success(f"{saved_count} posts saved to Supabase.")

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
                        file_name=f"{selected_brand_name}_social_calendar.csv",
                        mime="text/csv"
                    )
                    
                    # Also display as a table
                    st.subheader("Selected Posts for Export")
                    st.dataframe(df)

with tab3:
    st.header("Article to LinkedIn Posts")
    
    article_text = st.text_area("Paste your article here", height=300, 
                               placeholder="Paste the full text of your article here...")
    website = st.text_input("Article URL", placeholder="place article URL here (optional)",)

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
    
    if st.button("Generate Posts from Article"):
        if not api_key:
            st.error("Please enter your OpenAI API key")
        elif not article_text:
            st.error("Please paste your article text")
        else:
            st.session_state.api_key = api_key
            with st.spinner("Generating posts from article..."):
                # Use brand data if selected, otherwise use generic brand data
                brand_data_to_use = selected_article_brand_data if selected_article_brand_data else {
                    'name': 'Generic Brand',
                    'brand_voice': 'Professional and engaging',
                    'overall_voice': 'Informative and approachable',
                    'brand_phrases': ''
                }
                st.session_state.article_posts = article_to_posts(article_text, website, num_posts, brand_data_to_use, api_key)
    
    # Display article-based posts
    if 'article_posts' in st.session_state and st.session_state.article_posts:
        st.subheader("Generated LinkedIn Posts from Article")
        
        for i, post in enumerate(st.session_state.article_posts):
            # Create 5 columns: checkbox, content area, post refinement, graphic refinement, actions
            col1, col2, col3, col4, col5 = st.columns([0.05, 0.45, 0.15, 0.15, 0.2])
            
            with col1:
                selected = st.checkbox(f"#{post['number']}", value=post['selected'], key=f"article_select_{i}")
                st.session_state.article_posts[i]['selected'] = selected
            
            with col2:
                post['content'] = st.text_area("Post", post['content'], height=150, key=f"article_post_{i}")
                post['graphic'] = st.text_area("Graphic Concept", post['graphic'], height=80, key=f"article_graphic_{i}")
            
            with col3:
                st.markdown("**Refine Post**")
                article_post_feedback = st.text_area("Refine post as...", placeholder="e.g., casual, formal, fun", key=f"article_post_feedback_{i}", height=70)
                st.session_state.article_posts[i]['post_feedback'] = article_post_feedback
                
                if article_post_feedback:
                    if st.button("Refine Post", key=f"article_refine_post_{i}"):
                        with st.spinner("Refining post..."):
                            refined_post = refine_post(post, article_post_feedback, st.session_state.api_key)
                            st.session_state.article_posts[i] = refined_post
                            st.rerun()
            
            with col4:
                st.markdown("**Refine Graphic**")
                article_graphic_feedback = st.text_area("Refine graphic as...", placeholder="e.g., minimalist, colorful, corporate", key=f"article_graphic_feedback_{i}", height=70)
                st.session_state.article_posts[i]['graphic_feedback'] = article_graphic_feedback
                
                if article_graphic_feedback:
                    if st.button("Refine Graphic", key=f"article_refine_graphic_{i}"):
                        with st.spinner("Refining graphic concept..."):
                            refined_graphic = refine_graphic(post, article_graphic_feedback, st.session_state.api_key)
                            st.session_state.article_posts[i]['graphic'] = refined_graphic
                            st.rerun()
            
            with col5:
                st.markdown("**Actions**")
                # Keep legacy feedback field for backward compatibility
                article_legacy_feedback = st.text_area("General feedback", placeholder="General refinement", key=f"article_legacy_feedback_{i}", height=70)
                st.session_state.article_posts[i]['feedback'] = article_legacy_feedback
                
                if article_legacy_feedback:
                    if st.button("Refine Both", key=f"article_refine_both_{i}"):
                        with st.spinner("Refining post and graphic..."):
                            refined_post = refine_post(post, article_legacy_feedback, st.session_state.api_key)
                            st.session_state.article_posts[i] = refined_post
                            st.rerun()
            
            st.divider()
        
        if st.button("Export Selected Article Posts"):
            # Filter selected posts
            selected_posts = [post for post in st.session_state.article_posts if post['selected']]
            
            if not selected_posts:
                st.warning("No posts selected for export.")
            else:
                # Save selected article posts to Supabase
                saved_count = 0
                for post in selected_posts:
                    result = st.session_state.supabase_client.save_posts(
                        brand_id=selected_article_brand_id,
                        post=post['content'],
                        user_id=None,
                        graphic_concept=post['graphic'],
                        type="LinkedIn Article Posts",
                        date='' #TODO: Add date handling if needed
                    )
                    if result:
                        saved_count += 1
                st.success(f"{saved_count} article posts saved to Supabase.")

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
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="article_linkedin_posts.csv",
                    mime="text/csv"
                )
                
                # Also display as a table
                st.subheader("Selected Posts for Export")
                st.dataframe(df)

with tab4:
    st.header("Previous Saved Posts")
    
    if not st.session_state.supabase_client or not st.session_state.brands:
        st.warning("Please check your Supabase connection and create at least one brand in the Brand Management tab.")
    else:
        brand_options = {brand['name']: brand['id'] for brand in st.session_state.brands}
        selected_prev_brand_name = st.selectbox("Select Brand to View Posts", options=list(brand_options.keys()), key="prev_brand_select")
        selected_prev_brand_id = brand_options[selected_prev_brand_name] if selected_prev_brand_name else None
        
        if st.button("Load Saved Posts"):
            if selected_prev_brand_id:
                with st.spinner("Loading saved posts..."):
                    posts = st.session_state.supabase_client.get_posts_by_brand(selected_prev_brand_id)
                    if posts:
                        st.subheader(f"Saved Posts for {selected_prev_brand_name}")
                        for post in posts:
                            with st.expander(f"📅 {post.get('date', 'No Date')} | {post.get('type', 'No Type')}"):
                                st.markdown(f"**Post Content:**\n\n{post.get('post', '')}")
                                st.markdown(f"**Graphic Concept:**\n\n{post.get('graphic_concept', '')}")
                                st.markdown(f"**User ID:** `{post.get('user_id', 'N/A')}`")
                    else:
                        st.info("No saved posts found for this brand.")
            else:
                st.warning("Please select a brand.")

# Footer
st.markdown("---")
st.markdown("Social Media Content Generator")
