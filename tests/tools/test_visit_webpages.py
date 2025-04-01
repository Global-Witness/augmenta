import asyncio
import pytest
from augmenta.tools.visit_webpages import visit_webpages

async def main():
    # Test URLs - using some stable websites as examples
    urls = [
        'https://new.abb.com/uk',
    ]
    
    results = await visit_webpages(urls)
    
    # Print results in a readable format
    for result in results:
        print(f"\nURL: {result['url']}")
        print("Content:")
        print("-" * 40)
        print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())