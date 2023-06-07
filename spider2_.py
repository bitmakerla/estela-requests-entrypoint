from estela_requests.requests_wrapper import EstelaWrapper
from bs4 import BeautifulSoup

spider_name = "bbc_news"
def scrape_news():
    requests = EstelaWrapper()
    url = "https://www.bbc.com/news"  # URL of BBC News

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the news article elements on the page
        articles = soup.find_all("div", class_="gs-c-promo")

        # Iterate over the articles and extract the title and URL
        for article in articles:
            title = article.find("h3").text.strip()
            article_url = article.find("a")["href"]
            item = {
                "title": title,
                "url": article_url,
            }
            print("Item found : %s" % item)
            requests.send_item(item)
        requests.call_after_session_middlewares()
    else:
        print("Failed to fetch news. Error:", response.status_code)
    

# Call the scraper function
scrape_news()
