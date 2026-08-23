#!/usr/bin/env python3
"""Regenerates README.md from live GitHub profile data."""
import datetime
import json
import os
import urllib.request

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "DroidNinja")
TOKEN = os.environ["GITHUB_TOKEN"]
ACTIVE_WINDOW_DAYS = 365
TOP_LANG_COUNT = 4
ACTIVE_PROJECT_COUNT = 6

LANG_COLORS = {
    "Java": "b07219",
    "Python": "3572A5",
    "C++": "f34b7d",
    "TypeScript": "3178c6",
    "Kotlin": "A97BFF",
    "C": "555555",
    "JavaScript": "f1e05a",
    "HTML": "e34c26",
    "CSS": "663399",
    "Ruby": "701516",
    "C#": "178600",
    "Go": "00ADD8",
    "Swift": "F05138",
    "Shell": "89e051",
    "Vue": "41b883",
    "Dart": "00B4AB",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    bio
    location
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        name
        pushedAt
        isArchived
        stargazerCount
        forkCount
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["data"]


def shields_badge(lang, pct):
    color = LANG_COLORS.get(lang, "888888")
    label = lang.replace("+", "%2B").replace("#", "%23").replace(" ", "%20")
    return (
        f"![{lang}](https://img.shields.io/static/v1?style=flat-square&label=%E2%A0%80"
        f"&color=555&labelColor=%23{color}&message={label}%20{pct}%25)"
    )


def main():
    data = graphql(QUERY, {"login": USERNAME})
    user = data["user"]
    repos = [r for r in user["repositories"]["nodes"] if not r["isArchived"]]

    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ACTIVE_WINDOW_DAYS)
    active = sorted(
        (r for r in repos if datetime.datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00")) >= cutoff),
        key=lambda r: r["pushedAt"],
        reverse=True,
    )[:ACTIVE_PROJECT_COUNT]

    total_stars = sum(r["stargazerCount"] for r in repos)

    lang_bytes = {}
    for r in repos:
        for edge in r["languages"]["edges"]:
            lang_bytes[edge["node"]["name"]] = lang_bytes.get(edge["node"]["name"], 0) + edge["size"]
    total_bytes = sum(lang_bytes.values()) or 1
    top_langs = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:TOP_LANG_COUNT]
    lang_badges = [shields_badge(lang, round(size / total_bytes * 100, 1)) for lang, size in top_langs]
    while len(lang_badges) < 4:
        lang_badges.append("")

    contrib = user["contributionsCollection"]

    active_lines = [
        f"- [{r['name']}](https://github.com/{USERNAME}/{r['name']}) — "
        f"⭐ {r['stargazerCount']:,} · 🍴 {r['forkCount']:,} · "
        f"{r['primaryLanguage']['name'] if r['primaryLanguage'] else 'n/a'} · "
        f"pushed {r['pushedAt'][:10]}"
        for r in active
    ]
    if not active_lines:
        active_lines = ["_No repos pushed in the last year._"]

    readme = f"""# Hi there, I'm {user['name'] or USERNAME} 👋

{user['bio'] or ''}

## 📊 Stats

| Profile | Activity | Top languages (by repo size) |
|---------|----------|-------------------------------|
| 📦 **{user['repositories']['totalCount']}** public repos | 🔥 **{contrib['totalCommitContributions']}** commits this year | {lang_badges[0]} |
| 👥 **{user['followers']['totalCount']}** followers | 🔀 **{contrib['totalPullRequestContributions']}** PRs this year | {lang_badges[1]} |
| ⭐ **{total_stars:,}** stars earned | | {lang_badges[2]} |
| 📍 {user['location'] or ''} | | {lang_badges[3]} |

## 🚀 Active Projects (last {ACTIVE_WINDOW_DAYS} days)

{chr(10).join(active_lines)}

## 🤝 Connect with me

[![X](https://img.shields.io/badge/X-000000?style=flat&logo=x&logoColor=white)](https://twitter.com/droid_arun)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077b5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/arunsharma92)
[![Blog](https://img.shields.io/badge/Blog-arunsharma.me-orange?style=flat&logo=rss&logoColor=white)](https://arunsharma.me)

<sub>Auto-generated on {datetime.date.today().isoformat()} by [update-readme.yml](.github/workflows/update-readme.yml).</sub>
"""

    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
