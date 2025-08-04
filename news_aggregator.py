#!/usr/bin/env python3
"""
Latest News Aggregator

This script fetches the latest news from multiple sources for today's date.
It aggregates news from various APIs and presents them in a structured format.
"""

import requests
import json
from datetime import datetime, timedelta
import time
import os
from typing import List, Dict, Optional
import argparse


class NewsAggregator:
    """News aggregation class that fetches news from multiple sources."""
    
    def __init__(self):
        self.news_sources = {
            'newsapi': {
                'url': 'https://newsapi.org/v2/top-headlines',
                'api_key_env': 'NEWS_API_KEY',
                'params': {
                    'country': 'us',
                    'pageSize': 20,
                    'sortBy': 'publishedAt'
                }
            },
            'guardian': {
                'url': 'https://content.guardianapis.com/search',
                'api_key_env': 'GUARDIAN_API_KEY',
                'params': {
                    'page-size': 20,
                    'order-by': 'newest',
                    'show-fields': 'headline,byline,thumbnail,short-url'
                }
            }
        }
        
        # Free news sources that don't require API keys
        self.free_sources = {
            'hacker_news': 'https://hacker-news.firebaseio.com/v0/topstories.json',
            'reddit_worldnews': 'https://www.reddit.com/r/worldnews/hot.json?limit=20',
            'reddit_india_sports': 'https://www.reddit.com/r/IndianSports/hot.json?limit=15',
            'reddit_cricket': 'https://www.reddit.com/r/Cricket/hot.json?limit=15'
        }
        
        # Indian sports news sources
        self.indian_sports_sources = {
            'espn_cricinfo': 'https://www.espncricinfo.com/ci/content/rss/feeds_rss_cricket.xml',
            'sportskeeda_api': 'https://www.sportskeeda.com/api/v1/articles?category=cricket&country=india&limit=10'
        }
        
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NewsAggregator/1.0 (Python News Fetcher)'
        })

    def get_newsapi_news(self) -> List[Dict]:
        """Fetch news from NewsAPI.org"""
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            print("⚠️  NewsAPI key not found. Set NEWS_API_KEY environment variable.")
            return []
        
        try:
            params = self.news_sources['newsapi']['params'].copy()
            params['apiKey'] = api_key
            params['from'] = self.today
            
            response = self.session.get(
                self.news_sources['newsapi']['url'], 
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                if article.get('title') and article.get('title') != '[Removed]':
                    articles.append({
                        'title': article['title'],
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', 'NewsAPI'),
                        'published_at': article.get('publishedAt', ''),
                        'author': article.get('author', 'Unknown')
                    })
            
            print(f"✅ Fetched {len(articles)} articles from NewsAPI")
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from NewsAPI: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing NewsAPI response: {e}")
            return []

    def get_guardian_news(self) -> List[Dict]:
        """Fetch news from The Guardian API"""
        api_key = os.getenv('GUARDIAN_API_KEY')
        if not api_key:
            print("⚠️  Guardian API key not found. Set GUARDIAN_API_KEY environment variable.")
            return []
        
        try:
            params = self.news_sources['guardian']['params'].copy()
            params['api-key'] = api_key
            params['from-date'] = self.today
            
            response = self.session.get(
                self.news_sources['guardian']['url'],
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('response', {}).get('results', []):
                articles.append({
                    'title': article.get('webTitle', ''),
                    'description': article.get('fields', {}).get('headline', ''),
                    'url': article.get('webUrl', ''),
                    'source': 'The Guardian',
                    'published_at': article.get('webPublicationDate', ''),
                    'author': article.get('fields', {}).get('byline', 'Unknown')
                })
            
            print(f"✅ Fetched {len(articles)} articles from The Guardian")
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Guardian: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Guardian response: {e}")
            return []

    def get_hacker_news(self) -> List[Dict]:
        """Fetch top stories from Hacker News"""
        try:
            # Get top story IDs
            response = self.session.get(self.free_sources['hacker_news'], timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:15]  # Get top 15 stories
            
            articles = []
            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_response = self.session.get(story_url, timeout=5)
                    story_response.raise_for_status()
                    story = story_response.json()
                    
                    if story and story.get('type') == 'story' and story.get('title'):
                        # Check if story is from today (within last 24 hours)
                        story_time = datetime.fromtimestamp(story.get('time', 0))
                        if (datetime.now() - story_time).days <= 1:
                            articles.append({
                                'title': story['title'],
                                'description': f"Score: {story.get('score', 0)} | Comments: {story.get('descendants', 0)}",
                                'url': story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                                'source': 'Hacker News',
                                'published_at': story_time.isoformat(),
                                'author': story.get('by', 'Unknown')
                            })
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except requests.exceptions.RequestException:
                    continue
            
            print(f"✅ Fetched {len(articles)} articles from Hacker News")
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Hacker News: {e}")
            return []

    def get_reddit_news(self) -> List[Dict]:
        """Fetch news from Reddit WorldNews"""
        try:
            response = self.session.get(self.free_sources['reddit_worldnews'], timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                if post_data.get('title') and not post_data.get('stickied', False):
                    # Check if post is from today
                    post_time = datetime.fromtimestamp(post_data.get('created_utc', 0))
                    if (datetime.now() - post_time).days <= 1:
                        articles.append({
                            'title': post_data['title'],
                            'description': f"Score: {post_data.get('score', 0)} | Comments: {post_data.get('num_comments', 0)}",
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'source': 'Reddit WorldNews',
                            'published_at': post_time.isoformat(),
                            'author': post_data.get('author', 'Unknown')
                        })
            
            print(f"✅ Fetched {len(articles)} articles from Reddit")
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Reddit: {e}")
            return []

    def get_indian_sports_news(self) -> List[Dict]:
        """Fetch Indian sports news from Reddit sources"""
        articles = []
        
        # Fetch from Reddit Indian Sports
        try:
            response = self.session.get(self.free_sources['reddit_india_sports'], timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                if post_data.get('title') and not post_data.get('stickied', False):
                    # Check if post is from today
                    post_time = datetime.fromtimestamp(post_data.get('created_utc', 0))
                    if (datetime.now() - post_time).days <= 1:
                        articles.append({
                            'title': post_data['title'],
                            'description': f"🏏 Indian Sports | Score: {post_data.get('score', 0)} | Comments: {post_data.get('num_comments', 0)}",
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'source': 'Reddit Indian Sports',
                            'published_at': post_time.isoformat(),
                            'author': post_data.get('author', 'Unknown'),
                            'category': 'Indian Sports'
                        })
            
            print(f"✅ Fetched {len(articles)} articles from Reddit Indian Sports")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Reddit Indian Sports: {e}")
        
        # Fetch from Reddit Cricket
        try:
            response = self.session.get(self.free_sources['reddit_cricket'], timeout=10)
            response.raise_for_status()
            
            data = response.json()
            cricket_articles = 0
            
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                if post_data.get('title') and not post_data.get('stickied', False):
                    # Check if post is from today and contains India-related keywords
                    post_time = datetime.fromtimestamp(post_data.get('created_utc', 0))
                    title_lower = post_data['title'].lower()
                    
                    # Filter for India-related cricket news
                    india_keywords = ['india', 'indian', 'bcci', 'kohli', 'rohit', 'dhoni', 'ipl', 'mumbai indians', 'csk', 'rcb']
                    is_india_related = any(keyword in title_lower for keyword in india_keywords)
                    
                    if (datetime.now() - post_time).days <= 1 and is_india_related:
                        articles.append({
                            'title': post_data['title'],
                            'description': f"🏏 Cricket | Score: {post_data.get('score', 0)} | Comments: {post_data.get('num_comments', 0)}",
                            'url': f"https://reddit.com{post_data.get('permalink', '')}",
                            'source': 'Reddit Cricket',
                            'published_at': post_time.isoformat(),
                            'author': post_data.get('author', 'Unknown'),
                            'category': 'Cricket'
                        })
                        cricket_articles += 1
            
            print(f"✅ Fetched {cricket_articles} India-related articles from Reddit Cricket")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching from Reddit Cricket: {e}")
        
        return articles

    def get_newsapi_indian_sports(self) -> List[Dict]:
        """Fetch Indian sports news from NewsAPI if available"""
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            return []
        
        try:
            params = {
                'apiKey': api_key,
                'q': 'India sports OR cricket OR IPL OR hockey OR badminton OR kabaddi',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 15,
                'from': self.today
            }
            
            response = self.session.get(
                'https://newsapi.org/v2/everything',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                if article.get('title') and article.get('title') != '[Removed]':
                    articles.append({
                        'title': article['title'],
                        'description': f"🏏 {article.get('description', '')}",
                        'url': article.get('url', ''),
                        'source': f"NewsAPI Sports ({article.get('source', {}).get('name', 'Unknown')})",
                        'published_at': article.get('publishedAt', ''),
                        'author': article.get('author', 'Unknown'),
                        'category': 'Indian Sports'
                    })
            
            print(f"✅ Fetched {len(articles)} Indian sports articles from NewsAPI")
            return articles
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching Indian sports from NewsAPI: {e}")
            return []

    def aggregate_all_news(self, include_sports: bool = True) -> List[Dict]:
        """Aggregate news from all available sources"""
        print(f"🔍 Fetching latest news for {self.today}...")
        if include_sports:
            print("🏏 Including Indian sports news...")
        print("=" * 50)
        
        all_articles = []
        
        # Fetch from API sources
        all_articles.extend(self.get_newsapi_news())
        all_articles.extend(self.get_guardian_news())
        
        # Fetch from free sources
        all_articles.extend(self.get_hacker_news())
        all_articles.extend(self.get_reddit_news())
        
        # Fetch Indian sports news if requested
        if include_sports:
            all_articles.extend(self.get_indian_sports_news())
            all_articles.extend(self.get_newsapi_indian_sports())
        
        # Remove duplicates based on title similarity
        unique_articles = self.remove_duplicates(all_articles)
        
        # Sort by publication date (newest first)
        unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_articles

    def get_sports_only(self) -> List[Dict]:
        """Get only Indian sports news"""
        print(f"🏏 Fetching Indian sports news for {self.today}...")
        print("=" * 50)
        
        all_articles = []
        
        # Fetch Indian sports news
        all_articles.extend(self.get_indian_sports_news())
        all_articles.extend(self.get_newsapi_indian_sports())
        
        # Remove duplicates based on title similarity
        unique_articles = self.remove_duplicates(all_articles)
        
        # Sort by publication date (newest first)
        unique_articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_articles

    def remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title_lower = article['title'].lower()
            # Simple duplicate detection - check if title is too similar
            is_duplicate = False
            for seen_title in seen_titles:
                if self.similarity_ratio(title_lower, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(title_lower)
        
        return unique_articles

    def similarity_ratio(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings"""
        if not str1 or not str2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def display_news(self, articles: List[Dict], max_articles: Optional[int] = None):
        """Display news articles in a formatted way"""
        if not articles:
            print("❌ No news articles found for today.")
            return
        
        display_articles = articles[:max_articles] if max_articles else articles
        
        print(f"\n📰 LATEST NEWS FOR {self.today.upper()}")
        print(f"📊 Found {len(articles)} unique articles")
        if max_articles and len(articles) > max_articles:
            print(f"📋 Displaying top {max_articles} articles")
        print("=" * 80)
        
        for i, article in enumerate(display_articles, 1):
            print(f"\n{i}. 📰 {article['title']}")
            print(f"   🏢 Source: {article['source']}")
            if article.get('author') and article['author'] != 'Unknown':
                print(f"   ✍️  Author: {article['author']}")
            if article.get('description'):
                print(f"   📝 {article['description'][:200]}{'...' if len(article.get('description', '')) > 200 else ''}")
            if article.get('published_at'):
                try:
                    pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    print(f"   🕒 Published: {pub_date.strftime('%Y-%m-%d %H:%M:%S')}")
                except:
                    print(f"   🕒 Published: {article['published_at']}")
            if article.get('url'):
                print(f"   🔗 URL: {article['url']}")
            print("-" * 80)

    def save_to_file(self, articles: List[Dict], filename: str = None):
        """Save articles to a JSON file"""
        if not filename:
            filename = f"news_{self.today.replace('-', '_')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'date': self.today,
                    'total_articles': len(articles),
                    'generated_at': datetime.now().isoformat(),
                    'articles': articles
                }, f, indent=2, ensure_ascii=False)
            
            print(f"💾 News saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving to file: {e}")


def main():
    """Main function to run the news aggregator"""
    parser = argparse.ArgumentParser(description='Fetch latest news for today')
    parser.add_argument('--max-articles', type=int, default=25, 
                       help='Maximum number of articles to display (default: 25)')
    parser.add_argument('--save', action='store_true', 
                       help='Save articles to JSON file')
    parser.add_argument('--output', type=str, 
                       help='Output filename for saved articles')
    parser.add_argument('--sports-only', action='store_true',
                       help='Fetch only Indian sports news')
    parser.add_argument('--no-sports', action='store_true',
                       help='Exclude Indian sports news from general news')
    
    args = parser.parse_args()
    
    # Display setup instructions
    print("🚀 NEWS AGGREGATOR")
    if args.sports_only:
        print("🏏 INDIAN SPORTS MODE")
    print("=" * 50)
    print("📋 Setup Instructions:")
    print("   For more news sources, set these environment variables:")
    print("   • NEWS_API_KEY: Get free key from https://newsapi.org")
    print("   • GUARDIAN_API_KEY: Get free key from https://open-platform.theguardian.com")
    print("   📝 Note: The program works without API keys using free sources!")
    if not args.sports_only:
        print("   🏏 Indian sports news is included by default!")
    print("=" * 50)
    
    # Initialize and run aggregator
    aggregator = NewsAggregator()
    
    # Determine which articles to fetch
    if args.sports_only:
        articles = aggregator.get_sports_only()
    else:
        include_sports = not args.no_sports
        articles = aggregator.aggregate_all_news(include_sports=include_sports)
    
    # Display results
    aggregator.display_news(articles, args.max_articles)
    
    # Save to file if requested
    if args.save:
        aggregator.save_to_file(articles, args.output)
    
    print(f"\n✅ News aggregation complete! Found {len(articles)} articles for today.")


if __name__ == "__main__":
    main()
