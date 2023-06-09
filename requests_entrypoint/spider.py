import requests
from bs4 import BeautifulSoup
from estela_requests.requests_wrapper import EstelaWrapper
from estela_requests.request_interfaces import RequestsInterface
from estela_queue_adapter.get_interface import get_producer_interface
from urllib.parse import urljoin

url = "https://stackoverflow.com/questions/tagged/awk"
crequests = RequestsInterface()
#producer = get_producer_interface()
wrapper = EstelaWrapper()

counter = 4
def get_pages(act_url, i):
    response = wrapper.get(act_url)
    soup = BeautifulSoup(response.content, "html.parser")
    titles = [s.find("a", class_="s-link").get("href") for s in soup.find_all("div", class_="s-post-summary--content")]
    my_item = {
        "url": act_url,
        "titles": titles
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
wrapper.call_after_session_middlewares()
