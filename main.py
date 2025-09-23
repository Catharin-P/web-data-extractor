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
    Takes all the crawled data (including raw text) and asks the AI
    to generate a detailed, actionable user flow guide.
    """
    print("\n" + "="*60)
    print("Step 4: Generating Detailed User Flow Guide")
    print("="*60)

    # 1. Prepare the input data for the AI.
    # THIS IS THE KEY CHANGE: We are now including the FULL RAW TEXT of each page.
    app_map_string = "Here is a map of the web application, with each page's URL and its full, raw text content:\n\n"
    for url, data in final_data.items():
        # We only include the most relevant pages in the prompt to stay within token limits
        # and focus the AI on the core user journey.
        if url.endswith(('/home', '/new-project', '/saved-projects', '/my-orders', '/rekraft', '/support')):
            app_map_string += f"--- Page URL: {url} ---\n"
            app_map_string += f"Raw Text Content of this page:\n\"\"\"\n{data.get('raw_text', 'No text found.')}\n\"\"\"\n\n"

    # 2. Define the powerful, detailed final prompt
    system_prompt = (
        "You are an expert technical writer and product onboarding specialist. Your task is to create a detailed user guide for a new user "
        "by analyzing the raw text content of several key pages from a web application. Your tone should be helpful, clear, and encouraging."
    )
    user_prompt = (
        f"Based on the raw text content from the application pages provided below, please write a comprehensive user flow guide. "
        f"Structure the guide as a step-by-step walkthrough of a typical user journey, starting from the '/home' page.\n\n"
        f"For each major page in the flow (like Home, New Project, Saved Projects), please create two distinct sections:\n"
        f"1. **What You Can See:** Describe the key information, lists, data, and sections visible on the page. For example, mention lists of projects, user information, buttons, etc.\n"
        f"2. **What You Can Do:** Describe the primary actions the user can take on this page. For example, 'Create a new project', 'View project details', 'Raise a support ticket', 'Generate a render', etc.\n\n"
        f"Use Markdown for clear formatting (headings, subheadings, bold text, and bullet points) to make the guide easy to read.\n\n"
        f"--- RAW PAGE DATA ---\n{app_map_string}"
    )

    # 3. Call the AI
    try:
        if not summarizer.client:
            print("OpenAI client not available. Skipping flow summary.")
            return

        print("Sending detailed application map to GPT-4o-mini for final analysis...")
        completion = summarizer.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.4,
            max_tokens=2500, # Allow for a very long and detailed guide
        )
        flow_summary = completion.choices[0].message.content.strip()

        # 4. Display and save the result
        print("\n--- DETAILED WEB APP USER GUIDE ---")
        print(flow_summary)
        print("-----------------------------------")

        with open("detailed_user_guide.md", "w", encoding="utf-8") as f:
            f.write(flow_summary)
        print("\n✅ Successfully saved detailed user guide to: detailed_user_guide.md")

    except Exception as e:
        print("\n--- ERROR Generating Final Flow Summary ---")
        print(traceback.format_exc())


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

    # Step 3: Process data and create the initial JSON file
    print("\n--- Step 3: Processing and Summarizing Individual Pages ---")
    final_data = {}
    for url, data in crawled_data.items():
        print(f"Processing: {url}")
        # Get a quick summary for the JSON file (optional but good for data checking)
        summary = summarizer.summarize_page(data["text"], url)
        final_data[url] = {
            "summary": summary,
            "raw_text": data["text"],
            "outgoing_links": data["links"]
        }
    
    with open(config.STRUCTURED_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4)
    print(f"\n✅ Successfully saved detailed page data to: {config.STRUCTURED_DATA_FILE}")

    # (Saving the graph file is omitted for brevity but can be added back if needed)

    # --- NEW FINAL STEP ---
    await generate_flow_summary(final_data, summarizer)

    print("\n--- Pipeline Finished Successfully! ---")

if __name__ == "__main__":
    asyncio.run(run_pipeline())