import os
import asyncio
from playwright.async_api import async_playwright
from google.generativeai import configure, GenerativeModel
import chromadb
from chromadb.utils import embedding_functions
import logging
from dotenv import load_dotenv # New import

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY not found in .env or environment variables. Please set it.")
    exit(1)

configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL_NAME = "gemini-1.5-flash"

# ChromaDB Configuration
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "book_chapters"
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


# --- Utility Functions ---
def get_gemini_model():
    """Returns an initialized Gemini GenerativeModel."""
    return GenerativeModel(GEMINI_MODEL_NAME)

def store_content_in_chroma(collection, content_id, content_text, version_type="original"):
    """Stores content in ChromaDB."""
    try:
        collection.add(
            documents=[content_text],
            metadatas=[{"id": content_id, "version_type": version_type}],
            ids=[content_id]
        )
        logging.info(f"Content ID '{content_id}' ({version_type}) stored in ChromaDB.")
    except Exception as e:
        logging.error(f"Error storing content '{content_id}' in ChromaDB: {e}")

async def semantic_search_chroma(collection, query_text, n_results=1):
    """Performs semantic search in ChromaDB."""
    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
        logging.info(f"Semantic search for '{query_text}' completed.")
        return results
    except Exception as e:
        logging.error(f"Error during semantic search: {e}")
        return None

# --- Main Workflow Functions ---

def ensure_directory(path):
    if os.path.isfile(path):
        os.remove(path)
    if not os.path.exists(path):
        os.makedirs(path)

