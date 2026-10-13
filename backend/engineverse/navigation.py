"""The site's information architecture, written down once.

EngineVerse grew to roughly sixty pages. The navigation that pointed at them was
written out three separate times - the desktop top bar, the five footer columns
and the mobile bottom bar - and each copy was edited on its own. They drifted:

* the top bar said ``Practice`` and the footer heading said ``Practise``;
* the top bar said ``Code`` for ``/programming`` while the footer said
  ``Learn to code`` for the same URL, next to a *different* item called ``Learn``;
* the mobile bar lit up ``My stream`` while the reader was on ``/explore`` or
  ``/subjects/...``, and lit up ``Sheets`` while they were on ``/projects``;
* about fifteen pages (``/mistakes``, ``/streaks``, ``/today``, ``/leaderboard``,
  ``/onboarding``, ``/install``, ``/videos``, ``/books``, ``/dpp/archive``) were
  reachable only from the footer, so a reader who never scrolled that far could
  not find them at all;
* ``/sitemap.xml`` carried its own list of twenty paths and had quietly fallen
  behind the application - it omitted ``/sheets``, a top-bar item, and every
  sheet slug with it.

Nothing enforced agreement because nothing was shared. This module is the shared
thing: one ordered table of every destination on the site, grouped the way a
learner actually thinks about it. The top bar, the mobile menu, the footer, the
breadcrumb trail, the "everything on EngineVerse" index, the sitemap and the
GitHub Pages export list are all *rendered from this table*, so a page added here
appears in all of them and a page missing here is missing from all of them. When
the site and its navigation disagree, this file is the one place to look.

Deliberately dumb on purpose. It is plain data with no database access and no
request object, so ``scripts/export_pages.py`` can import it at build time and
the test suite can assert on it without an application running. Anything that
comes from the database - the counts on the index page - is filled in by the
caller; this module only knows the shape of the site.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence

__all__ = [
    "Crumb",
    "Destination",
    "FooterColumn",
    "NavItem",
    "Section",
    "EXTRA_FOOTER_SECTIONS",
    "SECTIONS",
    "account_destinations",
    "active_mobile",
    "all_destinations",
    "breadcrumb_trail",
    "destination_for",
    "find",
    "footer_columns",
    "index_sections",
    "indexable_paths",
    "mobile_nav",
    "primary_nav",
    "section_for",
]


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Destination:
    """One page a reader is meant to be able to find.

    ``match`` lists the URL prefixes that mean "you are here". A destination owns
    its child pages - ``Practice sheets`` matches ``/sheets`` *and*
    ``/sheets/arrays-hashing`` - which is what makes both the active-link
    highlighting and the breadcrumb trail derivable instead of hand-written per
    template. Prefixes are compared on a path-segment boundary, so ``/stream``
    does not accidentally claim ``/streams`` and ``/practice`` does not claim
    ``/practice/problems`` for the wrong group.
    """

    label: str
    path: str
    blurb: str = ""
    match: tuple[str, ...] = ()
    #: Needs an account: the page answers an anonymous request by redirecting to
    #: /login. Dropped from navigation for a signed-out visitor so nobody is
    #: shown a link that only bounces them, and excluded from the static export,
    #: which cannot run accounts.

    #:
    #: This is a claim about the application's behaviour, not an opinion about
    #: who the page is for, and ``test_navigation.py`` checks it against the
    #: running app. A page that merely works *better* when signed in still
    #: renders anonymously on an instance where sign-in is optional, so it is not
    #: signed_in: marking it would hide a working page from signed-out readers
    #: and drop it from the static export.
    signed_in: bool = False
    #: Listed in the sitemap when the instance allows anonymous browsing.
    indexable: bool = True
    #: Kept out of menus and the footer because it is a variant of another entry
    #: rather than a destination of its own (/streams alongside /stream).
    minor: bool = False
    #: Offered only to signed-in readers, even though the page itself renders for
    #: an anonymous one. Distinct from ``signed_in`` because it is a navigation
    #: judgement rather than a claim about the application: /stream answers an
    #: anonymous request by redirecting to whatever branch it falls back to,
    #: which is not what a link labelled "My stream" promises - there is no "my"
    #: without an account. Signed-out readers get "All streams" instead.
    member_only: bool = False
    #: The path is a *shape*, not a page: only /portfolio/{username} and
    #: /certificates/{verify_id} exist, so the bare prefix must never be rendered
    #: as a link - it would be a 404. Used for breadcrumb grouping only.
    pattern: bool = False
    #: Key into the icon macro in ``templates/_icons.html``.
    icon: str = ""

    @property
    def prefixes(self) -> tuple[str, ...]:
        return self.match or (self.path,)

    def matches(self, path: str) -> bool:
        """True when this destination owns ``path``, including its child pages.

        Used to mark the current link in menus and the footer, so "you are here"
        is derived from the same prefixes the breadcrumb trail uses instead of
        being a second, hand-written guess per template.
        """
        owner = destination_for(path)
        return owner is not None and owner.path == self.path


@dataclass(frozen=True)
class Section:
    """A group of destinations that answers one question.

    The group label is itself a link to ``landing``. That matters because the
    menus open on hover and focus: a reader without JavaScript, or on a touch
    screen, or using a screen reader, still gets somewhere useful from one click
    on the group name instead of a control that does nothing.
    """

    key: str
    label: str
    blurb: str
    landing: str
    destinations: tuple[Destination, ...] = ()
    #: Key into the icon macro, for the index page and the mobile menu headings.
    icon: str = ""
    #: Appears as a level in the breadcrumb trail. False for the footer-only
    #: administrative groups, which organise links rather than describe a place.
    crumb_group: bool = True
    #: Gets its own footer column. False where the group has a single link that
    #: the footer already shows as a button, so it would be said twice.
    in_footer: bool = True
    #: What the group is called for a signed-out visitor. "My stream" is a
    #: promise the site cannot keep without an account, so that group reads
    #: "Streams" to everyone else - the same swap the top bar already made.
    anonymous_label: str = ""
    #: Where the group label points for a signed-out visitor, when ``landing``
    #: needs an account. The Revise group lands on the private schedule for a
    #: member and on the public decks for everyone else; without this the label
    #: would be a link whose only effect is a bounce to /login.
    anonymous_landing: str = ""

    def landing_for(self, signed_in: bool) -> str:
        """The URL this group's label should point at, for this audience.

        Falls back to the group's first publicly readable destination, then to an
        empty string - which tells the template to render a plain heading rather
        than a link, because a heading that goes nowhere honest is better than a
        link that redirects to a sign-in form.
        """
        if signed_in:
            return self.landing
        if self.anonymous_landing:
            return self.anonymous_landing
        for dest in self.destinations:
            if not dest.signed_in and not dest.member_only and not dest.pattern:
                return dest.path
        return ""

    def for_audience(self, signed_in: bool) -> "Section":
        """This section, filtered and re-pointed for a signed-out visitor.

        Both halves matter and used to be done separately: dropping the gated
        destinations while leaving the group label pointing at a gated landing
        page is what let /revision and /today reach a signed-out reader as links
        that could only bounce them to /login.
        """
        if signed_in:
            return self
        return Section(
            key=self.key, label=self.anonymous_label or self.label,
            blurb=self.blurb, landing=self.landing_for(False),
            icon=self.icon, crumb_group=self.crumb_group, in_footer=self.in_footer,
            anonymous_landing=self.anonymous_landing, anonymous_label=self.anonymous_label,
            destinations=tuple(
                d for d in self.destinations if not d.signed_in and not d.member_only
            ),
        )


# --- My stream: the entry point ---------------------------------------------

STREAM = Section(
    key="stream",
    label="My stream",
    blurb="Your branch's own study hub, and the switcher for every other branch.",
    landing="/stream",
    anonymous_landing="/streams",
    anonymous_label="Streams",
    icon="compass",
    in_footer=False,
    destinations=(
        Destination(
            "My stream", "/stream",
            "Opens on the branch saved in your profile, with everything that branch has.",
            match=("/stream",), icon="compass",
            # Not gated - a signed-out visitor is redirected to a branch page that
            # works - so ``signed_in`` would be a false claim about the app, and
            # test_signed_in_flags_match_what_the_application_actually_does would
            # catch it. It is member_only instead: the label is "My stream", and
            # not publishable either, since "my" stream has no single canonical
            # URL. /streams is the one a signed-out reader gets and the one that
            # goes in a sitemap.
            member_only=True, indexable=False,
        ),
        Destination(
            "All streams", "/streams",
            "Switch branch, or see what another branch studies.",
            match=("/streams",), minor=True,
        ),
    ),
)

# --- Learn: "what do I study?" ----------------------------------------------

LEARN = Section(
    key="learn",
    label="Learn",
    blurb="Subjects, notes, formulas and the reading that goes with them.",
    landing="/explore",
    icon="book",
    destinations=(
        Destination(
            "Explore subjects", "/explore",
            "The whole catalogue: every branch, subject and topic, filterable by semester.",
            match=("/explore", "/branches", "/subjects", "/topics"), icon="book",
        ),
        Destination(
            "Formula centre", "/formulas",
            "Searchable formulas with their variables, units and where each one applies.",
            icon="sigma",
        ),
        Destination(
            "Video library", "/videos",
            "Lectures and walkthroughs grouped by category, kept beside the notes.",
            icon="play",
        ),
        Destination(
            "Reference books", "/books",
            "The standard texts for each subject, with what each one is good for.",
            icon="library",
        ),
        Destination(
            "Roadmaps", "/roadmaps",
            "Term-by-term and career paths, with the steps written out.",
            match=("/roadmaps",), icon="map",
        ),
        Destination(
            "Study tutor", "/tutor",
            "Answers composed only from this site's own material, with the sources cited.",
            icon="spark",
        ),
    ),
)

# --- Practice: "how do I check I know it?" ----------------------------------

PRACTICE = Section(
    key="practice",
    label="Practice",
    blurb="Questions, daily sets and the notebook of things you got wrong.",
    landing="/practice",
    icon="target",
    destinations=(
        Destination(
            "Practice hub", "/practice",
            "Where to start a session: today's set, the question bank and your accuracy.",
            match=("/practice",), icon="target",
        ),
        Destination(
            "Daily practice", "/dpp",
            "A fresh mixed set every day, with the whole archive behind it.",
            match=("/dpp",), icon="calendar",
        ),
        Destination(
            "Daily practice archive", "/dpp/archive",
            "Every past daily set, to work back through when today's is done.",
            minor=True,
        ),
        Destination(
            "Question bank", "/practice/questions",
            "Multiple choice, numericals, conceptual, debugging and interview questions.",
            icon="list",
        ),
        Destination(
            "Mistake notebook", "/mistakes",
            "Every question you got wrong, kept until you get it right twice.",
            signed_in=True, icon="eraser",
        ),
    ),
)

# --- Code: "can I build something that runs?" -------------------------------

CODE = Section(
    key="code",
    label="Code",
    blurb="Language paths, coding problems, curated sheets and project briefs.",
    landing="/programming",
    icon="terminal",
    destinations=(
        Destination(
            "Language paths", "/programming",
            "Staged modules with checkpoints, from first syntax to advanced engineering.",
            match=("/programming",), icon="terminal",
        ),
        Destination(
            "Coding problems", "/practice/problems",
            "Problems with editor stubs and tests, run by the judge on this host.",
            icon="code",
        ),
        Destination(
            "Practice sheets", "/sheets",
            "Curated sets by pattern and by stream, including a thirty-problem interview core.",
            match=("/sheets",), icon="layers",
        ),
        Destination(
            "Projects", "/projects",
            "Briefs with ordered steps, skills, resources and a shippable result.",
            match=("/projects",), icon="hammer",
        ),
    ),
)

# --- Revise: "how do I not forget it?" --------------------------------------

REVISE = Section(
    key="revise",
    label="Revise",
    blurb="Spaced repetition, flashcards and the sheets you revise from.",
    landing="/revision",
    anonymous_landing="/flashcards",
    icon="refresh",
    destinations=(
        Destination(
            "My revision", "/revision",
            "Your own SM-2 schedule: what is due today and what is coming up.",
            icon="refresh",
        ),
        Destination(
            "Public flashcards", "/flashcards",
            "Every deck on the site, browsable without signing in.",
            icon="cards",
        ),
        Destination(
            "Formula centre", "/formulas",
            "The same formulas as under Learn, collected here for a last-minute pass.",
            icon="sigma",
        ),
        Destination(
            "Roadmaps", "/roadmaps",
            "Zoom out to the term-by-term plan the revision is serving.",
            match=("/roadmaps",), icon="map",
        ),
    ),
)

# --- Progress: "am I getting better?" ---------------------------------------

PROGRESS = Section(
    key="progress",
    label="Progress",
    blurb="Your plan for today, your streak, and how you compare.",
    landing="/today",
    anonymous_landing="/leaderboard",
    icon="flame",
    destinations=(
        Destination(
            "Today's plan", "/today",
            "One page saying what to do next: the daily set, due cards, topics to retry.",
            signed_in=True, icon="sun",
        ),
        Destination(
            "Streaks and heatmap", "/streaks",
            "Six months of study days, your current streak and your XP history.",
            icon="flame",
        ),
        Destination(
            "Leaderboard", "/leaderboard",
            "How your XP compares with everyone else on this instance.",
            icon="trophy",
        ),
        Destination(
            "My profile", "/profile",
            "Your badges, certificates, submissions and public portfolio.",
            signed_in=True, indexable=False, icon="user",
        ),
    ),
)

# --- Community and career ---------------------------------------------------

COMMUNITY = Section(
    key="community",
    label="Community",
    blurb="Other learners, placement preparation, and what this platform is.",
    landing="/community",
    icon="chat",
    destinations=(
        Destination(
            "Discussion forum", "/community",
            "Threads and answers from other learners on this instance.",
            match=("/community",), icon="chat",
        ),
        Destination(
            "Placement prep", "/placements",
            "Interview sets, company patterns and the sheet that covers them.",
            icon="briefcase",
        ),
        Destination(
            "About EngineVerse", "/about",
            "What this platform is, what it is not, and how it is built.",
            icon="info",
        ),
    ),
)

# --- Finding your way around ------------------------------------------------

GUIDE = Section(
    key="guide",
    label="Browse",
    blurb="The index of everything on this site, search, and optional outside reading.",
    landing="/resources",
    icon="grid",
    in_footer=False,
    destinations=(
        Destination(
            "Everything on EngineVerse", "/resources",
            "The complete index of every page and tool here, grouped, with live counts.",
            match=("/resources",), icon="grid",
        ),
        Destination(
            "Search", "/search",
            "Search notes, problems, sheets, projects and the community at once.",
            minor=True,
        ),
        Destination(
            "Optional external reading", "/resources/offsite",
            "Documentation sites and open textbooks. Nothing in a lesson needs them.",
            match=("/resources/offsite",), minor=True,
        ),
    ),
)

SECTIONS: tuple[Section, ...] = (STREAM, LEARN, PRACTICE, CODE, REVISE, PROGRESS, COMMUNITY, GUIDE)

#: Order the entries appear in the desktop bar. "My stream" first because it
#: answers "where is my course?", then the four study verbs, then everything the
#: bar has no room for folded under "More". Six entries replace ten flat links.
TOPBAR_ORDER: tuple[str, ...] = ("stream", "learn", "practice", "code", "revise", "more")

#: Sections folded into the "More" menu rather than getting a bar slot.
MORE_SECTIONS: tuple[str, ...] = ("progress", "community", "guide")

#: Groups that belong in the footer and the index but not in the top bar:
#: account, legal and install.
EXTRA_FOOTER_SECTIONS: tuple[Section, ...] = (
    Section(
        key="account",
        label="Your account",
        crumb_group=False,
        # The footer merges this group and Platform into a single "Account"
        # column, so neither gets one of its own.
        in_footer=False,
        blurb="Settings, notifications and the staff console.",
        landing="/settings",
        anonymous_landing="/privacy",
        icon="cog",
        destinations=(
            Destination("Settings", "/settings",
                        "Profile, branch, security and notification preferences.",
                        signed_in=True, indexable=False, icon="cog"),
            Destination("Notifications", "/notifications",
                        "What changed since you last looked.",
                        signed_in=True, indexable=False, icon="bell"),
            Destination("Onboarding", "/onboarding",
                        "Set your branch, semester and how deep you want your notes.",
                        signed_in=True, indexable=False, minor=True),
            Destination("Public portfolio", "/portfolio",
                        "The page other learners and recruiters see, at /portfolio/{you}.",
                        indexable=False, minor=True, pattern=True),
            Destination("Admin console", "/admin",
                        "Staff only: content, users and instance settings.",
                        signed_in=True, indexable=False, minor=True),
            Destination("Verify a certificate", "/certificates",
                        "Check a certificate by its ID. Open to anyone, no account needed.",
                        indexable=False, minor=True, pattern=True),
        ),
    ),
    Section(
        key="platform",
        label="Platform",
        crumb_group=False,
        in_footer=False,
        blurb="Installing the app, reading offline, and the terms it runs under.",
        landing="/about",
        icon="download",
        destinations=(
            Destination("Install the app", "/install",
                        "Add EngineVerse to your home screen and use it like an app.",
                        icon="download"),
            Destination("Offline help", "/offline",
                        "What still works when the connection does not.", minor=True),
            Destination("Privacy", "/privacy",
                        "What is stored, and what never leaves this server."),
            Destination("Terms", "/terms",
                        "The terms this instance is offered under."),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------

def all_sections() -> tuple[Section, ...]:
    """Every section, top bar and footer alike, in reading order."""
    return SECTIONS + EXTRA_FOOTER_SECTIONS


def all_destinations() -> Iterator[Destination]:
    """Every destination on the site, in reading order, without duplicates.

    A path may legitimately appear in more than one group - the formula centre is
    both something you learn from and something you revise from - so this
    de-duplicates on path and keeps the first, most prominent listing.
    """
    seen: set[str] = set()
    for section in all_sections():
        for dest in section.destinations:
            if dest.path in seen:
                continue
            seen.add(dest.path)
            yield dest


def find(path: str) -> Destination | None:
    """The destination whose URL is exactly ``path``."""
    for dest in all_destinations():
        if dest.path == path:
            return dest
    return None


def destination_for(path: str) -> Destination | None:
    """The destination that owns ``path``, including its child pages.

    Longest prefix wins, so ``/resources/offsite`` claims itself rather than
    being swallowed by ``/resources``, and ``/practice/problems`` claims itself
    rather than being swallowed by ``/practice``.
    """
    best: Destination | None = None
    best_len = -1
    for dest in all_destinations():
        for prefix in dest.prefixes:
            clean = prefix.rstrip("/") or "/"
            if len(clean) <= best_len:
                continue
            if path == clean or path.startswith(clean + "/"):
                best, best_len = dest, len(clean)
    return best


def section_for(path: str) -> Section | None:
    """The section that owns ``path``, for grouping and breadcrumbs."""
    dest = destination_for(path)
    if dest is None:
        return None
    for section in all_sections():
        if any(d.path == dest.path for d in section.destinations):
            return section
    return None


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NavItem:
    """One entry in the desktop top bar or the mobile bottom bar."""

    label: str
    href: str
    match: tuple[str, ...] = ()
    children: tuple[Destination, ...] = ()
    #: Active only on this exact URL - used by "Home", whose prefix would
    #: otherwise match every page on the site.
    exact: bool = False
    icon: str = ""
    #: One line saying what the group is for, shown at the top of its menu.
    blurb: str = ""

    @property
    def prefixes(self) -> tuple[str, ...]:
        return self.match or (self.href,)

    def is_active(self, path: str) -> bool:
        for prefix in self.prefixes:
            clean = prefix.rstrip("/") or "/"
            if self.exact:
                if path == clean:
                    return True
            elif path == clean or path.startswith(clean + "/"):
                return True
        return False


def _section_item(section: Section, signed_in: bool = True) -> NavItem:
    section = section.for_audience(signed_in)
    children = tuple(d for d in section.destinations if not d.minor and d.path != section.landing)
    match = tuple(p for d in section.destinations for p in d.prefixes)
    return NavItem(label=section.label, href=section.landing, match=match,
                   children=children, icon=section.icon, blurb=section.blurb)


def primary_nav(signed_in: bool = True) -> list[NavItem]:
    """The desktop top bar: six grouped entries instead of ten flat links.

    Each group label links to that group's landing page, so the bar is still one
    click to the most important page in every group for a reader who never opens
    a menu - and the menus are what make the other forty pages findable without
    scrolling to the footer. ``signed_in`` drops the destinations that need an
    account.
    """
    by_key = {section.key: section for section in SECTIONS}
    items: list[NavItem] = []

    for key in TOPBAR_ORDER:
        if key == "stream":
            section = by_key["stream"].for_audience(signed_in)
            if not section.destinations:
                continue
            # The stream hub stays a direct link, not a menu: it is the answer to
            # "where is my course?" and deserves one click. Everything else from
            # the Browse group rides along in its menu.
            guide = next((d for d in GUIDE.destinations if d.path == "/resources"), None)
            children = tuple(d for d in section.destinations if not d.minor and d.path != section.landing)
            if guide is not None:
                children = children + (guide,)
            items.append(NavItem(
                label="My stream" if signed_in else "Streams",
                href="/stream" if signed_in else "/streams",
                match=("/stream", "/streams"), children=children, icon="compass",
                blurb=section.blurb,
            ))
            continue
        if key == "more":
            children: list[Destination] = []
            for more_key in MORE_SECTIONS:
                section = by_key[more_key].for_audience(signed_in)
                children.extend(d for d in section.destinations if not d.minor)
            if not children:
                continue
            items.append(NavItem(
                label="More", href="/resources",
                match=tuple(p for d in children for p in d.prefixes),
                children=tuple(children), icon="grid",
                blurb="Your progress, other learners, and the index of every page here.",
            ))
            continue
        item = _section_item(by_key[key], signed_in=signed_in)
        if item.children or item.href:
            items.append(item)
    return items


def mobile_nav(signed_in: bool = True) -> list[NavItem]:
    """The five-icon bottom bar.

    Five slots is the whole budget, so these are the five things a learner
    returns to every day. Everything else is in the menu button, which now shows
    the same grouped structure as the desktop bar instead of a flat list of ten.
    """
    def match_of(section: Section) -> tuple[str, ...]:
        return tuple(p for d in section.destinations for p in d.prefixes)

    return [
        NavItem(label="Home", href="/", match=("/",), exact=True, icon="home"),
        NavItem(
            label="Stream" if signed_in else "Streams",
            href="/stream" if signed_in else "/streams",
            match=("/stream", "/streams"), icon="compass",
        ),
        NavItem(label="Learn", href=LEARN.landing, match=match_of(LEARN), icon="book"),
        NavItem(label="Practice", href=PRACTICE.landing, match=match_of(PRACTICE), icon="target"),
        NavItem(label="Code", href=CODE.landing, match=match_of(CODE), icon="terminal"),
    ]


def active_mobile(path: str, items: Sequence[NavItem] | None = None) -> str | None:
    """The one bottom-bar item that owns ``path``, or None.

    Returns at most one label, never two. The bar used to highlight several at
    once because each item was tested independently against overlapping
    prefixes; longest match wins here, so ``/practice/problems`` belongs to Code
    even though ``/practice`` also matches it.
    """
    best: str | None = None
    best_len = -1
    for item in (items if items is not None else mobile_nav()):
        for prefix in item.prefixes:
            clean = prefix.rstrip("/") or "/"
            hit = path == clean if item.exact else (path == clean or path.startswith(clean + "/"))
            if hit and len(clean) > best_len:
                best, best_len = item.label, len(clean)
    return best


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FooterColumn:
    heading: str
    links: tuple[Destination, ...] = ()


def footer_columns(signed_in: bool = True) -> list[FooterColumn]:
    """The footer, built from the same table as the top bar.

    One column per section, in the same order, with the same labels and the same
    URLs. The footer was a fourth hand-written copy of the navigation and had
    drifted: it said "Practise" where the bar said "Practice", and called
    /programming "Learn to code" where the bar called it "Code". Both now come
    from one string, so they cannot disagree.
    """
    columns: list[FooterColumn] = []
    for section in all_sections():
        if not section.in_footer:
            continue
        section = section.for_audience(signed_in)
        links = tuple(d for d in section.destinations if not d.minor)
        if not links:
            continue
        columns.append(FooterColumn(heading=section.label, links=links))
    return columns


def account_destinations(signed_in: bool = True) -> list[Destination]:
    """The footer's account and platform links, kept out of the main columns."""
    out: list[Destination] = []
    for section in EXTRA_FOOTER_SECTIONS:
        out.extend(d for d in section.destinations if signed_in or not d.signed_in)
    return out


