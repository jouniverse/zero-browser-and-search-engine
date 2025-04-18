from bs4 import BeautifulSoup
from urllib.parse import urlparse
from settings import *

with open("blacklist.txt") as f:
    domains = set(f.read().split("\n"))


def tracker_urls(row):
    """
    Return the number of known trackers found in the given row of data.

    The function works by finding all <script> tags with a src attribute
    and all <a> tags with an href attribute. It then extracts the hostname
    from the src and href attributes and checks if the hostname is in the
    list of known tracker domains.

    Parameters
    ----------
    row : pandas Series
        A row of data containing an "html" column.

    Returns
    -------
    int
        The number of known trackers found in the given row of data.

    """
    soup = BeautifulSoup(row["html"])
    scripts = soup.find_all("script", {"src": True})
    srcs = [s.get("src") for s in scripts]

    links = soup.find_all("a", {"href": True})
    href = [l.get("href") for l in links]

    all_domains = [urlparse(s).hostname for s in srcs + href]
    return len([a for a in all_domains if a in domains])


def get_page_content(row):
    """
    Return the text content of the given row of data.

    The function works by parsing the HTML content of the given row of data
    and extracting all the text content.

    Parameters
    ----------
    row : pandas Series
        A row of data containing an "html" column.

    Returns
    -------
    str
        The text content of the given row of data.

    """
    soup = BeautifulSoup(row["html"])
    text = soup.get_text()
    return text


class Filter:
    def __init__(self, results):
        self.filtered = results.copy()

    def tracker_filter(self):
        """
        Filter results based on the presence of tracker URLs.

        The function works by counting the number of tracker URLs in each row
        of the given DataFrame and then adding this count to the "rank" column.
        The count is multiplied by two to have a greater impact on the ranking.

        The function also replaces rows with a high number of tracker URLs with
        a special value indicating that the row should be filtered out.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        tracker_count = self.filtered.apply(tracker_urls, axis=1)
        tracker_count[tracker_count > tracker_count.median()] = RESULT_COUNT
        self.filtered["rank"] += tracker_count * 2

    def content_filter(self):
        """
        Filter results based on the length of the content on each page.

        The function works by counting the number of words on each page and
        then adding this count to the "rank" column. The count is divided by
        the median count to normalise the values. Any page with a word count
        of less than half the median is given a special value indicating that
        the row should be filtered out.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        page_content = self.filtered.apply(get_page_content, axis=1)
        word_count = page_content.apply(lambda x: len(x.split(" ")))

        word_count /= word_count.median()
        word_count[word_count <= 0.5] = RESULT_COUNT
        word_count[word_count != RESULT_COUNT] = 0
        self.filtered["rank"] += word_count

    def filter(self):
        """
        Apply all filters to the given DataFrame.

        This function applies the tracker filter and the content filter to the
        given DataFrame. The filters are applied in this order, meaning that the
        tracker filter is applied first and the content filter is applied
        afterwards. The filtered DataFrame is then sorted by the rank column
        and the rank is rounded to the nearest integer.

        Parameters
        ----------
        None

        Returns
        -------
        filtered : DataFrame
            The filtered DataFrame.
        """
        self.tracker_filter()
        self.content_filter()
        self.filtered = self.filtered.sort_values("rank", ascending=True)
        self.filtered["rank"] = self.filtered["rank"].round()
        return self.filtered