async def scrape_and_screenshot(url: str, output_dir: str = "screenshots"):
    """Scrapes content from a URL and takes a screenshot."""
    ensure_directory(output_dir)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            logging.info(f"Navigating to {url}...")
            await page.goto(url, wait_until='networkidle')
            screenshot_path = os.path.join(output_dir, "scraped_page.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logging.info(f"Screenshot saved to {screenshot_path}")

            # Extract main content - adjust selectors if needed for different websites
            content_elements = await page.query_selector_all('div.mw-parser-output p')
            if not content_elements:
                content_elements = await page.query_selector_all('body p')

            scraped_text = "\n".join([await el.inner_text() for el in content_elements])
            logging.info(f"Scraped {len(scraped_text)} characters from the page.")

            await browser.close()
            return scraped_text

        except Exception as e:
            logging.error(f"Error during scraping or screenshot: {e}")
            await browser.close()
            return None

async def ai_spin_chapter(original_text: str, current_iteration: int, model: GenerativeModel):
    """Uses Gemini to "spin" or rewrite a chapter."""
    if not original_text:
        return None

    prompt = (
        f"You are an AI Writer. Rewrite the following chapter text, focusing on creating a more engaging "
        f"narrative style. Keep the core information but rephrase and expand where appropriate. "
        f"This is iteration {current_iteration}. Only provide the rewritten text.\n\n"
        f"Original Chapter:\n{original_text}"
    )

    try:
        logging.info(f"Sending text to Gemini for spinning (Iteration {current_iteration})...")
        response = await model.generate_content_async(prompt)
        spun_text = response.text
        logging.info(f"Gemini spinning complete. Generated {len(spun_text)} characters.")
        return spun_text
    except Exception as e:
        logging.error(f"Error during AI spinning: {e}")
        return None

async def ai_review_chapter(chapter_text: str, model: GenerativeModel):
    """Uses Gemini to review a spun chapter."""
    if not chapter_text:
        return None

    prompt = (
        f"You are an AI Reviewer. Analyze the following chapter text for clarity, coherence, grammar, "
        f"and engagement. Provide constructive feedback to improve it. Start with a summary of its strengths "
        f"and then list specific areas for improvement. Focus on the content itself, not just grammar.\n\n"
        f"Chapter to Review:\n{chapter_text}"
    )

    try:
        logging.info("Sending chapter to Gemini for AI review...")
        response = await model.generate_content_async(prompt)
        review_text = response.text
        logging.info("Gemini AI review complete.")
        return review_text
    except Exception as e:
        logging.error(f"Error during AI review: {e}")
        return None

async def human_in_the_loop_feedback(ai_generated_text: str, chapter_id: str, chroma_collection):
    """Simulates human interaction for review and editing."""
    print("\n--- Human-in-the-Loop Review ---")
    print("AI Generated Chapter:\n")
    print(ai_generated_text)
    print("\n-------------------------------\n")

    while True:
        action = input("Enter 'accept', 'edit', or 'reject' this chapter: ").lower().strip()
        if action == 'accept':
            logging.info(f"Human accepted chapter {chapter_id}. Storing as 'final'.")
            store_content_in_chroma(chroma_collection, f"{chapter_id}_final", ai_generated_text, "final")
            return ai_generated_text
        elif action == 'edit':
            print("\nPlease provide your edits. Enter 'DONE' on a new line when finished.")
            edited_lines = []
            while True:
                line = input()
                if line.strip().upper() == 'DONE':
                    break
                edited_lines.append(line)
            human_edited_text = "\n".join(edited_lines)
            logging.info(f"Human edited chapter {chapter_id}. Storing as 'human_edited'.")
            store_content_in_chroma(chroma_collection, f"{chapter_id}_human_edited", human_edited_text, "human_edited")
            print("\n--- Edited Chapter Preview ---")
            print(human_edited_text)
            print("------------------------------\n")
            return human_edited_text
        elif action == 'reject':
            logging.warning(f"Human rejected chapter {chapter_id}. Ending workflow for this chapter.")
            return None
        else:
            print("Invalid input. Please enter 'accept', 'edit', or 'reject'.")

async def main():
    target_url = "https://en.wikisource.org/wiki/The_Gates_Of_Morning/Book_1/Chapter_1"
    chapter_id_base = "gates_of_morning_ch1"
    num_iterations = 2

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding_function)
        logging.info(f"ChromaDB collection '{COLLECTION_NAME}' ready.")
    except Exception as e:
        logging.error(f"Failed to initialize ChromaDB: {e}")
        return

    gemini_model = get_gemini_model()

    # 1. Scrape and Screenshot
    original_chapter_text = await scrape_and_screenshot(target_url)
    if not original_chapter_text:
        logging.error("Failed to scrape original content. Exiting.")
        return

    store_content_in_chroma(collection, f"{chapter_id_base}_original", original_chapter_text, "original")
    current_chapter_text = original_chapter_text

    # 2. Iterative AI Spin and Human-in-the-Loop
    for i in range(1, num_iterations + 1):
        logging.info(f"\n--- Starting Iteration {i} ---")
        ai_spun_text = await ai_spin_chapter(current_chapter_text, i, gemini_model)
        if not ai_spun_text:
            logging.error(f"AI spinning failed in iteration {i}. Exiting loop.")
            break

        store_content_in_chroma(collection, f"{chapter_id_base}_ai_spun_iter_{i}", ai_spun_text, f"ai_spun_iter_{i}")

        ai_review_feedback = await ai_review_chapter(ai_spun_text, gemini_model)
        if ai_review_feedback:
            print("\n--- AI Reviewer Feedback ---")
            print(ai_review_feedback)
            print("----------------------------\n")

        human_decision_text = await human_in_the_loop_feedback(ai_spun_text, f"{chapter_id_base}_iter_{i}", collection)
        if human_decision_text:
            current_chapter_text = human_decision_text
        else:
            logging.warning(f"Human rejected chapter in iteration {i}. Ending workflow.")
            break

    # 3. Demonstrate Semantic Search (using ChromaDB)
    print("\n--- Demonstrating Semantic Search ---")
    search_query = "What happens to the protagonist in the beginning?"
    search_results = await semantic_search_chroma(collection, search_query)

    if search_results and search_results['documents']:
        print(f"Semantic search results for '{search_query}':")
        for j, doc in enumerate(search_results['documents']):
            metadata = search_results['metadatas'][j][0]
            distance = search_results['distances'][j][0]
            print(f"  Result {j+1} (Distance: {distance:.2f}):")
            print(f"    ID: {metadata['id']}, Version Type: {metadata['version_type']}")
            print(f"    Content Snippet: {doc[:200]}...")
            print("-" * 20)
    else:
        print(f"No semantic search results found for '{search_query}'.")

    logging.info("\nAutomated Book Publication Workflow simulation complete.")

if __name__ == "__main__":
    asyncio.run(main())