# ---------------------------------------------------------------------------
# Breadcrumbs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Crumb:
    """One level of a breadcrumb trail. No ``href`` means "you are here"."""

    label: str
    href: str | None = None

    @property
    def is_current(self) -> bool:
        return self.href is None


def breadcrumb_trail(
    path: str,
    leaf: str = "",
    parents: Sequence[tuple[str, str]] | None = None,
    signed_in: bool = True,
) -> list[Crumb]:
    """The trail to ``path``, derived from the table instead of per template.

    Twelve of the forty-nine templates carried a hand-written breadcrumb and the
    other thirty-seven carried none, so most of the site had no way back up the
    hierarchy. The labels disagreed as well: /branches/x said "Branches" and
    /subjects/y said "Subjects" while both pointed at /explore.

    The trail is Home, then the owning group, then the owning destination, then
    the item itself. A level is dropped when it would repeat the URL of the level
    above it, so /topics/arrays reads "Home > Learn > Arrays" rather than
    "Home > Learn > Explore subjects > Arrays" with two links to the same page.

    ``leaf`` is the name of the item on this page, supplied by the handler that
    already fetched it. Without one, the trail stops at its last link and the
    page's own heading is the current level.

    ``parents`` inserts extra ``(label, url)`` levels immediately above the leaf,
    for the one relationship the flat table cannot express: a topic belongs to a
    subject as well as to the catalogue, so /topics/arrays asks its handler for
    the subject in between. Everything else is derivable and needs no argument.

    ``signed_in`` matters because a trail is made of links. For a signed-out
    reader the group level resolves to that group's public landing page, and a
    member-only level is dropped entirely: the exported static copy has no
    /stream page, so a breadcrumb pointing at one is a link that goes nowhere.
    """
    if path in ("", "/"):
        return [Crumb("Home")] if leaf else []

    crumbs: list[Crumb] = [Crumb("Home", "/")]
    dest = destination_for(path)
    section = section_for(path)
    if section is not None:
        section = section.for_audience(signed_in)
    if dest is not None and not signed_in and (dest.signed_in or dest.member_only):
        # This reader cannot be sent to that level, so the trail skips it and
        # keeps the group above it, which has already been re-pointed.
        dest = None

    if section is not None:
        on_destination = dest is not None and dest.path == path
        # The group level, unless the group's landing page *is* this page or the
        # destination below it - repeating a URL in a trail is noise. A group
        # that exists only to organise the footer ("Your account", "Platform")
        # is not a place a reader travels through, so it is left out too.
        #
        # This is tested even when dest is None, which happens for a signed-out
        # reader on a member-only page: the group still belongs in the trail,
        # re-pointed at the public landing page, so /stream/production reads
        # "Home > Streams > Production Engineering" instead of losing its middle.
        if (section.crumb_group and section.landing not in ("/", path)
                and not (on_destination and section.landing == dest.path)):
            crumbs.append(Crumb(section.label, section.landing))
        if dest is not None:
            # A pattern destination (/portfolio, /certificates) names a family of
            # pages rather than one page. Its label is useful in the trail but
            # its path is a 404, so it appears as a plain level with no link.
            if not on_destination and dest.path != section.landing and dest.path not in ("/", path):
                crumbs.append(Crumb(dest.label, None if dest.pattern else dest.path))
            elif on_destination and not leaf:
                # This page *is* a named destination, so it is the current level.
                crumbs.append(Crumb(dest.label))
    elif dest is not None and dest.path not in ("/", path):
        crumbs.append(Crumb(dest.label, None if dest.pattern else dest.path))

    for label, href in (parents or ()):
        if not label:
            continue
        # Never repeat the level immediately above, and never link to this page.
        if href and (href == path or (crumbs and crumbs[-1].href == href)):
            continue
        crumbs.append(Crumb(str(label)[:120], href or None))
    if leaf:
        crumbs.append(Crumb(leaf[:120]))
    return crumbs


