# 🕷️ Intelligent Web Crawler & Analyzer – Khan Academy

## 🔍 Overview
This project analyzes the crawlability and structure of [Khan Academy](https://www.khanacademy.org), extracting meaningful data and providing insights into accessing and navigating its content using crawling tools.

## 📦 Features

- ✅ robots.txt analysis (crawl delay, sitemaps, path permissions)
- ✅ HTML content extraction (titles from main categories)
- ✅ JS/API handling detection
- ✅ Streamlit dashboard for insights
- ⚠️ Recommendation of tools based on analysis

---

## 📁 Project Structure

```
├── streamlit_app.py
├── crawlability_summary.json
├── extracted_titles.json
├── api_test_output.txt
├── requirements.txt
└── README.md
```

## 🚀 Setup & Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Or deploy via [Streamlit Cloud](https://share.streamlit.io/)

---

## 💡 Findings

- **Crawlability**: Mostly allowed, with a clean sitemap.
- **APIs**: Internal APIs are not accessible via HTTP; JS rendering is required.
- **Extraction**: Basic content (titles, links) extractable using BeautifulSoup.

---

## 👥 Team Members & Roles

| Member | Role                          |
|--------|-------------------------------|
| 1      | Crawlability Specialist       |
| 2      | Content Extractor             |
| 3      | JS/API Handler                |
| 4      | Report & Dashboard Designer   |
| 5      | Documentation & Deployment    |

## 📌 Note

For deeper crawling (e.g. lesson content), use tools like Selenium or Playwright due to JS-heavy structure.
