import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from urllib.parse import urlparse

# Page config
st.set_page_config(
    page_title="Khan Academy Crawler Dashboard",
    page_icon="🕷️",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

def load_data():
    try:
        with open('crawl_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ crawl_results.json not found. Please run the crawler first.")
        return None

def calculate_crawlability_score(data):
    score = 100
    
    # Deduct points if crawl delay is too restrictive
    if data['crawl_config']['crawl_delay'] > 5:
        score -= 20
    elif data['crawl_config']['crawl_delay'] > 2:
        score -= 10
    
    # Add points for sitemaps
    if data['sitemaps']['urls']:
        score += min(len(data['sitemaps']['urls']) * 5, 20)
    
    # Deduct points for disallowed paths
    disallowed = sum(1 for status in data['tested_paths'].values() if status == 'Disallowed')
    score -= disallowed * 5
    
    return min(100, max(0, score))

def create_sitemap_visualization(data):
    G = nx.Graph()
    
    # Create nodes and edges from the extracted headings
    for section, pages in data['extracted_headings'].items():
        section_name = section.split('/')[-1].upper()
        G.add_node(section_name, size=20, color='#1f77b4')
        
        for page_url in pages.keys():
            page_name = urlparse(page_url).path.split('/')[-1]
            if page_name:
                G.add_node(page_name, size=15, color='#2ca02c')
                G.add_edge(section_name, page_name)
    
    # Get node positions using spring layout
    pos = nx.spring_layout(G)
    
    # Create edges trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edges_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    # Create nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_size.append(G.nodes[node]['size'])
        node_color.append(G.nodes[node]['color'])
    
    nodes_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        marker=dict(
            size=node_size,
            color=node_color,
            line_width=2))
    
    fig = go.Figure(data=[edges_trace, nodes_trace],
                   layout=go.Layout(
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                   )
    
    return fig

# Load data
data = load_data()

if data:
    # Title
    st.title("🕷️ Khan Academy Crawler Dashboard")
    st.markdown("---")
    
    # Top metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        crawlability_score = calculate_crawlability_score(data)
        st.metric("Crawlability Score", f"{crawlability_score}/100")
    
    with col2:
        st.metric("Pages Crawled", data['crawl_stats']['total_pages'])
    
    with col3:
        st.metric("Sections Analyzed", data['crawl_stats']['sections_crawled'])
    
    # Configuration and Stats
    st.markdown("### 📊 Crawl Configuration")
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        st.info(f"""
        - Max Depth: {data['crawl_config']['max_depth']}
        - Max Pages per Section: {data['crawl_config']['max_pages_per_section']}
        - Crawl Delay: {data['crawl_config']['crawl_delay']} seconds
        """)
    
    with config_col2:
        st.info(f"""
        - Sitemaps Found: {len(data['sitemaps']['urls'])}
        - Sections Crawled: {data['crawl_stats']['sections_crawled']}
        - Total Pages: {data['crawl_stats']['total_pages']}
        """)
    
    # Sitemap Visualization
    st.markdown("### 🗺️ Visual Sitemap")
    fig = create_sitemap_visualization(data)
    st.plotly_chart(fig, use_container_width=True)
    
    # Extracted Headings Analysis
    st.markdown("### 📑 Content Analysis")
    
    # Create tabs for each section
    tabs = st.tabs(list(data['extracted_headings'].keys()))
    
    for tab, (section, pages) in zip(tabs, data['extracted_headings'].items()):
        with tab:
            # Count headings by level for this section
            heading_counts = {f"h{i}": 0 for i in range(1, 7)}
            for page_data in pages.values():
                for level, headings in page_data.items():
                    heading_counts[level] += len(headings)
            
            # Create bar chart of heading distribution
            df = pd.DataFrame(list(heading_counts.items()), columns=['Level', 'Count'])
            fig = px.bar(df, x='Level', y='Count', 
                        title=f'Heading Distribution in {section}',
                        color='Count',
                        color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show sample headings
            st.markdown("#### Sample Content")
            for page_url, page_data in pages.items():
                with st.expander(f"📄 {urlparse(page_url).path}"):
                    for level, headings in page_data.items():
                        if headings:
                            st.markdown(f"**{level.upper()}**")
                            for heading in headings:
                                st.markdown(f"- {heading['text']}")
    
    # Recommendations
    st.markdown("### 💡 Recommendations")
    
    recommendations = [
        {
            "title": "Crawling Strategy",
            "content": f"""
            - Current crawl delay is {data['crawl_config']['crawl_delay']}s - {'consider increasing for less server load' if data['crawl_config']['crawl_delay'] < 2 else 'good balance'}
            - {'Using sitemaps is recommended for better coverage' if not data['sitemaps']['urls'] else 'Good use of sitemaps for navigation'}
            - {'Consider increasing depth for more content' if data['crawl_config']['max_depth'] < 2 else 'Good depth coverage'}
            """
        },
        {
            "title": "Tools & Techniques",
            "content": """
            - Use Selenium for JavaScript-rendered content
            - Implement rate limiting and respect robots.txt
            - Consider using async crawling for better performance
            - Add error recovery and retry mechanisms
            """
        },
        {
            "title": "Content Extraction",
            "content": """
            - Parse metadata for better content understanding
            - Extract structured data when available
            - Consider implementing full-text search
            - Add support for different content types
            """
        }
    ]
    
    cols = st.columns(len(recommendations))
    for col, rec in zip(cols, recommendations):
        with col:
            st.info(f"**{rec['title']}**\n{rec['content']}")
    
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard updates automatically when new crawl data is available*") 