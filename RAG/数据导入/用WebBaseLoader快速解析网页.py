from bs4 import BeautifulSoup, SoupStrainer
from langchain_community.document_loaders import WebBaseLoader

page_url = "https://www.xiaohongshu.com/explore/69e7648f000000001a026d3a?xsec_token=ABXoHaUhYOBswdEtQzN56KZsv4ocqt7ZlSFbh5Bvb22rA=&xsec_source=pc_feed"

loader=WebBaseLoader(web_paths=[page_url])

docs=loader.load()

print(f'{docs[0].metadata}\n')
print(docs[0].page_content.strip())

print('-----'*50)

loader=WebBaseLoader(
    web_paths=[page_url],
    bs_kwargs={"parse_only": SoupStrainer(id="bodyContent")},
    bs_get_text_kwargs={",separator*":"I", "strip": True}
)

print(f'{docs[0].metadata}\n')
print(docs[0].page_content.strip())