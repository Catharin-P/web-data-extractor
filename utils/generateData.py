# generate_data.py
import asyncio
import json
import networkx as nx
import pickle

from src.crawler import WebAppCrawler
from utils.summarizer import TextSummarizer

# --- Configuration ---
# You can change this to the starting URL of the web app you want to analyze
START_URL = "http://books.toscrape.com/"
STRUCTURED_DATA_FILE = "structured_data.json"
GRAPH_FILE = "site_graph.gpickle"

async def run_pipeline():
    # 1. Crawl the web application to get text and links
    print("--- Step 1: Starting Web Application Crawl ---")
    crawler = WebAppCrawler(START_URL)
    crawled_data = await crawler.crawl()
    if not crawled_data:
        print("Crawling failed or returned no data. Exiting pipeline.")
        return

    print(f"\n--- Crawl Complete. Found {len(crawled_data)} pages. ---")

    # 2. Initialize the AI Summarizer
    print("\n--- Step 2: Initializing AI Summarizer ---")
    summarizer = TextSummarizer()

    # 3. Process data: Build graph and summarize content
    print("\n--- Step 3: Processing Data and Generating Summaries ---")
    site_graph = nx.DiGraph()
    final_data = {}

    for url, data in crawled_data.items():
        print(f"Processing: {url}")
        
        # Add the page (node) and its links (edges) to the graph
        site_graph.add_node(url)
        for link in data["links"]:
            if link in crawled_data: # Ensure the link target was also crawled
                site_graph.add_edge(url, link)
        
        # Generate the AI summary for the page's content
        summary = summarizer.summarize(data["text"])
        
        # Store all collected data for this URL
        final_data[url] = {
            "summary": summary,
            "raw_text": data["text"],
            "outgoing_links": data["links"]
        }

    # 4. Save the final structured data
    print("\n--- Step 4: Saving Final Data Artifacts ---")
    
    # Save the comprehensive JSON data file
    with open(STRUCTURED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)
    print(f"✅ Successfully saved structured data to: {STRUCTURED_DATA_FILE}")

    # Save the NetworkX graph object for flow analysis
    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(site_graph, f)
    print(f"✅ Successfully saved site flow graph to: {GRAPH_FILE}")
    print(f"Graph contains {site_graph.number_of_nodes()} nodes and {site_graph.number_of_edges()} edges.")

    print("\n--- Pipeline Finished Successfully! ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())