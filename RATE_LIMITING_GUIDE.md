# API Rate Limiting & Quota Management Guide

## 🎯 Problem Solved

Your application was hitting **429 RESOURCE_EXHAUSTED** errors because:
- Multiple agents making API calls simultaneously
- No delays between consecutive API calls
- No quota management or usage tracking
- Generic retry logic that didn't handle rate limits properly

## ✅ Solutions Implemented

### 1. **Intelligent Rate Limiting**
- **Minimum delay** between API calls (2 seconds by default)
- **Agent delays** between different agent calls (3 seconds)
- **Automatic quota tracking** (daily/hourly limits)
- **Smart backoff** based on error type

### 2. **Advanced Error Handling**
- **Error classification**: Rate limits, auth errors, server errors
- **Contextual retry delays**: 2 minutes for rate limits vs 2 seconds for server errors
- **Graceful degradation**: Fallback responses when API fails
- **Usage tracking**: Monitor daily/hourly API consumption

### 3. **Quota Management**
- **Daily limits**: 50 API calls (configurable)
- **Hourly limits**: 15 API calls (configurable)
- **Automatic resets**: Counters reset at midnight/hour boundaries
- **Quota exceeded protection**: Prevents API calls when limits reached

## 🔧 Configuration

Add these to your `.env` file for optimal performance:

```env
# Conservative API limits (adjust based on your Gemini tier)
API_DAILY_QUOTA=50      # Max calls per day
API_HOURLY_QUOTA=15     # Max calls per hour
API_MIN_DELAY=2.0       # Delay between calls
API_RATE_LIMIT_DELAY=120.0  # Delay for 429 errors
API_AGENT_DELAY=3.0     # Delay between agents
```

## 📊 Monitoring API Usage

The application now shows API usage statistics:

```
📊 API Usage Summary:
   Daily calls: 12/50 (24.0%)
   Hourly calls: 5/15 (33.3%)
   Rate limit hits: 0
```

## 🛡️ Error Recovery

### Rate Limit Hits (429)
- **Automatic retry** with 2-minute delay
- **Exponential backoff** for multiple failures
- **Fallback responses** if retries exhausted

### Quota Exceeded
- **Graceful degradation** to cached/fallback responses
- **Clear warnings** about quota status
- **Automatic quota reset** detection

### Network/Server Issues
- **Standard retry** with exponential backoff
- **Detailed error logging**
- **Continued operation** with fallbacks

## 🎛️ Tuning for Your Usage

### Free Tier Gemini Users:
```env
API_DAILY_QUOTA=30
API_HOURLY_QUOTA=10
API_MIN_DELAY=3.0
API_AGENT_DELAY=5.0
```

### Paid Tier Users:
```env
API_DAILY_QUOTA=200
API_HOURLY_QUOTA=50
API_MIN_DELAY=1.0
API_AGENT_DELAY=2.0
```

### High-Volume Users:
```env
API_DAILY_QUOTA=1000
API_HOURLY_QUOTA=100
API_MIN_DELAY=0.5
API_AGENT_DELAY=1.0
```

## 🚦 Best Practices

1. **Start Conservative**: Use lower limits initially
2. **Monitor Usage**: Check the API usage summary after runs
3. **Adjust Gradually**: Increase limits as you understand your patterns
4. **Cache Effectively**: Leverage caching to reduce API calls
5. **Batch Processing**: Consider processing multiple items together

## 🔍 Troubleshooting

### Still Getting Rate Limits?
- **Increase delays**: `API_MIN_DELAY=5.0`, `API_AGENT_DELAY=10.0`
- **Reduce concurrent calls**: Lower daily/hourly quotas
- **Check Gemini dashboard**: Monitor actual usage vs limits

### Too Many Fallbacks?
- **Check API key validity**: Ensure key is active and has quota
- **Verify network**: Stable internet connection required
- **Review error logs**: Look for authentication or permission issues

### Performance Too Slow?
- **Reduce delays**: Lower `API_MIN_DELAY` and `API_AGENT_DELAY`
- **Increase quotas**: If you have higher Gemini limits
- **Optimize caching**: Ensure cache is working effectively

---

**Result**: Your application now handles API limits gracefully while maintaining full functionality! 🎉
