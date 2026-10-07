#!/usr/bin/env python3
"""Email a monthly snapshot of AI-related repositories trending on GitHub."""

from __future__ import annotations

import os
import re
import smtplib
from email.message import EmailMessage
from html import unescape
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

BASE = "https://github.com/trending"
LANGUAGES = [
    "", "python", "typescript", "javascript", "jupyter-notebook",
    "go", "rust", "java", "c-plus-plus", "swift", "kotlin", "shell",
    "dart", "ruby", "php", "c-sharp", "vue", "html",
]
AI_TERMS = re.compile(
    r"\b(ai|artificial intelligence|machine learning|deep learning|"
    r"llm|large language model|generative|agent|agents|assistant|"
    r"copilot|rag|embedding|transformer|diffusion|inference|"
    r"vision model|language model|multimodal|neural network)\b",
    re.IGNORECASE,
)
HEADERS = {"User-Agent": "monthly-ai-star-report/1.0"}
TIMEOUT = 25


def as_int(value: str) -> int:
    return int(value.replace(",", "").replace(".", "").strip())


def trending_page(language: str) -> list[dict]:
    suffix = f"/{quote(language, safe='')}" if language else ""
    response = requests.get(
        f"{BASE}{suffix}",
        params={"since": "monthly"},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for card in soup.select("article.Box-row"):
        title_link = card.select_one("h2 a[href]")
        if not title_link:
            continue
        path = title_link.get("href", "").strip("/")
        if path.count("/") != 1:
            continue

        text = unescape(card.get_text(" ", strip=True))
        monthly = re.search(r"([\d,.]+)\s+stars?\s+this month", text, re.I)
        if not monthly:
            continue

        description_node = card.select_one("p")
        description = description_node.get_text(" ", strip=True) if description_node else ""
        repo_name = path
        if not AI_TERMS.search(f"{repo_name} {description}"):
            continue

        results.append({
            "name": repo_name,
            "url": f"https://github.com/{repo_name}",
            "description": description,
            "monthly_stars": as_int(monthly.group(1)),
        })
    return results


def collect() -> list[dict]:
    by_name = {}
    errors = []
    for language in LANGUAGES:
        try:
            for item in trending_page(language):
                old = by_name.get(item["name"])
                if old is None or item["monthly_stars"] > old["monthly_stars"]:
                    by_name[item["name"]] = item
        except requests.RequestException as exc:
            label = language or "all languages"
            errors.append(f"{label}: {exc}")

    ranked = sorted(
        by_name.values(),
        key=lambda item: (-item["monthly_stars"], item["name"].lower()),
    )[:10]
    if not ranked:
        detail = "; ".join(errors[:4]) or "No matching projects were found."
        raise RuntimeError(f"Could not collect an AI trending list. {detail}")
    return ranked


def make_email(items: list[dict]) -> EmailMessage:
    sender = os.environ["GMAIL_ADDRESS"]
    recipient = os.environ.get("RECIPIENT_EMAIL", "chenhello892@gmail.com")
    month = __import__("datetime").date.today().strftime("%Y年%m月")
    rows = []
    text_rows = []
    for index, item in enumerate(items, 1):
        description = item["description"] or "（GitHub 未提供项目简介）"
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f'<td><a href="{item["url"]}">{item["name"]}</a></td>'
            f'<td>{item["monthly_stars"]:,}</td>'
            f"<td>{description}</td>"
            "</tr>"
        )
        text_rows.append(
            f'{index}. {item["name"]} +{item["monthly_stars"]:,} stars\n'
            f'   {item["url"]}\n   {description}'
        )

    message = EmailMessage()
    message["Subject"] = f"{month} GitHub AI 项目 Star 增长榜 Top 10"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"{month} GitHub AI 项目 Star 增长榜 Top 10\n\n"
        + "\n\n".join(text_rows)
        + "\n\n统计口径：GitHub Trending 月榜中识别为 AI 相关的项目，按页面显示的本月新增 stars 排序。"
    )
    table = "".join(rows)
    message.add_alternative(
        "<html><body>"
        f"<h2>{month} GitHub AI 项目 Star 增长榜 Top 10</h2>"
        "<p>按 GitHub Trending 月榜页面显示的本月新增 stars 排序。"
        "项目通过名称和简介中的 AI 相关关键词识别。</p>"
        "<table border='1' cellpadding='6' cellspacing='0'>"
        "<thead><tr><th>排名</th><th>项目</th><th>本月新增 Stars</th><th>简介</th></tr></thead>"
        f"<tbody>{table}</tbody></table>"
        "</body></html>",
        subtype="html",
    )
    return message


def main() -> None:
    items = collect()
    message = make_email(items)
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        smtp.send_message(message)
    print(f"Sent monthly AI Star report to {message['To']} ({len(items)} projects).")


if __name__ == "__main__":
    main()
