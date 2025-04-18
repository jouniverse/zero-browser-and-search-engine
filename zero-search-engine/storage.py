import sqlite3
import pandas as pd


class DBStorage:
    def __init__(self):
        self.con = sqlite3.connect("links.db")
        self.setup_tables()

    def setup_tables(self):
        """
        Set up the tables for storing search results in the database.

        Tables created:
        - results
            - id INTEGER PRIMARY KEY
            - query TEXT
            - rank INTEGER
            - link TEXT
            - title TEXT
            - snippet TEXT
            - html TEXT
            - created DATETIME
            - relevance INTEGER
            - UNIQUE(query, link)

        """
        cur = self.con.cursor()
        results_table = r"""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY,
                query TEXT,
                rank INTEGER,
                link TEXT,
                title TEXT,
                snippet TEXT,
                html TEXT,
                created DATETIME,
                relevance INTEGER,
                UNIQUE(query, link)
            );
            """
        cur.execute(results_table)
        self.con.commit()
        cur.close()

    def query_results(self, query):
        """
        Query the database for results for a given query, and return as a DataFrame sorted by rank.

        Parameters
        ----------
        query : str
            The query to search for.

        Returns
        -------
        df : pandas.DataFrame
            The results of the query, sorted by rank.
        """
        df = pd.read_sql(
            "select * from results where query=? order by rank asc",
            self.con,
            params=[query],
        )
        return df

    def insert_row(self, values):
        """
        Insert a row into the database with the given values.

        Parameters
        ----------
        values : list
            A list of values for the row to be inserted, in the order of:
            [query, rank, link, title, snippet, html, created]

        Returns
        -------
        None
        """
        cur = self.con.cursor()
        try:
            cur.execute(
                "INSERT INTO results (query, rank, link, title, snippet, html, created) VALUES(?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            self.con.commit()
        except sqlite3.IntegrityError:
            pass
        cur.close()

    def update_relevance(self, query, link, relevance):
        """
        Update the relevance of a search result in the database.

        Parameters
        ----------
        query : str
            The query the result is for.
        link : str
            The link of the result.
        relevance : int
            The new relevance value.

        Returns
        -------
        None
        """
        cur = self.con.cursor()
        cur.execute(
            "UPDATE results SET relevance=? WHERE query=? AND link=?",
            [relevance, query, link],
        )
        self.con.commit()
        cur.close()
