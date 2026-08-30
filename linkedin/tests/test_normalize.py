"""Tests for LinkedIn URL canonicalization.

Cases are drawn from real portal values so the suite fails if the assumptions
about the live data ever stop holding.
"""

import pytest

from qbs_linkedin.normalize import (
    UrlError,
    canonical_url,
    choose_profile_url,
    extract_slug,
    looks_mojibake,
    same_profile,
    slug_matches_name,
)


class TestCanonicalUrl:
    @pytest.mark.parametrize("raw", [
        "https://linkedin.com/in/shawnpetersonquantum",
        "https://www.linkedin.com/in/shawnpetersonquantum",
        "https://www.linkedin.com/in/ShawnPetersonQuantum/",
        "linkedin.com/in/shawnpetersonquantum?trk=nav",
        "http://linkedin.com/in/shawnpetersonquantum#about",
    ])
    def test_all_forms_collapse_to_one(self, raw):
        assert canonical_url(raw) == "https://linkedin.com/in/shawnpetersonquantum"

    def test_matches_the_portals_dominant_form(self):
        # 94.9% of stored values are bare-host. Canonicalizing to www would
        # fail to match almost every existing record.
        assert canonical_url("https://www.linkedin.com/in/x").startswith(
            "https://linkedin.com/in/"
        )

    def test_rejects_non_profile_urls(self):
        with pytest.raises(UrlError):
            canonical_url("https://linkedin.com/company/quantum")
        with pytest.raises(UrlError):
            canonical_url(None)

    def test_rejects_mojibake_rather_than_writing_an_unmatchable_key(self):
        with pytest.raises(UrlError, match="double-encoded"):
            canonical_url("https://linkedin.com/in/hervã©-amar-24722650")


class TestMojibake:
    def test_detects_live_corrupted_values(self):
        assert looks_mojibake("hervã©-amar-24722650")

    def test_accepts_correctly_encoded_accents(self):
        assert not looks_mojibake("hervé-amar-24722650")
        assert not looks_mojibake("jose-garcia-123")


class TestSameProfile:
    def test_host_form_does_not_break_equality(self):
        assert same_profile(
            "https://www.linkedin.com/in/jim-becker-a647a130",
            "https://linkedin.com/in/jim-becker-a647a130",
        )

    def test_different_people_are_not_equal(self):
        assert not same_profile(
            "https://linkedin.com/in/jim-becker-a647a130",
            "https://linkedin.com/in/margie-becker-267034a",
        )

    def test_missing_values(self):
        assert not same_profile(None, "https://linkedin.com/in/x")


class TestSlugMatchesName:
    @pytest.mark.parametrize("slug,first", [
        ("jim-becker-a647a130", "Jim"),
        ("richard-lynch-2918b431", "Dick"),      # nickname -> full
        ("dick-lynch-782730180", "Richard"),     # full -> nickname
        ("mike-helland-9a93a81b8", "Michael"),
        ("shawnpetersonquantum", "Shawn"),       # no separators
    ])
    def test_accepts_the_right_person(self, slug, first):
        assert slug_matches_name(slug, first)

    @pytest.mark.parametrize("slug,first,last", [
        ("pmkelley", "Patrick", "Kelley"),       # initials style, real row
        ("nphillips3616", "Nathan", "Phillips"), # initials style, real row
        ("riporter", "Rick", "Porter"),          # real row
    ])
    def test_accepts_initial_style_slugs(self, slug, first, last):
        # A first-name-only check drops every prospect using this slug style.
        assert slug_matches_name(slug, first, last)

    @pytest.mark.parametrize("slug,first,last", [
        ("margie-becker-267034a", "Jim", "Becker"),
        ("alec-strohmaier-411a915", "Nan", "Strohmaier"),
        ("virginia-kelley-5223b563", "Patrick", "Kelley"),
    ])
    def test_surname_alone_never_admits_a_relative(self, slug, first, last):
        # Same surname, wrong first initial -- exactly the relative-mismatch
        # class that would send Jim's pitch to Margie.
        assert not slug_matches_name(slug, first, last)

    @pytest.mark.parametrize("slug,first", [
        ("margie-becker-267034a", "Jim"),        # spouse, real portal row
        ("alec-strohmaier-411a915", "Nan"),      # relative, real portal row
        ("elvira-perez-5640b1227", "Froy"),      # relative, real portal row
        ("aisling-kerins-9b411861", "Craig"),    # bad enrichment, real row
    ])
    def test_rejects_the_wrong_person(self, slug, first):
        assert not slug_matches_name(slug, first)

    def test_missing_inputs_never_pass(self):
        assert not slug_matches_name(None, "Jim")
        assert not slug_matches_name("jim-becker", None)
        assert not slug_matches_name("jim-becker", "   ")