# ---------------------------------------------------------------------------
# The "everything in one place" index
# ---------------------------------------------------------------------------

def index_sections(signed_in: bool = True) -> list[Section]:
    """Every section, for the complete index page.

    Same data as the top bar, but nothing is folded away and nothing is hidden as
    ``minor``: this is the page that answers "what is actually on this site?", so
    it lists the variants too and includes the account and platform groups.
    """
    ordered = [STREAM, LEARN, PRACTICE, CODE, REVISE, PROGRESS, COMMUNITY, GUIDE]
    ordered.extend(EXTRA_FOOTER_SECTIONS)
    out: list[Section] = []
    for section in ordered:
        section = section.for_audience(signed_in)
        # A pattern destination (/portfolio, /certificates) has no page of its
        # own to open, so the index - which is a list of things to click - leaves
        # it out. It still shapes breadcrumbs, which is what it is here for.
        dests = tuple(d for d in section.destinations if not d.pattern)
        if not dests:
            continue
        out.append(Section(
            key=section.key, label=section.label, blurb=section.blurb,
            landing=section.landing, icon=section.icon,
            crumb_group=section.crumb_group, in_footer=section.in_footer,
            anonymous_landing=section.anonymous_landing, destinations=dests,
        ))
    return out


# ---------------------------------------------------------------------------
# Sitemap and static export
# ---------------------------------------------------------------------------

