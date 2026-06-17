import unittest

from worldcup.scrape import parse_matches


HTML = """
<html><body>
<h3 id="Group_A">Group A</h3>
<div itemscope itemtype="http://schema.org/SportsEvent" class="footballbox">
  <div class="fleft"><time>
    <div class="fdate">June&nbsp;11,&nbsp;2026<span style="display:none"><span class="bday">2026-06-11</span></span></div>
    <div class="ftime">8:00&nbsp;p.m. UTC-6</div>
  </time></div>
  <table class="fevent"><tr>
    <th class="fhome"><span itemprop="name">Mexico</span></th>
    <th class="fscore"><a>2–0</a></th>
    <th class="faway"><span itemprop="name">South Africa</span></th>
  </tr></table>
  <div class="fright"><span itemprop="name address">Mexico City Stadium, Mexico City</span></div>
</div>
<h3 id="Round_of_32">Round of 32</h3>
<div itemscope itemtype="http://schema.org/SportsEvent" class="footballbox">
  <div class="fleft"><time>
    <div class="fdate">June&nbsp;28,&nbsp;2026<span style="display:none"><span class="bday">2026-06-28</span></span></div>
    <div class="ftime">3:00&nbsp;p.m. UTC-4</div>
  </time></div>
  <table class="fevent"><tr>
    <th class="fhome"><span itemprop="name">Runner-up Group A</span></th>
    <th class="fscore"><a>Match 73</a></th>
    <th class="faway"><span itemprop="name">Runner-up Group B</span></th>
  </tr></table>
  <div class="fright"><span itemprop="name address">MetLife Stadium, East Rutherford</span></div>
</div>
</body></html>
"""


class ScrapeTest(unittest.TestCase):
    def test_parse_matches(self):
        matches = parse_matches(HTML)

        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["stage"], "Group A")
        self.assertEqual(matches[0]["time"], "03:00")
        self.assertEqual(matches[0]["score"], "2-0")
        self.assertEqual(matches[0]["status"], "played")
        self.assertEqual(matches[0]["winner"], "team_1")
        self.assertEqual(matches[1]["stage"], "Round of 32")
        self.assertEqual(matches[1]["match_number"], 73)
        self.assertEqual(matches[1]["status"], "scheduled")


if __name__ == "__main__":
    unittest.main()
