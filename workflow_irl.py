from typing import List
import feedparser
from datetime import datetime
from time import mktime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import anthropic
import random

API_KEY = "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"
client = anthropic.Anthropic(api_key=API_KEY)

def complete(
    prompt: str, 
    sys_prompt: str = "",
    prefill: str = "",
    model_name: str = "claude-3-5-haiku-latest",
    temperature: float = 0.0,
    max_tokens: int = 4000,
    
):
    messages = [{"role": "user", "content": prompt}]
    if prefill != "":
        messages.append({"role": "assistant", "content": prefill})

    message = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        system=sys_prompt,
        messages=messages
    )
    return message.content[0].text

class RssItem:
    id: str
    title: str
    description: str
    url: str

class RssItemDetailed:
    def __init__(self, title, description, url, content, highlighted_quote):
        self.title = title
        self.description = description
        self.url = url
        self.content = content
        self.highlighted_quote = highlighted_quote
 
def articles_of(rss_link: str, start: str, end: str) -> Generator[RssItem, None, None]:    
    feed = feedparser.parse(rss_link)
    if isinstance(start, str): start = datetime.fromisoformat(start)
    if isinstance(end, str): end = datetime.fromisoformat(end)

    for entry in feed.entries:
        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
        if start <= pub_date <= end:
            item = RssItem()
            item.id = entry.id
            item.title = entry.title
            item.description = entry.get('description', '')
            item.url = entry.link
            yield item

def get_contents_from(items: List[RssItem], num_workers: int = 5) -> List[RssItemDetailed]:
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        def fetch_content(item: RssItem) -> RssItemDetailed:
            response = requests.get(item.url)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()
            return RssItemDetailed(
                title=item.title,
                description=item.description,
                url=item.url,
                content=content,
                highlighted_quote=""
            )

        results = executor.map(fetch_content, items)
        return results

def only_relevant_content(items: List[RssItem]) -> List[RssItem]:
    raise NotImplementedError("Not implemented")

def get_valuable_quote(item: RssItemDetailed) -> str:
    raise NotImplementedError("Not implemented")

def present_content(items: List[RssItemDetailed]) -> str:
    raise NotImplementedError("Not implemented")

example_rss_feeds = [
    "https://www.micahlerner.com/feed.xml",
    "https://distributed-computing-musings.com/rss"
]

def main():
    items = articles_of("https://www.theguardian.com/rss", "2025-03-20", "2025-03-21")
    filtered_items = only_relevant_content(items)
    contents = list(get_contents_from(filtered_items))

    # Randomly select 10% of the filtered items, and get quote
    num_samples = max(1, int(len(contents) * 0.1))
    random_indexes = random.sample(range(len(contents)), num_samples)
    for idx in random_indexes:
        contents[idx].highlighted_quote = get_valuable_quote(contents[idx])

    # Present the content
    output = present_content(contents)
    print(output)

if __name__ == "__main__":
    main()
