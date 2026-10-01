import json
import os
import re
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

CATEGORIES = [
    "Aerospace",
    "Naval",
    "Land Systems",
    "Cybersecurity",
    "Space",
    "AI/Robotics",
    "Defence Technology"
]

CATEGORY_KEYWORDS = {
    "Cybersecurity": [
        "cyber", "security", "monitoring", "threat",
        "alert", "malware", "network", "vulnerability",
        "incident"
    ],

    "Space": [
        "space", "satellite", "orbit",
        "earth observation", "ground station",
        "launch", "astronomy"
    ],

    "AI/Robotics": [
        "ai", "artificial intelligence", "robot",
        "robotics", "autonomous", "computer vision",
        "machine learning"
    ],

    "Aerospace": [
        "aircraft", "aerospace", "aviation",
        "drone", "flight", "airborne",
        "air vehicle"
    ],

    "Naval": [
        "naval", "ship", "maritime",
        "submarine", "vessel", "ocean", "sea"
    ],

    "Land Systems": [
        "land", "ground vehicle", "army",
        "vehicle", "inspection", "terrain"
    ]
}

STOPWORDS = {
    "the", "and", "for", "with", "that", "this",
    "from", "into", "their", "they", "have",
    "has", "will", "are", "was", "were",
    "been", "being", "about", "over", "under",
    "using", "uses", "used", "new", "more",
    "than", "also", "its", "our", "which",
    "through", "platform", "system", "technology"
}


def detect_category(title, content):
    text = f"{title} {content}".lower()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(
            1 for keyword in keywords
            if keyword in text
        )

    best_category = max(
        scores,
        key=scores.get
    )

    if scores[best_category] == 0:
        return "Defence Technology"

    return best_category


def extract_keywords(title, content):
    text = f"{title} {content}".lower()

    words = re.findall(
        r"[a-zA-Z][a-zA-Z-]{3,}",
        text
    )

    words = [
        word
        for word in words
        if word not in STOPWORDS
    ]

    counts = Counter(words)

    return [
        word
        for word, count in counts.most_common(6)
    ]


def make_summary(title, content):
    text = content.strip()

    if not text:
        return title

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    if len(sentences) >= 2:
        return " ".join(sentences[:2])

    return sentences[0][:350]


def extract_topics(category, keywords):
    topics = [category]

    for keyword in keywords[:4]:
        if keyword not in topics:
            topics.append(keyword)

    return topics[:6]


def extract_entities(title, content):
    text = f"{title}. {content}"

    matches = re.findall(
        r"\b(?:[A-Z][a-zA-Z-]+"
        r"(?:\s+[A-Z][a-zA-Z-]+){0,3})\b",
        text
    )

    entities = []

    for item in matches:

        item = item.strip()

        if item.lower() in {
            "the",
            "new",
            "this",
            "earth",
            "cloud"
        }:
            continue

        if item not in entities:
            entities.append(item)

    return entities[:6]


def process_article(title, content):

    try:
        import urllib.request

        system = """
You are an information-processing assistant for ASTRA SENTINEL.

Analyze only the supplied article text.

Return valid JSON with exactly these keys:
category
summary
keywords
topics
entities

Category must be exactly one of:
Aerospace
Naval
Land Systems
Cybersecurity
Space
AI/Robotics
Defence Technology

Summary must be 2-3 concise sentences.

keywords, topics, and entities must each be arrays of 3-6 short strings.

Do not invent facts.
"""

        payload = {
            "model": "llama3.2:3b",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"{system}\n\n"
                        f"TITLE: {title}\n\n"
                        f"ARTICLE:\n{content[:12000]}"
                    )
                }
            ],
            "stream": False,
            "format": "json"
        }

        request = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        data = json.loads(
            result["message"]["content"]
        )

        if data.get("category") not in CATEGORIES:
            data["category"] = "Defence Technology"

        for key in ["keywords", "topics", "entities"]:
            if not isinstance(data.get(key), list):
                data[key] = []

        if not data.get("summary"):
            data["summary"] = make_summary(title, content)

        return data

    except Exception:
        category = detect_category(title, content)
        keywords = extract_keywords(title, content)
        topics = extract_topics(category, keywords)
        entities = extract_entities(title, content)
        summary = make_summary(title, content)

        return {
            "category": category,
            "summary": summary,
            "keywords": keywords,
            "topics": topics,
            "entities": entities
        }