class TestChooseProfileUrl:
    def test_agreeing_urls_resolve_cleanly(self):
        url, problem = choose_profile_url(
            "https://linkedin.com/in/jim-becker-a647a130",
            "https://www.linkedin.com/in/jim-becker-a647a130",
            "Jim",
        )
        assert url == "https://linkedin.com/in/jim-becker-a647a130"
        assert problem is None

    def test_name_disambiguates_a_conflict(self):
        # Real row: hs_linkedin_url points at the contact's relative.
        url, problem = choose_profile_url(
            "https://linkedin.com/in/jim-becker-a647a130",
            "https://linkedin.com/in/margie-becker-267034a",
            "Jim",
        )
        assert url == "https://linkedin.com/in/jim-becker-a647a130"
        assert problem is None

    def test_unique_property_is_not_assumed_authoritative(self):
        # Real row: the *unique* property holds the wrong person and
        # hs_linkedin_url is correct.
        url, problem = choose_profile_url(
            "https://linkedin.com/in/virginia-kelley-5223b563",
            "https://linkedin.com/in/pmkelley",
            "Patrick", "Kelley",
        )
        assert url == "https://linkedin.com/in/pmkelley"
        assert problem is None

    def test_first_name_wins_over_a_relatives_slug(self):
        # Real row. "froycperez" contains the first name; "elvira-perez" is a
        # relative matched on surname. The first name settles it.
        url, problem = choose_profile_url(
            "https://linkedin.com/in/froycperez",
            "https://linkedin.com/in/elvira-perez-5640b1227",
            "Froy", "Perez",
        )
        assert url == "https://linkedin.com/in/froycperez"
        assert problem is None

    def test_undecidable_conflict_skips_rather_than_guesses(self):
        # Neither slug carries the first name and neither starts with "c".
        url, problem = choose_profile_url(
            "https://linkedin.com/in/aisling-kerins-9b411861",
            "https://linkedin.com/in/tmrosen-9b41",
            "Craig", "Rosenstein",
        )
        assert url is None
        assert "conflicting" in problem

    def test_no_url_at_all(self):
        url, problem = choose_profile_url(None, None, "Jim")
        assert url is None
        assert "no LinkedIn URL" in problem


class TestSlugMatchingAtScale:
    """Cases from the live list-5243 run (1,136 contacts).

    A first-name-only check skipped 31 of them; most were this person under a
    short form, an accent, or a surname-led slug. Each row here is a real
    portal contact.
    """

    @pytest.mark.parametrize("slug,first,last", [
        ("pradog", "Gabriel", "Prado"),                 # surname + initial
        ("smithm432", "Matthew", "Smith"),              # surname-led
        ("barnesphil", "Philip", "Barnes"),             # surname-led
        ("jbbattaglia", "Ben", "Battaglia"),            # initials + surname
        ("sbhagcha", "Sumit", "Bhagchandani"),          # initial + truncated
        ("kgosser", "Kris", "Gösser"),                  # accent folded
        ("lizchasse", "Elizabeth", "Chasse"),           # Liz
        ("drew-detzler-8863559a", "Andrew", "Detzler"), # Drew
        ("nickz1", "Nicholas", "Zgorski"),              # Nick
        ("anthonyroy", "Tony", "Roy"),                  # Tony -> Anthony
        ("nicolemstmartin", "Nikki", "St.Martin"),      # Nikki -> Nicole
        ("julietin", "Julieta", "Alvarado"),            # first-name prefix
        ("jessgmarketing", "Jessica", "Garrett"),       # prefix in brand slug
    ])
    def test_recovers_real_contacts(self, slug, first, last):
        assert slug_matches_name(slug, first, last)

    @pytest.mark.parametrize("slug,first,last", [
        # Wrong person — the expensive failure. Messaging one of these sends
        # a cold pitch to someone's relative under Shawn's name.
        ("margie-becker-267034a", "Jim", "Becker"),
        ("alec-strohmaier-411a915", "Nan", "Strohmaier"),
        ("virginia-kelley-5223b563", "Patrick", "Kelley"),
        ("elvira-perez-5640b1227", "Froy", "Perez"),
        ("aisling-kerins-9b411861", "Craig", "Rosenstein"),
        ("kerstin-topham-30b32971", "Michael", "Murdock"),
        ("am-hernandez", "Angela", "Cipriani"),
        # Brand slugs — genuinely ambiguous, belong in review not in a guess.
        ("techmarketingpro", "Scott", "Davis"),
        ("bbmktg", "Linda", "Ford"),
        ("navipsych", "Stephanie", "Camp"),
        ("innovationinaction", "Bill", "Evans"),
    ])
    def test_never_admits_the_wrong_person(self, slug, first, last):
        assert not slug_matches_name(slug, first, last)

    def test_short_first_names_do_not_prefix_match(self):
        # "jim"[:4] would be "jim" — three characters is not evidence, and a
        # loose prefix rule here is what would let "margie" through.
        assert not slug_matches_name("jimenez-corp", "Jim", "Becker")
