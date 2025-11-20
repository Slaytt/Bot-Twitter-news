import asyncio
from tools.scraper import scrape_website

async def test_scraper():
    print("Testing scraper on https://www.lemonde.fr/")
    result = await scrape_website("https://www.lemonde.fr/")
    print("Result:")
    print(result)
    
    if "Example Domain" in result:
        print("\nSUCCESS: Scraper retrieved content correctly.")
    else:
        print("\nFAILURE: Scraper did not retrieve expected content.")

if __name__ == "__main__":
    asyncio.run(test_scraper())
