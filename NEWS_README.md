# Latest News Aggregator

A Python program that fetches the latest news from multiple sources for today's date. The program aggregates news from various APIs and free sources, removes duplicates, and presents them in a structured format.

## Features

- **Multiple News Sources**: Fetches from NewsAPI, The Guardian, Hacker News, and Reddit WorldNews
- **Indian Sports Coverage**: Dedicated section for Indian sports news from Reddit Indian Sports and Cricket
- **Free Sources Available**: Works without API keys using Hacker News and Reddit
- **Duplicate Removal**: Intelligent duplicate detection based on title similarity
- **Today's Focus**: Filters news to show only articles from today
- **Flexible Output**: Display in terminal or save to JSON file
- **Sports Filtering**: Options to include, exclude, or show only Indian sports news
- **Rate Limiting**: Respectful API usage with proper rate limiting
- **Error Handling**: Robust error handling for network issues

## Quick Start

### 1. Install Dependencies

```bash
pip install -r news_requirements.txt
```

### 2. Run the Program

```bash
python news_aggregator.py
```

The program will work immediately using free sources (Hacker News and Reddit). For more comprehensive news coverage, see the API setup section below.

## Usage Examples

### Basic Usage
```bash
# Get latest news (default: 25 articles, includes Indian sports)
python news_aggregator.py

# Limit to 10 articles
python news_aggregator.py --max-articles 10

# Save articles to JSON file
python news_aggregator.py --save

# Save to custom filename
python news_aggregator.py --save --output my_news.json
```

### Indian Sports Options
```bash
# Get only Indian sports news
python news_aggregator.py --sports-only

# Get general news without Indian sports
python news_aggregator.py --no-sports

# Get Indian sports with limited articles
python news_aggregator.py --sports-only --max-articles 5
```

### Command Line Options

- `--max-articles N`: Maximum number of articles to display (default: 25)
- `--save`: Save articles to JSON file
- `--output FILENAME`: Custom output filename for saved articles
- `--sports-only`: Fetch only Indian sports news
- `--no-sports`: Exclude Indian sports news from general news

## News Sources

### Free Sources (No API Key Required)
- **Hacker News**: Top technology and startup stories
- **Reddit WorldNews**: Popular world news from Reddit community
- **Reddit Indian Sports**: Dedicated Indian sports community discussions
- **Reddit Cricket**: Cricket news filtered for India-related content

### API Sources (Optional - Requires Free API Keys)
- **NewsAPI**: Comprehensive news from 70,000+ sources worldwide
- **NewsAPI Sports**: Indian sports news when using sports-specific queries
- **The Guardian**: Quality journalism from The Guardian newspaper

## API Setup (Optional)

To get more comprehensive news coverage, you can set up free API keys:

### NewsAPI Setup
1. Visit [https://newsapi.org](https://newsapi.org)
2. Sign up for a free account (100 requests/day)
3. Get your API key
4. Set environment variable:
   ```bash
   export NEWS_API_KEY="your_api_key_here"
   ```

### The Guardian API Setup
1. Visit [https://open-platform.theguardian.com](https://open-platform.theguardian.com)
2. Register for a free developer key
3. Get your API key
4. Set environment variable:
   ```bash
   export GUARDIAN_API_KEY="your_api_key_here"
   ```

### Setting Environment Variables

#### macOS/Linux:
```bash
# Temporary (current session only)
export NEWS_API_KEY="your_newsapi_key"
export GUARDIAN_API_KEY="your_guardian_key"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export NEWS_API_KEY="your_newsapi_key"' >> ~/.bashrc
echo 'export GUARDIAN_API_KEY="your_guardian_key"' >> ~/.bashrc
```

#### Windows:
```cmd
# Temporary
set NEWS_API_KEY=your_newsapi_key
set GUARDIAN_API_KEY=your_guardian_key

# Permanent
setx NEWS_API_KEY "your_newsapi_key"
setx GUARDIAN_API_KEY "your_guardian_key"
```

## Output Format

### Terminal Display
The program displays news in a formatted, easy-to-read format:

```
📰 LATEST NEWS FOR 2025-07-28
📊 Found 45 unique articles
📋 Displaying top 25 articles
================================================================================

1. 📰 Breaking: Major Tech Company Announces New Product
   🏢 Source: NewsAPI
   ✍️  Author: John Doe
   📝 This is a description of the news article...
   🕒 Published: 2025-07-28 15:30:00
   🔗 URL: https://example.com/article
--------------------------------------------------------------------------------
```

### JSON Output
When using `--save`, articles are saved in structured JSON format:

```json
{
  "date": "2025-07-28",
  "total_articles": 45,
  "generated_at": "2025-07-28T23:49:26.123456",
  "articles": [
    {
      "title": "Article Title",
      "description": "Article description",
      "url": "https://example.com/article",
      "source": "NewsAPI",
      "published_at": "2025-07-28T15:30:00",
      "author": "John Doe"
    }
  ]
}
```

## Features in Detail

### Duplicate Detection
The program uses intelligent duplicate detection to remove similar articles:
- Compares article titles using word-based similarity
- Removes articles with >80% title similarity
- Keeps the most recent version of duplicate articles

### Date Filtering
- Focuses on today's news only
- For sources without date filtering, checks publication timestamps
- Includes articles from the last 24 hours

### Error Handling
- Graceful handling of network timeouts
- Continues operation even if some sources fail
- Clear error messages for troubleshooting

### Rate Limiting
- Respects API rate limits
- Implements delays between requests where needed
- Uses session management for efficient connections

## Troubleshooting

### Common Issues

1. **No articles found**
   - Check your internet connection
   - Verify that today's date has recent news
   - Try running without API keys to test free sources

2. **API key errors**
   - Verify environment variables are set correctly
   - Check that API keys are valid and active
   - Ensure you haven't exceeded rate limits

3. **Network timeouts**
   - Check internet connection
   - Some sources may be temporarily unavailable
   - The program will continue with available sources

4. **Permission errors when saving**
   - Ensure you have write permissions in the current directory
   - Try specifying a different output path

### Debug Mode
For troubleshooting, you can modify the script to add more verbose logging by uncommenting debug print statements.

## Customization

### Adding New Sources
To add new news sources, modify the `NewsAggregator` class:

1. Add source configuration to `news_sources` or `free_sources`
2. Create a new method like `get_source_news()`
3. Add the method call to `aggregate_all_news()`

### Changing Date Range
To fetch news from different date ranges, modify the date filtering logic in each source method.

### Custom Filtering
Add custom filtering logic in the `aggregate_all_news()` method to filter by keywords, categories, or other criteria.

## Dependencies

- **requests**: HTTP library for API calls
- **json**: JSON parsing (built-in)
- **datetime**: Date/time handling (built-in)
- **argparse**: Command-line argument parsing (built-in)
- **typing**: Type hints (built-in)

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to contribute by:
- Adding new news sources
- Improving duplicate detection
- Adding new output formats
- Enhancing error handling
- Adding tests

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify your setup follows the installation instructions
3. Ensure you have a stable internet connection
4. Check that any API keys are valid and active
