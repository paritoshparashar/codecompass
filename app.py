import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="CodeCompass", layout="wide")

st.title("🧭 CodeCompass")
st.markdown("**Issue-to-Code Navigator** | Paste a repo and an issue, find the exact code to fix.")

with st.sidebar:
    st.header("Configuration")
    repo_url = st.text_input("GitHub Repo URL", value="https://github.com/pallets/click")
    issue_text = st.text_area("Issue Description", value="How do I add a default value to an argument?", height=150)
    analyze_btn = st.button("Analyze Codebase", type="primary")
    if st.button("Clear Cache for this Repo"):
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'): repo_name = repo_name[:-4]
        
        try:
            # This calls the backend to clear the disk cache
            import requests
            # We will just clear it locally for simplicity in this MVP
            import shutil
            from pathlib import Path
            cache_path = Path("./_cache") / repo_name
            if cache_path.exists():
                shutil.rmtree(cache_path)
                st.success("Cache cleared! Next run will re-process the repo.")
        except Exception as e:
            st.error(f"Failed to clear cache: {e}")

if analyze_btn:
    if not repo_url or not issue_text:
        st.error("Please provide both a repo URL and an issue description.")
    else:
        with st.spinner("Ingesting repo, parsing AST, and generating embeddings... This may take 15-30 seconds."):
            try:
                # Call the FastAPI backend running on localhost:8000
                response = requests.post(
                    "http://localhost:8000/analyze",
                    json={"repo_url": repo_url, "issue_text": issue_text},
                    timeout=9000
                )
                response.raise_for_status()
                data = response.json()
                
                st.success("Analysis Complete!")

                # Show the classification
                category = data.get('issue_category', 'unknown')
                st.info(f"**Issue Type Detected:** {category.capitalize()}")
                                
                st.header("Top 10 Relevant Files")
                for i, res in enumerate(data['ranked_files']):
                    # Clean up the path for display
                    file_name = res['file'].split('/')[-1]
                    
                    with st.expander(f"**{i+1}. {file_name}** (Final Score: {res['score']:.3f})", expanded=(i<3)):
                        col1, col2 = st.columns(2)
                        col1.metric("Semantic Score", f"{res['semantic']:.3f}")
                        col2.metric("Structural Score (PageRank)", f"{res['structural']:.3f}")
                        st.code(f"Full Path: {res['file']}", language="bash")
                        if 'explanation' in res:
                            st.info(f"**AI Explanation:** {res['explanation']}")

                # Render Interactive Graph
                if 'graph_html' in data and data['graph_html']:
                    st.header("Interactive Call Graph")
                    st.markdown("**Red nodes** are the top 3 ranked files. Drag, zoom, and hover to explore.")
                    components.html(data['graph_html'], height=650, scrolling=True)

                        
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to CodeCompass API. Did you start the backend? (Run: `uvicorn api:app`)")
            except Exception as e:
                st.error(f"An error occurred: {e}")