#!/usr/bin/env python3
"""Send a monthly AI Star snapshot from GitHub to Feishu."""

from __future__ import annotations

import os
import re
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


def make_text(items: list[dict]) -> str:
    from datetime import date

    report_date = date.today().isoformat()
    lines = [
        f"截至 {report_date} 的近 30 天 GitHub AI 项目 Star 增长榜 Top 10",
        "按 GitHub Trending 月榜显示的新增 Stars 排序：",
        "",
    ]
    for index, item in enumerate(items, 1):
        description = item["description"] or "GitHub 未提供项目简介"
        lines.extend([
            f'{index}. {item["name"]}  +{item["monthly_stars"]:,} Stars',
            item["url"],
            description,
            "",
        ])
    lines.append("说明：根据 GitHub Trending 月榜及项目名称、简介中的 AI 关键词筛选。")
    return "\n".join(lines)


def send_feishu(items: list[dict]) -> None:
    webhook = os.environ["FEISHU_WEBHOOK"]
    payload = {"msg_type": "text", "content": {"text": make_text(items)}}
    response = requests.post(webhook, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    if result.get("code", 0) != 0:
        raise RuntimeError(f"Feishu bot returned an error: {result}")


def main() -> None:
    items = collect()
    send_feishu(items)
    print(f"Sent monthly AI Star report to Feishu ({len(items)} projects).")


if __name__ == "__main__":
    main()