#: Public paths that are not destinations anyone navigates to, but that a
#: crawler should still know exist.
SYSTEM_PATHS: tuple[str, ...] = ("/",)

#: Never published, whatever the table says. These are private to one account or
#: to staff, and putting them in a public sitemap would leak a username or
#: advertise a console.
NON_INDEXABLE: frozenset[str] = frozenset({
    "/profile", "/settings", "/notifications", "/onboarding", "/admin",
    "/today", "/streaks", "/revision", "/mistakes", "/portfolio", "/certificates",
})


def indexable_paths(public_only: bool = False) -> list[str]:
    """Every path worth putting in a sitemap or a static export.

    ``/sitemap.xml`` used to carry its own hardcoded list and had fallen behind
    the application: it omitted ``/sheets`` - a top-bar item - and every sheet
    slug, plus ``/stream``, ``/install`` and ``/search``. Deriving the list from
    the navigation table means the sitemap cannot drift again.

    ``public_only`` restricts the result to pages an anonymous reader can
    actually open. That is what the static GitHub Pages export needs, and it is
    also the right answer for a sitemap on an instance where sign-in is
    compulsory: listing pages a crawler will only be redirected away from is
    noise, not coverage.
    """
    out: list[str] = []
    for dest in all_destinations():
        if dest.pattern or not dest.indexable or dest.path in NON_INDEXABLE:
            continue
        if public_only and dest.signed_in:
            continue
        out.append(dest.path)
    for path in SYSTEM_PATHS:
        if path not in NON_INDEXABLE:
            out.append(path)
    return sorted(set(out))
