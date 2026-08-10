from codecompass.repo import RepoIngestionPipeline

if __name__ == "__main__":
    # Use a well-structured, medium-sized repo for testing
    URL = "https://github.com/pallets/click"
    
    # Initialize the pipeline
    pipeline = RepoIngestionPipeline(repo_url=URL)
    
    # Execute the full pipeline
    files = pipeline.execute()
    
    print(f"\n--- Pipeline Results ---")
    print(f"Total Python files extracted: {len(files)}")
    print("\nFirst 5 files:")
    for f in files[:5]:
        print(f" - {f.name}")