# main_pipeline.py
import asyncio
import json
import networkx as nx
import pickle

from intelligent_crawler import IntelligentCrawler
from utils.summarizer import TextSummarizer
import config

async def run_pipeline():
    # 1. Explore the web application dynamically
    print("--- Step 1: Starting Intelligent WebApp Exploration ---")
    crawler = IntelligentCrawler()
    crawled_data = await crawler.explore()
    if not crawled_data:
        print("Exploration failed or returned no data. Exiting.")
        return

    print(f"\n--- Exploration Complete. Discovered {len(crawled_data)} pages/states. ---")

    # 2. Initialize AI Summarizer
    print("\n--- Step 2: Initializing AI Summarizer ---")
    summarizer = TextSummarizer()

    # 3. Process data: Build graph and generate summaries
    print("\n--- Step 3: Processing Data and Generating Summaries ---")
    site_graph = nx.DiGraph()
    final_data = {}

    for url, data in crawled_data.items():
        print(f"Processing: {url}")
        
        # Add page (node) and its links (edges) to the graph
        site_graph.add_node(url)
        for link in data["links"]:
            # Ensure the link target was also discovered before adding an edge
            if link in crawled_data:
                site_graph.add_edge(url, link)
        
        # Generate summary for the page's content
        summary = summarizer.summarize(data["text"])
        
        # Store all collected data for this URL
        final_data[url] = {
            "summary": summary,
            "raw_text": data["text"],
            "outgoing_links": data["links"]
        }

    # 4. Save the final data artifacts
    print("\n--- Step 4: Saving Final Data Artifacts ---")
    
    with open(config.STRUCTURED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)
    print(f"✅ Successfully saved structured data to: {config.STRUCTURED_DATA_FILE}")

    with open(config.GRAPH_FILE, "wb") as f:
        pickle.dump(site_graph, f)
    print(f"✅ Successfully saved site flow graph to: {config.GRAPH_FILE}")
    print(f"Graph contains {site_graph.number_of_nodes()} nodes and {site_graph.number_of_edges()} edges.")

    print("\n--- Pipeline Finished Successfully! ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())