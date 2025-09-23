# main_pipeline.py
import asyncio
import json
import networkx as nx
import pickle

# We now need the summarizer class in this main file to call it at the end
from utils.summarizer import TextSummarizer
from src.crawler import IntelligentCrawler
import config

async def generate_flow_summary(final_data: dict, summarizer: TextSummarizer):
    """
    Takes all the crawled data and asks the AI to generate a
    holistic user flow guide.
    """
    print("\n" + "="*60)
    print("Step 4: Generating Final User Flow Summary")
    print("="*60)

    # 1. Prepare the input data for the AI
    # We create a simplified text map of the entire application.
    app_map_string = "Here is a map of the web application, with each page's URL, a summary of its purpose, and the other pages it links to:\n\n"
    for url, data in final_data.items():
        app_map_string += f"Page URL: {url}\n"
        app_map_string += f"Page Summary: {data.get('summary', 'N/A')}\n"
        
        links = data.get('outgoing_links', [])
        if links:
            app_map_string += "Links to:\n"
            for link in links:
                app_map_string += f"- {link}\n"
        app_map_string += "---\n"

    # 2. Define the powerful final prompt
    system_prompt = (
        "You are a helpful and clear technical writer. Your goal is to create a user guide for a new user "
        "by analyzing a map of a web application. The map contains page URLs, summaries of each page's purpose, "
        "and their connections."
    )
    user_prompt = (
        f"Based on the application map provided below, please write a user flow guide. Structure it as a step-by-step walkthrough. "
        f"Start from the '/home' page and describe a logical journey a new user would take to explore the main features. "
        f"Explain what they can do on each key page (like 'New Project', 'Saved Projects', 'My Orders', etc.). "
        f"Use a friendly and encouraging tone. Format the output using Markdown for clarity (e.g., using headings and bullet points).\n\n"
        f"APPLICATION MAP:\n{app_map_string}"
    )

    # 3. Call the AI
    try:
        if not summarizer.client:
            print("OpenAI client not available. Skipping flow summary.")
            return

        print("Sending complete application map to GPT-4o-mini for final analysis...")
        completion = summarizer.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=1500, # Allow for a longer, more detailed guide
        )
        flow_summary = completion.choices[0].message.content.strip()

        # 4. Display and save the result
        print("\n--- WEB APP USER FLOW GUIDE ---")
        print(flow_summary)
        print("---------------------------------")

        # Save the guide to a Markdown file for easy reading
        with open("flow_summary.md", "w", encoding="utf-8") as f:
            f.write(flow_summary)
        print("\n✅ Successfully saved user flow guide to: flow_summary.md")

    except Exception as e:
        print("\n--- ERROR Generating Final Flow Summary ---")
        print(e)


async def run_pipeline():
    # Step 1: Crawl the web application
    print("--- Step 1: Starting Web Application Crawl ---")
    crawler = IntelligentCrawler()
    crawled_data = await crawler.explore()
    if not crawled_data:
        print("Crawling failed or returned no data. Exiting.")
        return

    # Step 2: Initialize the AI Summarizer
    print("\n--- Step 2: Initializing AI Summarizer ---")
    summarizer = TextSummarizer()

    # Step 3: Process data: Build graph and summarize each page individually
    print("\n--- Step 3: Processing and Summarizing Individual Pages ---")
    site_graph = nx.DiGraph()
    final_data = {}

    for url, data in crawled_data.items():
        print(f"Processing: {url}")
        site_graph.add_node(url)
        for link in data["links"]:
            if link in crawled_data:
                site_graph.add_edge(url, link)
        
        # Get the summary for this single page
        summary = summarizer.summarize_page(data["text"], url)
        
        final_data[url] = {
            "summary": summary,
            "raw_text": data["text"],
            "outgoing_links": data["links"]
        }
    
    # Save the intermediate structured data
    with open(config.STRUCTURED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)
    print(f"\n✅ Successfully saved detailed page data to: {config.STRUCTURED_DATA_FILE}")

    with open(config.GRAPH_FILE, "wb") as f:
        pickle.dump(site_graph, f)
    print(f"✅ Successfully saved site flow graph to: {config.GRAPH_FILE}")

    # --- NEW FINAL STEP ---
    # Now that we have all the page summaries, generate the final user guide.
    await generate_flow_summary(final_data, summarizer)

    print("\n--- Pipeline Finished Successfully! ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())