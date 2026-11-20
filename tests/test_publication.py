"""Regression checks for the buyer-facing publication, without an external browser."""
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.home = (ROOT / "docs/index.html").read_text()
        self.main = self.home.split('<main id="main">', 1)[1].split('</main>', 1)[0]

    def test_one_headline_then_five_product_cards(self):
        self.assertEqual(len(re.findall(r'<h1\b', self.main)), 1)
        self.assertLess(self.main.index('<h1'), self.main.index('id="shop"'))
        self.assertEqual(self.main.count('<article class="shop-card">'), 5)
        self.assertIn('shop-grid-tools', self.main)

    def test_research_is_reachable_but_not_a_homepage_dashboard(self):
        self.assertNotIn('id="roadmap"', self.main)
        self.assertNotIn('class="tcount', self.main)
        for target in ('suggestions.html', 'questions.html', 'flagged.html', 'measurement.html', 'review.html'):
            self.assertIn(f'href="{target}"', self.home.split('<footer>', 1)[1])

    def test_native_navigation_and_disclosure_on_every_published_page(self):
        for path in (ROOT / 'docs').rglob('*.html'):
            text = path.read_text()
            with self.subTest(page=path.name):
                self.assertEqual(text.count('<div class="nav-group">'), 1)
                self.assertEqual(text.count('<details class="nav-menu">'), 3)
                self.assertLess(text.index('As an Amazon Associate I earn from qualifying purchases.'), text.index('<main'))
                self.assertIn('As an Amazon Associate I earn from qualifying purchases.', text.split('<footer>', 1)[1])

    def test_every_card_has_a_paid_sponsored_tagged_destination(self):
        cards = re.findall(r'<article class="shop-card">(.*?)</article>', self.main, re.S)
        for card in cards:
            self.assertIn('Paid link. As an Amazon Associate I earn from qualifying purchases.', card)
            self.assertIn('rel="sponsored noopener noreferrer"', card)
            self.assertRegex(card, r'https://www.amazon.com/dp/B[A-Z0-9]{9}\?tag=shopnow047c-20')

    def test_artwork_not_presented_as_a_product_photo_or_test(self):
        self.assertIn('Editorial illustration—not a product or test photo.', self.main)
        self.assertIn('Listing-based guides, not hands-on reviews.', self.main)
        self.assertIn('countertop-editorial.jpg', self.main)
        self.assertTrue((ROOT / 'docs/countertop-editorial.jpg').exists())

    def test_measurement_disabled_until_permanent_host_is_configured(self):
        self.assertIn('<meta name="zone4-measure-endpoint" content="">', self.home)
        measurement = (ROOT / 'docs/measurement.html').read_text()
        self.assertIn('Not hosted.', measurement)
        self.assertIn('not unique people', measurement)
        self.assertIn('90-day', measurement)


if __name__ == '__main__':
    unittest.main()
