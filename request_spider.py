from bs4 import BeautifulSoup
from estela_requests import EstelaRequests
from estela_requests.estela_hub import EstelaHub
from urllib.parse import urljoin

url = "https://stackoverflow.com/questions/tagged/awk"
with EstelaRequests.from_estela_hub(EstelaHub.create_from_settings()) as wrapper:
    counter = 5
    def get_pages(act_url, i):
        response = wrapper.get(act_url)
        soup = BeautifulSoup(response.content, "html.parser")
        titles = [s.find("a", class_="s-link").get("href") for s in soup.find_all("div", class_="s-post-summary--content")]
        my_item = {
            "url": act_url,
            "titles": ",".join(titles[:3])
        }
        wrapper.send_item(my_item)

        next_link = soup.find('a', {'rel': 'next'})
        next_page = urljoin(act_url, next_link["href"])
        print(next_page)
        i += 1
        if counter < i:
            return
        get_pages(next_page, i)

    get_pages(url, 0)