"""The navigation table, and every surface rendered from it.

EngineVerse's navigation used to be written out by hand in four places - the
desktop top bar, the five footer columns, the mobile bottom bar and the sitemap -
and each copy was edited on its own. They drifted until the bar said "Practice"
and the footer said "Practise", the bar said "Code" for /programming while the
footer said "Learn to code" for the same URL, the bottom bar highlighted two
items at once, about fifteen pages were reachable only from the footer, all 45
branch hubs had no inbound link at all, and the sitemap omitted /sheets and every
sheet slug.

``engineverse/navigation.py`` replaced the four copies with one table. These tests
are what keeps it that way: they assert the properties that were violated, so a
future edit that reintroduces a hand-written list fails here instead of shipping.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from engineverse import navigation


# ---------------------------------------------------------------------------
# The table itself
# ---------------------------------------------------------------------------

def test_every_destination_has_a_label_path_and_blurb():
    """A destination with no blurb renders an empty line in three different menus."""
    for dest in navigation.all_destinations():
        assert dest.label.strip(), f"{dest.path} has no label"
        assert dest.path.startswith("/"), f"{dest.label} has a relative path"
        assert dest.blurb.strip(), f"{dest.path} has no blurb"


def test_paths_are_unique_across_the_table():
    """Two destinations claiming one URL would fight over the active state."""
    paths = [dest.path for dest in navigation.all_destinations()]
    duplicates = {p for p in paths if paths.count(p) > 1}
    assert not duplicates, f"duplicated destination paths: {sorted(duplicates)}"


def test_labels_are_unique_within_a_menu():
    """A menu that lists the same word twice is unreadable."""
    for item in navigation.primary_nav(signed_in=True):
        labels = [child.label for child in item.children]
        duplicates = {label for label in labels if labels.count(label) > 1}
        assert not duplicates, f"{item.label} menu repeats {sorted(duplicates)}"


def test_a_path_can_be_listed_in_more_than_one_group():
    """Deliberate: the formula centre is both study material and revision material.

    Guarded here because de-duplication in all_destinations() is what makes the
    sitemap and the active-state lookups behave; if that ever stops happening the
    same URL would be exported twice and could win its own prefix contest.
    """
    assert navigation.find("/formulas") is not None
    groups = [
        section.label for section in navigation.all_sections()
        if any(d.path == "/formulas" for d in section.destinations)
    ]
    assert len(groups) > 1, "/formulas should appear under more than one group"
    assert len(list(navigation.all_destinations())) == len(
        {d.path for d in navigation.all_destinations()}
    )


def test_pattern_destinations_are_never_treated_as_pages():
    """/portfolio and /certificates are shapes, not URLs.

    Only /portfolio/{username} and /certificates/{verify_id} exist. Rendering the
    bare prefix as a link - in a breadcrumb or the sitemap - would be a 404.
    """
    for path in ("/portfolio", "/certificates"):
        dest = navigation.find(path)
        assert dest is not None and dest.pattern, f"{path} must be marked pattern"
        assert not dest.indexable, f"{path} must not be indexable"
        assert path not in navigation.indexable_paths()
        assert path not in navigation.indexable_paths(public_only=True)


def test_no_private_page_is_published():
    """A public sitemap must not name a page that belongs to one account."""
    private = {"/profile", "/settings", "/notifications", "/admin", "/today",
               "/streaks", "/revision", "/mistakes", "/onboarding"}
    published = set(navigation.indexable_paths())
    assert not (private & published), f"private pages in the sitemap: {sorted(private & published)}"


def test_public_only_excludes_everything_needing_an_account():
    """The static export renders anonymously, so it must not list gated pages."""
    for path in navigation.indexable_paths(public_only=True):
        dest = navigation.find(path)
        assert dest is None or not dest.signed_in, f"{path} needs an account"


# ---------------------------------------------------------------------------
# Owning a path: what makes active states and breadcrumbs derivable
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path,expected", [
    # A prefix must not swallow a sibling that merely starts with the same
    # letters, which is why matching happens on a segment boundary.
    ("/stream/computer-science", "/stream"),
    ("/streams", "/streams"),
    ("/practice", "/practice"),
    ("/practice/questions", "/practice/questions"),
    ("/practice/problems", "/practice/problems"),
    ("/practice/problems/two-sum", "/practice/problems"),
    ("/resources", "/resources"),
    ("/resources/offsite", "/resources/offsite"),
    ("/sheets/arrays-hashing", "/sheets"),
    ("/dpp/2026-10-13", "/dpp"),
    ("/dpp/archive", "/dpp/archive"),
    ("/topics/arrays", "/explore"),
    ("/subjects/dbms", "/explore"),
    ("/branches/aerospace", "/explore"),
    ("/roadmaps/gate-mechanical-path", "/roadmaps"),
    ("/programming/python", "/programming"),
    ("/projects/portfolio-website", "/projects"),
    ("/community/01ABC", "/community"),
])
def test_destination_for_claims_the_right_owner(path, expected):
    owner = navigation.destination_for(path)
    assert owner is not None, f"nothing owns {path}"
    assert owner.path == expected


def test_unknown_paths_have_no_owner():
    assert navigation.destination_for("/no-such-page") is None


# ---------------------------------------------------------------------------
# The bottom bar: exactly one item, and the right one
# ---------------------------------------------------------------------------

def test_bottom_bar_has_five_items():
    """Five is the budget on a phone; a sixth makes the labels unreadable."""
    assert len(navigation.mobile_nav()) == 5


@pytest.mark.parametrize("path", [
    "/", "/stream", "/stream/x", "/streams", "/explore", "/subjects/y",
    "/topics/z", "/branches/b", "/practice", "/practice/questions",
    "/practice/problems", "/practice/problems/a", "/sheets", "/sheets/a",
    "/projects", "/projects/p", "/programming", "/programming/py",
    "/formulas", "/roadmaps", "/revision", "/today", "/settings",
    "/community", "/resources", "/placements", "/nowhere",
])
def test_bottom_bar_highlights_at_most_one_item(path):
    """The bug this replaces: several items lit at once.

    "My stream" used to highlight on /explore, /subjects and /topics, and
    "Sheets" used to highlight on /projects, because each link tested its own
    overlapping prefixes independently. active_mobile() returns one label.
    """
    assert isinstance(navigation.active_mobile(path), (str, type(None)))


@pytest.mark.parametrize("path,expected", [
    ("/", "Home"),
    ("/stream/computer-science", "Stream"),
    ("/streams", "Stream"),
    # These three are the regressions: the catalogue belongs to Learn, not to the
    # stream tab, and projects belong to Code, not to Sheets.
    ("/explore", "Learn"),
    ("/subjects/dbms", "Learn"),
    ("/topics/arrays", "Learn"),
    ("/projects/portfolio-website", "Code"),
    ("/practice", "Practice"),
    ("/practice/questions", "Practice"),
    # /practice/problems sits under the Code group even though /practice also
    # matches it: longest prefix wins.
    ("/practice/problems/two-sum", "Code"),
    ("/sheets/arrays-hashing", "Code"),
    ("/programming/python", "Code"),
])
def test_bottom_bar_highlights_the_right_item(path, expected):
    assert navigation.active_mobile(path) == expected


def test_bottom_bar_labels_match_the_desktop_groups():
    """The phone and the desktop must not use different words for one thing."""
    desktop = {item.label for item in navigation.primary_nav()}
    for item in navigation.mobile_nav():
        if item.label in ("Home", "Stream"):
            continue
        assert item.label in desktop, f"bottom bar says {item.label!r}, the bar says {sorted(desktop)}"


# ---------------------------------------------------------------------------
# No disagreement between surfaces
# ---------------------------------------------------------------------------

def _label_by_href(signed_in: bool = True) -> dict[str, set[str]]:
    """Every *destination* label used for a URL, across every surface.

    Group labels are deliberately excluded: a group label is the name of a
    category ("Learn") and it links to that category's landing page, which also
    has its own destination label ("Explore subjects"). Two names for one URL
    across those two roles is the design, not drift - and it is asserted
    separately below.
    """
    found: dict[str, set[str]] = {}
    for item in navigation.primary_nav(signed_in):
        for child in item.children:
            found.setdefault(child.path, set()).add(child.label)
    for column in navigation.footer_columns(signed_in):
        for link in column.links:
            found.setdefault(link.path, set()).add(link.label)
    for section in navigation.index_sections(signed_in):
        for dest in section.destinations:
            found.setdefault(dest.path, set()).add(dest.label)
    return found


def test_one_url_has_one_label_everywhere():
    """The drift this module exists to prevent.

    /programming was "Code" in the bar and "Learn to code" in the footer;
    /revision was "Revise" in the bar and "Flashcards" in the footer. Every
    surface now reads the same string, because every surface reads this table.
    """
    offenders = {
        href: labels for href, labels in _label_by_href().items() if len(labels) > 1
    }
    assert not offenders, f"URLs with more than one label: {offenders}"


def test_group_labels_are_distinct():
    """Two groups called the same thing would make the bar ambiguous."""
    labels = [item.label for item in navigation.primary_nav()]
    assert len(labels) == len(set(labels)), f"repeated group labels: {labels}"
    headings = [column.heading for column in navigation.footer_columns()]
    assert len(headings) == len(set(headings)), f"repeated footer headings: {headings}"


def test_a_group_label_is_not_also_a_destination_label():
    """"Learn" and "Learn to code" one word apart was the original confusion.

    A group name and a destination name must not be near-duplicates pointing at
    different URLs, which is how the old footer ended up with "Learn" for
    /explore and "Learn to code" for /programming side by side.
    """
    groups = {item.label: item.href for item in navigation.primary_nav()}
    for dest in navigation.all_destinations():
        for label, href in groups.items():
            if dest.path == href:
                continue
            assert dest.label.lower() != label.lower(), (
                f"{dest.path} is labelled {dest.label!r}, the same as the group pointing at {href}"
            )


def test_the_footer_does_not_misspell_practice():
    headings = [column.heading for column in navigation.footer_columns()]
    assert "Practise" not in headings
    assert "Practice" in headings


def test_every_non_minor_destination_is_reachable_from_the_navigation():
    """About fifteen pages used to exist only in the footer, or nowhere.

    Anything a reader is meant to find must be in the top bar's menus or the
    footer - both of which are on every page - not only on a page they would have
    to already know about.
    """
    reachable: set[str] = set()
    for item in navigation.primary_nav():
        reachable.add(item.href)
        reachable.update(child.path for child in item.children)
    for column in navigation.footer_columns():
        reachable.update(link.path for link in column.links)
    reachable.update(d.path for d in navigation.account_destinations())

    missing = [
        dest.path for dest in navigation.all_destinations()
        if not dest.minor and not dest.pattern and dest.path not in reachable
    ]
    assert not missing, f"destinations no navigation surface links to: {missing}"


def test_the_index_page_lists_every_destination():
    """/resources is the page that answers 'what is actually on this site?'

    Pattern destinations are excluded on both sides: the index is a list of things
    to click, and /portfolio and /certificates are shapes rather than pages.
    """
    listed = {
        dest.path
        for section in navigation.index_sections()
        for dest in section.destinations
    }
    everything = {d.path for d in navigation.all_destinations() if not d.pattern}
    assert everything - listed == set(), f"missing from the index: {sorted(everything - listed)}"
    assert listed == everything, f"index lists paths that are not destinations: {sorted(listed - everything)}"


def test_signed_out_navigation_hides_gated_pages():
    """A signed-out visitor must not be shown links that only bounce to /login."""
    for item in navigation.primary_nav(signed_in=False):
        for child in item.children:
            assert not child.signed_in, f"{child.path} needs an account"
    for column in navigation.footer_columns(signed_in=False):
        for link in column.links:
            assert not link.signed_in, f"{link.path} needs an account"


def test_signed_out_group_labels_do_not_point_at_gated_landings():
    """Filtering the menu is not enough; the group label is a link too.

    Dropping the gated destinations while leaving the label on the gated landing
    page is how /revision and /today reached a signed-out reader as links whose
    only effect was a redirect to the sign-in form.
    """
    gated = {d.path for d in navigation.all_destinations() if d.signed_in}
    for item in navigation.primary_nav(signed_in=False):
        assert item.href not in gated, f"the {item.label} group points at gated {item.href}"
    for item in navigation.mobile_nav(signed_in=False):
        assert item.href not in gated, f"the {item.label} tab points at gated {item.href}"
    for section in navigation.index_sections(signed_in=False):
        assert section.landing not in gated, f"the {section.label} group points at gated {section.landing}"


def test_the_revise_group_falls_back_to_the_public_decks():
    """Members get their own schedule; everyone else gets the browsable decks."""
    signed_in = {i.label: i.href for i in navigation.primary_nav(True)}
    signed_out = {i.label: i.href for i in navigation.primary_nav(False)}
    assert signed_in["Revise"] == "/revision"
    assert signed_out["Revise"] == "/flashcards"


def test_a_group_with_no_public_landing_renders_a_heading_not_a_broken_link():
    """landing_for() answers "" rather than inventing a URL that 404s."""
    empty = navigation.Section(
        key="x", label="X", blurb="", landing="/settings",
        destinations=(navigation.Destination("Settings", "/settings", "s", signed_in=True),),
    )
    assert empty.landing_for(signed_in=False) == ""


def test_member_only_pages_are_not_offered_to_a_signed_out_reader():
    """/stream renders anonymously, so it is not gated - but it is not "mine".

    An anonymous request to /stream is redirected to whatever branch it falls
    back to, which is not what a link labelled "My stream" promises. Signed-out
    readers get "All streams" instead, in the bar, the menus, the mobile panel
    and the index.
    """
    stream = navigation.find("/stream")
    assert stream is not None and stream.member_only
    assert not stream.signed_in, "member_only is not the same claim as signed_in"

    offered = {
        dest.path
        for section in navigation.index_sections(signed_in=False)
        for dest in section.destinations
    }
    offered |= {item.href for item in navigation.primary_nav(signed_in=False)}
    offered |= {c.path for item in navigation.primary_nav(signed_in=False) for c in item.children}
    offered |= {item.href for item in navigation.mobile_nav(signed_in=False)}
    assert "/stream" not in offered, "a signed-out reader is being offered /stream"
    assert "/streams" in offered


def test_the_stream_group_is_relabelled_for_a_signed_out_reader():
    """"My stream" is a promise the site cannot keep without an account."""
    signed_in = {s.label for s in navigation.index_sections(True)}
    signed_out = {s.label for s in navigation.index_sections(False)}
    assert "My stream" in signed_in
    assert "My stream" not in signed_out
    assert "Streams" in signed_out


def test_a_breadcrumb_never_links_to_a_page_the_reader_cannot_open():
    """The trail is made of links, so it has to be audience-aware too.

    /stream/production used to breadcrumb through /stream for everybody. In the
    static export, which renders anonymously and has no /stream page, that was a
    link to a file that does not exist - and the exporter refuses to publish when
    it finds one.
    """
    gated = {d.path for d in navigation.all_destinations() if d.signed_in or d.member_only}
    for path in ("/stream/production", "/streams", "/sheets/arrays-hashing",
                 "/revision", "/explore", "/topics/arrays"):
        for crumb in navigation.breadcrumb_trail(path, "Leaf", signed_in=False):
            assert crumb.href not in gated, f"{path} trail links to gated {crumb.href}"


def test_a_dropped_member_only_level_keeps_its_group():
    """/stream/production still reads Home > Streams > Production Engineering."""
    trail = navigation.breadcrumb_trail("/stream/production", "Production", signed_in=False)
    assert [c.label for c in trail] == ["Home", "Streams", "Production"]
    assert trail[1].href == "/streams"


#: Pages that answer an anonymous request with a redirect to /login. These are
#: the ones a signed-out reader must never be offered, because the link's only
#: effect would be to bounce them.
GATED_PATHS = ("/mistakes", "/today", "/profile", "/settings",
               "/notifications", "/onboarding", "/admin")


def test_no_gated_url_is_offered_to_a_signed_out_reader(client, seeded):
    """End to end, on a real page, with anonymous browsing allowed.

    Note what is *not* in this list: /sheets, /revision, /placements, /streaks,
    /practice/questions and /practice/problems all render fine for a signed-out
    reader on an instance where sign-in is optional. Hiding those would have
    removed working pages from the public site and from the static export.
    """
    html = client.get("/explore").text
    for path in GATED_PATHS:
        assert f'href="{path}"' not in html, f"{path} is offered to a signed-out reader"


def test_a_signed_out_reader_is_still_offered_the_pages_they_can_open(client, seeded):
    """The other half of the same mistake, checked from the other direction."""
    html = client.get("/explore").text
    for path in ("/sheets", "/revision", "/placements", "/streaks",
                 "/practice/questions", "/practice/problems"):
        assert f'href="{path}"' in html, f"{path} renders anonymously but is hidden"


def test_signed_in_flags_match_what_the_application_actually_does(client, seeded):
    """The table is a claim about the app; this checks the claim.

    Six destinations were originally marked as needing an account because they
    are more useful with one - /sheets, /revision, /placements, /streaks and the
    two practice shelves. They all render fine anonymously when sign-in is
    optional. Marking them anyway hid working pages from signed-out readers and
    dropped them from the static export, which is how /placements ended up linked
    from 47 exported pages that did not exist.

    Anything that changes a page's gating must change this table with it, or this
    test fails and says which way the two disagree.
    """
    disagreements = []
    for dest in navigation.all_destinations():
        if dest.pattern:
            continue  # only /portfolio/{username} exists, not /portfolio
        response = client.get(dest.path, follow_redirects=False)
        location = response.headers.get("location", "")
        gated = response.status_code in (301, 302, 303, 307, 308) and "/login" in location
        if gated != dest.signed_in:
            disagreements.append((dest.path, dest.signed_in, response.status_code, location))
    assert not disagreements, (
        "navigation.signed_in disagrees with the application "
        "(path, table_says_needs_account, status, redirect): "
        f"{disagreements}"
    )


# ---------------------------------------------------------------------------
# Breadcrumbs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path,leaf,expected", [
    ("/", "", []),
    ("/explore", "", ["Home", "Explore subjects"]),
    ("/topics/arrays", "Arrays", ["Home", "Learn", "Arrays"]),
    ("/sheets/arrays-hashing", "Arrays", ["Home", "Code", "Practice sheets", "Arrays"]),
    ("/stream/computer-science", "CSE", ["Home", "My stream", "CSE"]),
    ("/mistakes", "", ["Home", "Practice", "Mistake notebook"]),
    ("/nowhere", "", ["Home"]),
])
def test_breadcrumb_trails(path, leaf, expected):
    trail = navigation.breadcrumb_trail(path, leaf)
    assert [crumb.label for crumb in trail] == expected


def test_breadcrumbs_never_repeat_a_url():
    """/topics/arrays would otherwise read Home > Learn > Explore subjects > ...

    with both "Learn" and "Explore subjects" linking to /explore.
    """
    for path in navigation.indexable_paths():
        trail = navigation.breadcrumb_trail(path, "Leaf")
        hrefs = [c.href for c in trail if c.href]
        assert len(hrefs) == len(set(hrefs)), f"{path} repeats a URL: {hrefs}"


def test_breadcrumbs_never_link_to_the_current_page():
    for path in navigation.indexable_paths():
        for crumb in navigation.breadcrumb_trail(path, "Leaf"):
            assert crumb.href != path, f"{path} links to itself in its own trail"


def test_only_the_last_crumb_can_be_the_current_one():
    """aria-current belongs on exactly one level, and only when it has no link."""
    for path in navigation.indexable_paths():
        trail = navigation.breadcrumb_trail(path, "Leaf")
        currents = [c for c in trail if c.is_current]
        assert len(currents) <= 1, f"{path} marks {len(currents)} levels current"
        if currents:
            assert trail[-1].is_current, f"{path} marks a middle level current"


def test_a_pattern_destination_never_becomes_a_link():
    """/portfolio/{username} must not produce a trail link to /portfolio."""
    trail = navigation.breadcrumb_trail("/portfolio/asha", "Asha")
    assert all(c.href != "/portfolio" for c in trail)
    assert [c.label for c in trail] == ["Home", "Public portfolio", "Asha"]


def test_extra_parents_insert_above_the_leaf():
    """A topic belongs to a subject as well as to the catalogue."""
    trail = navigation.breadcrumb_trail(
        "/topics/arrays", "Arrays", [("Data Structures", "/subjects/dsa")]
    )
    assert [c.label for c in trail] == ["Home", "Learn", "Data Structures", "Arrays"]
    assert trail[2].href == "/subjects/dsa"


def test_a_parent_that_repeats_the_level_above_is_dropped():
    trail = navigation.breadcrumb_trail(
        "/subjects/dsa", "DSA", [("Data Structures", "/subjects/dsa")]
    )
    hrefs = [c.href for c in trail if c.href]
    assert len(hrefs) == len(set(hrefs))


def test_a_long_leaf_is_truncated():
    """A 400-character thread title must not build a 400-character breadcrumb."""
    trail = navigation.breadcrumb_trail("/community/x", "t" * 400)
    assert len(trail[-1].label) <= 120


# ---------------------------------------------------------------------------
# Against the running application
# ---------------------------------------------------------------------------

def test_every_destination_path_serves_a_page(signed_in):
    """A navigation table that points at a 404 is worse than no table."""
    broken = []
    for dest in navigation.all_destinations():
        if dest.pattern:
            continue  # only /portfolio/{username} exists, not /portfolio
        response = signed_in.get(dest.path, follow_redirects=False)
        if response.status_code in (404, 405) or response.status_code >= 500:
            broken.append((dest.path, response.status_code))
    assert not broken, f"navigation points at broken pages: {broken}"


def test_the_rendered_top_bar_is_grouped_not_flat(signed_in):
    """Six grouped entries replace ten flat links."""
    html = signed_in.get("/explore").text
    assert 'class="mainnav"' in html
    groups = re.findall(r'class="navgroup(?: on)?"', html)
    flat = re.findall(r'class="navlink(?: on)?"', html)
    assert len(groups) + len(flat) <= 7, f"the bar has {len(groups) + len(flat)} entries"
    assert groups, "no grouped entries: the menus are gone"


def test_the_rendered_footer_headings_come_from_the_table(signed_in):
    """The footer's heading level is part of the page outline, not decoration.

    These were ``<h4>``, which meant a reader navigating by heading heard the
    page jump from an ``<h2>`` straight to a fourth-level heading - and because
    the footer is on every page, that skip was site-wide. ``.footer h2`` in the
    stylesheet keeps them looking the same.
    """
    html = signed_in.get("/explore").text
    footer = html.split('class="footer"', 1)[-1]
    headings = re.findall(r"<h2>([^<]+)</h2>", footer)
    expected = [column.heading for column in navigation.footer_columns()] + ["Account", "Tell us what's wrong"]
    assert headings == expected, f"footer headings {headings} != {expected}"


def test_the_rendered_bottom_bar_marks_one_item(signed_in):
    """And marks the *right* one: a topic belongs to Learn, not to the stream tab."""
    html = signed_in.get("/topics/arrays").text
    bottom = html.split('class="bottomnav"', 1)[-1].split("</nav>", 1)[0]
    assert bottom.count('aria-current="page"') == 1, "the bottom bar marks more than one page current"
    current = re.findall(r'<a href="([^"]+)"[^>]*aria-current="page"', bottom)
    assert current == ["/explore"], f"the highlighted tab points at {current}, expected /explore"


def test_the_rendered_bottom_bar_marks_projects_as_code(signed_in):
    """The other regression: "Sheets" used to light up while reading /projects."""
    html = signed_in.get("/projects").text
    bottom = html.split('class="bottomnav"', 1)[-1].split("</nav>", 1)[0]
    current = re.findall(r'<a href="([^"]+)"[^>]*aria-current="page"', bottom)
    assert current == ["/programming"], f"the highlighted tab points at {current}, expected /programming"


def test_deep_pages_render_a_breadcrumb(signed_in):
    """The thirty-seven templates that used to have no way back up."""
    for path, needle in [
        ("/topics/arrays", "Arrays"),
        ("/sheets/arrays-hashing", "Practice sheets"),
        ("/mistakes", "Mistake notebook"),
        ("/flashcards", "Public flashcards"),
        ("/videos", "Video library"),
        ("/books", "Reference books"),
    ]:
        html = signed_in.get(path).text
        assert 'aria-label="Breadcrumb"' in html, f"{path} has no breadcrumb"
        assert needle in html, f"{path} breadcrumb does not name {needle}"


def test_no_template_renders_a_second_breadcrumb(signed_in):
    """base.html draws the trail; a template drawing its own would show two."""
    for path in ("/topics/arrays", "/sheets/arrays-hashing", "/subjects/dbms",
                 "/projects/portfolio-website", "/stream/computer-science",
                 "/roadmaps/gate-mechanical-path", "/flashcards"):
        html = signed_in.get(path).text
        assert html.count('aria-label="Breadcrumb"') == 1, f"{path} renders two trails"


def test_the_sitemap_covers_every_indexable_page(client, seeded):
    """/sitemap.xml omitted /sheets and every sheet slug; both are in the table."""
    from xml.etree import ElementTree

    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locations = {
        node.text for node in ElementTree.fromstring(response.content).iter(f"{namespace}loc")
    }
    paths = {loc.split("//", 1)[-1].split("/", 1)[-1] for loc in locations}
    paths = {"/" + p if not p.startswith("/") else p for p in paths}

    missing = [p for p in navigation.indexable_paths() if p not in paths]
    assert not missing, f"sitemap is missing indexable pages: {missing[:12]}"


def test_the_sitemap_lists_every_sheet_slug(client, seeded):
    from engineverse import coding

    response = client.get("/sitemap.xml")
    for sheet in coding.list_sheets(limit=200):
        assert f"/sheets/{sheet['slug']}</loc>" in response.text, f"sheet {sheet['slug']} missing"


def test_the_index_page_renders_every_group(signed_in):
    """/resources is the 'all things together' page; it must list them all."""
    html = signed_in.get("/resources").text
    assert html.count("Everything on EngineVerse") >= 1
    for section in navigation.index_sections():
        assert f">{section.label}</a>" in html, f"the index omits the {section.label} group"
    for dest in navigation.all_destinations():
        if dest.pattern:
            continue
        assert f'href="{dest.path}"' in html, f"the index omits {dest.path}"


def test_branch_hubs_are_linked_from_the_catalogue(signed_in):
    """All 45 branch pages were in the sitemap and reachable from nowhere else.

    The branch picker on /explore only filtered the page, so nothing linked to
    /branches/{slug} or to the matching study hub.
    """
    from engineverse import catalog

    html = signed_in.get("/explore").text
    for branch in catalog.list_branches():
        assert f'href="/branches/{branch["slug"]}"' in html, f"/explore does not link {branch['slug']}"
        assert f'href="/stream/{branch["slug"]}"' in html, f"/explore does not link the {branch['slug']} hub"


def test_menus_open_without_javascript(signed_in):
    """A group label must be a real link, not a control that needs scripting.

    The site's rule is that every page works with no JavaScript, and the menus
    open on :hover and :focus-within in CSS. If a label were a <button> a reader
    with scripting off would have a navigation bar that does nothing.
    """
    html = signed_in.get("/explore").text
    labels = re.findall(r'<a class="navgroup-label" href="([^"]+)"', html)
    assert labels, "no group labels rendered as links"
    expected = {item.href for item in navigation.primary_nav() if item.children}
    assert set(labels) == expected


# ---------------------------------------------------------------------------
# The README
# ---------------------------------------------------------------------------

def _readme_nav_table() -> dict[str, str]:
    """The top-bar table in README.md, as {group label: landing path}."""
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Finding things", 1)[-1]
    rows = re.findall(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*`([^`]+)`\s*\|", section, re.M)
    return {label.strip(): path.strip() for label, path in rows}


def test_the_readme_top_bar_table_matches_the_application():
    """The README documents the navigation, so it has to be checked like code.

    A stale count in these docs has rotted before - the README claimed 6
    interactive diagrams long after all 48 were filled in - and a navigation
    table is exactly the kind of thing that goes wrong quietly, because nothing
    reads it at runtime.
    """
    documented = _readme_nav_table()
    assert documented, "no top-bar table found under README's 'Finding things'"
    actual = {item.label: item.href for item in navigation.primary_nav(signed_in=True)}
    assert documented == actual, (
        f"README says {documented} but the application renders {actual}"
    )
