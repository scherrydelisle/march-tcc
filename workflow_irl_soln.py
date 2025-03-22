from typing import List
import feedparser
from datetime import datetime
from time import mktime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import anthropic
import random

API_KEY = "REPLACE ME"
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
 
def articles_of(rss_link, start, end):    
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


def get_contents_from(items, num_workers=5):
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        def fetch_content(item):
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

def only_relevant_content(items):
    contents = ""
    ids_to_items = {}
    for item in items:
        contents += f"<content id=\"{item.id}\" description=\"{item.description}\" url=\"{item.url}\"/>\n"
        ids_to_items[item.id] = item

    system_prompt = """
    You are a helpful assistant that filters out irrelevant content from my news feed.
    Only keep content that is relevant and seems interesting in area of financial market, 
    software technology, and new breakthrough science. Try to keep some political content as well, but only
    minimal. Keep only political content that is relevant to financial markets.
    """
    
    user_prompt = f"""
    Here are list of the contents: Contents are provided in the following format:
    <content id="id" description="description" url="url"/>

    Here is the list of contents:
    {contents}

    Return only the contents that are relevant to the user prompt. Do not preelude anything. Only
    return id of the content that is relevant. each id should be listed in a new line.

    <example>
    id123
    id456
    id789
    </example>
    """

    filtered_contents = complete(user_prompt, system_prompt)
    filtered_contents = filtered_contents.split("\n")

    filtered_items = []
    for content in filtered_contents:
        filtered_items.append(ids_to_items[content])

    return filtered_items

def get_valuable_quote(item):
    system_prompt = """
    You are a helpful editor at the news aggregator site. Your job is to find the most valuable quote
    from the content provided. The quote should be short and to the point.

    Here is the guideline of the newsletter editor, who will use your quote in the newsletter:
    * Divide things into small chunks
    * Variety is the spice of life
    * Keep your flow of ideas strong
    * Use microhumor
    * Use concrete examples
    """
    
    user_prompt = f"""
    Here is the content:
    {item.content}

    Return only the quote that is relevant to the user prompt. Do not preelude anything. Only
    return the quote.

    <example>
    As the market is volatile, we are seeing a lot of volatility in the market in the last few days.
    It is however, expected to settle down in the coming days, as the Saudi Arabia and Russia are
    expected to agree on the production levels.
    </example>
    """
    return complete(user_prompt, system_prompt)

def present_content(items):
    print("items", items)

    lttr_style = """
Climate/Environment

    'Travesty of Justice': Jury Finds Greenpeace Must Pay Over $660 Million in Dakota Access Pipeline Case Common Dreams
    CRYPTO MINING COMPANY AGREES TO SPEED CLEANUP OF ITS COAL ASH PILE Allegheny Front
    Billions needed to save forests, but funding fuelling their destruction, reveals UNDP report Down to Earth
    How To Build A Thousand-Year-Old Tree NOEMA

Pandemics

    New measles cases confirmed in 2 Prince George’s County residents who traveled internationally WBAL-TV
    USDA launches biosecurity steps for poultry producers, adds details on H7N9 avian flu detection CIDRAP

China?

    Chinese semiconductors and alternative paths to innovation High Capacity

Africa

    Causes of War New Left Review. On the Democratic Republic of the Congo.
    The Alliance of Sahel States Forges Ahead Black Agenda Report
"""

    contents = ""
    for item in items:
        contents += f"<content description=\"{item.description}\" url=\"{item.url}\" quote=\"{item.highlighted_quote}\"/>\n"    
    
    system_prompt = f"""
    You are a helpful assistant that creates a email newsletter in markdown format. You are
    given list of contents, with Url, title, description and optionally highlighted quote. You
    will also make snark remarks about the content, if warranted that it adds tension and humor
    in the content. 

    Here is the newsletter organization style to imitate:
    {lttr_style}

    Here is the guideline for writing:
    * Don't use markdown headings. Instead, use the category names to divide the content.
    * Don't include takeaway in the newsletter. The title should be a link.
    * Snark remarks, if any should be critique of the content - not pointed at the reader. Don't make any expositive comments. 
    * If you are including a quote, use the quote formatting of the markdown
    * Ensure there is a line break between category heading and listed contents.
    * Include publisher name in the article title within a parenthesis.
    """

    user_prompt = f"""
    Contents are provided in the following format: <content description="description" url="url" quote="quote"/>, where quote and description are optional.

    <example>
    <content description="Traffic noise triggers road rage among male Galapagos birds" url="https://www.theguardian.com/science/2025/mar/20/traffic-noise-triggers-road-rage-among-male-galapagos-birds"/>
    </example>

    <contents>
    {contents}
    </contents>
    """

    newsletter = complete(user_prompt, system_prompt)
    print("newsletter", newsletter)
    return newsletter

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
    present_content(contents)

if __name__ == "__main__":
    main()
