import asyncio
from tools.scraper import scrape_website

async def test_scraper():
    print("Testing scraper on https://example.com...")
    result = await scrape_website("https://example.com")
    print("Result:")
    print(result)
    
    if "Example Domain" in result:
        print("\nSUCCESS: Scraper retrieved content correctly.")
    else:
        print("\nFAILURE: Scraper did not retrieve expected content.")

if __name__ == "__main__":
    asyncio.run(test_scraper())
