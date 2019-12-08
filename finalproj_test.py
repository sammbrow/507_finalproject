import unittest
import finalproj_main as finproj

class TestDataSources(unittest.TestCase):

    def test_toppage_scraping(self):
        page_data = finproj.scrape_top_page()
        
        self.assertEqual(len(page_data[0]), 84)
        self.assertEqual(len(page_data[1]), 84)

    def test_pagelink_scraping(self):
        data  = finproj.scrape_page_for_links('https://uxdesign.cc/what-designing-for-seniors-has-taught-me-c9c8a1421e84?source=collection_category---4------1-----------------------')
        data2  = finproj.scrape_page_for_links('https://uxdesign.cc/why-you-should-forget-about-the-number-of-clicks-b80532475fae?source=collection_category---4------9-----------------------')

        self.assertEqual(len(data), 4)
        self.assertEqual(data[0][0], "all too well")
        self.assertEqual(len(data2), 0)
        self.assertEqual(data2, [])

    def test_phrases_scraping(self):
        data  = finproj.collect_for_phrases()

        self.assertGreater(len(data[1]), 150)

class TestDatabaseConstruction(unittest.TestCase):

    def test_database(self):
        finproj.initialize_db()
        finproj.fill_db()
        conn = finproj.sqlite3.connect(finproj.DBNAME)
        cur = conn.cursor()

        statement1 = []
        for item in cur.execute('''SELECT Title FROM Articles'''):
            statement1.append(item)

        statement2 = []
        for item in cur.execute('''SELECT Phrase FROM Phrases'''):
            statement2.append(item)

        self.assertEqual(len(statement1), 84)
        self.assertGreater(len(str(statement1[0])), 5)
        self.assertGreater(len(statement2), 150)
        self.assertGreater(len(str(statement2[0])), 5)

        conn.commit()
        conn.close()

class TestQueries_Processing(unittest.TestCase):

    def test_top_stories_func(self):
        finproj.initialize_db()
        finproj.fill_db()
        conn = finproj.sqlite3.connect(finproj.DBNAME)
        cur = conn.cursor()
        data = finproj.top_stories_func()

        self.assertEqual(len(data), 84)

        conn.commit()
        conn.close()

    def test_phrases_func(self):
        finproj.initialize_db()
        finproj.fill_db()
        conn = finproj.sqlite3.connect(finproj.DBNAME)
        cur = conn.cursor()
        data = finproj.phrases_func()

        self.assertGreater(len(data), 150)

        conn.commit()
        conn.close()

    def test_top_stories_results_func(self):
        finproj.initialize_db()
        finproj.fill_db()
        conn = finproj.sqlite3.connect(finproj.DBNAME)
        cur = conn.cursor()

        data = finproj.top_stories_results_func("design")
        self.assertGreater(len(data), 10)

        data2 = finproj.top_stories_results_func("folleyes")
        self.assertLessEqual(len(data2), 1)

        conn.commit()
        conn.close()

    def test_phrases_results_func(self):
        finproj.initialize_db()
        finproj.fill_db()
        conn = finproj.sqlite3.connect(finproj.DBNAME)
        cur = conn.cursor()

        data = finproj.phrases_results_func("design")
        self.assertGreater(len(data), 10)

        data2 = finproj.phrases_results_func("folleyes")
        self.assertLessEqual(len(data2), 1)

        conn.commit()
        conn.close()

# unittest.main()
if __name__ == "__main__":
	unittest.main(verbosity=2)
