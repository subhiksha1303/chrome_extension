import re
import requests
import json
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from difflib import SequenceMatcher  # For text similarity checking
import nltk
from bs4 import BeautifulSoup

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab")

# ✅ Home Page Function
def home(request):
   return JsonResponse({"message": "Bias Buster API is live!"})

def extract_news_from_text(text):
    """Remove extra spaces and clean extracted text."""
    return " ".join(text.split())

def extract_news_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return None, f"Error fetching URL: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text from <p> tags inside article sections
        paragraphs = soup.find_all("p")
        article_text = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 30])

        if not article_text:
            return None, "No readable content found in the article."

        return extract_news_from_text(article_text), None
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"
    
# ✅ List of Trusted News Sources
TRUSTED_SOURCES = {
    "bbc.com", "cnn.com", "reuters.com", "theguardian.com", "nytimes.com",
    "aljazeera.com", "washingtonpost.com", "ndtv.com", "indiatoday.in",
    "timesofindia.indiatimes.com", "business-standard.com", "news18.com",
    "thehindu.com", "firstpost.com", "scroll.in", "theprint.in"
}

# ✅ Function to Check if a News Source is Trusted
def is_trusted_source(url):
    return any(source in url for source in TRUSTED_SOURCES)

# ✅ Function to Extract Keywords from Text
def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stopwords = {"the", "is", "in", "a", "an", "on", "of", "and", "to", "for", "with"}
    return " ".join([word for word in words if word not in stopwords][:8])

# ✅ Function to Check Similarity Between Two Texts
def text_similarity(text1, text2):
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

# ✅ Function to Fetch News from External APIs
GOOGLE_API_KEY = "AIzaSyD0RJdZ3NtQAI9Y2KqSiTdcfK3a0ulMHf0" 
GOOGLE_CSE_ID = "86f38c27f03df4661" 

def fetch_news_google(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_CSE_ID}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return response.json().get("items", [])

NEWS_API_KEY = "e242defe23904eee96b22acfb4d1ecee"  
NEWS_API_URL = "https://newsapi.org/v2/everything"

def fetch_news_newsapi(query):
    params = {"q": query, "apiKey": NEWS_API_KEY, "language": "en", "pageSize": 5}
    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code != 200:
        return []
    return response.json().get("articles", [])

# ✅ API Endpoint for News Analysis
@api_view(["POST", "GET"])
@csrf_exempt
def analyze_news(request):
    try:
        data = json.loads(request.body)
        news_text = data.get("news_text", "").strip()

        if not news_text:
            return JsonResponse({"status": "error", "message": "News text is required."}, status=400)

        keyword_query = extract_keywords(news_text)
        
        # Fetch news from both APIs
        google_news = fetch_news_google(keyword_query)
        newsapi_news = fetch_news_newsapi(keyword_query)

        all_articles = google_news + newsapi_news
        perspectives = []
        trusted_source_found = False

        if all_articles:
            for article in all_articles[:5]:  
                title = article.get("title", "")
                url = article.get("link", article.get("url", ""))
                source_name = article.get("displayLink", article.get("source", {}).get("name", "Unknown"))
                
                is_trusted = is_trusted_source(url)
                if is_trusted:
                    trusted_source_found = True
                
                # Check if the article is relevant
                similarity_score = text_similarity(news_text, title)
                if similarity_score < 0.5:  # Ignore unrelated articles
                    continue

                perspectives.append({
                    "source": source_name,
                    "title": title,
                    "url": url,
                })

            return JsonResponse({
                "status": "real" if trusted_source_found else "fake",
                "message": "News verified. Here are different perspectives:",
                "unbiased_news": news_text,  # Send full unbiased news
                "perspectives": perspectives
            })
        
        return JsonResponse({"status": "fake", "message": "No reliable sources found."})
    
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON input."}, status=400)
