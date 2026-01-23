# API Optimization Guide - Backend & Frontend Changes

This document outlines all the changes made to optimize the job matching API and prevent unnecessary API calls.

## 🔧 Backend Changes (Already Implemented)

### 1. ✅ Cache-First Strategy
**File:** `routes/job_routes.py`

- **GET requests** now return cached data or empty results (no automatic API calls)
- **POST with `force_refresh=True`** is required to trigger fresh job searches
- Prevents API calls on every page render

### 2. ✅ Location Validation
**File:** `routes/job_routes.py` (line 215-218)

```python
# Ensure location is never empty - use fallback to 'South Africa' if empty
location_str = (location or profile_data.get('location') or 'South Africa').strip()
if not location_str:
    location_str = 'South Africa'
```

**Fixes:** Invalid country string errors when location is empty

### 3. ✅ Request Deduplication
**File:** `routes/job_routes.py` (lines 33-35, 170-195)

Prevents duplicate API calls when the same request is made multiple times:
- Tracks in-flight requests by user_id, location, max_results, and min_score
- Returns 429 status if duplicate request detected
- Cleans up request tracking after 5 seconds

## 📱 Frontend Changes (Required Implementation)

### 1. Update API Call Pattern

#### ❌ **OLD WAY (Causes duplicate calls):**
```typescript
// DON'T DO THIS - Calls API on every render
useEffect(() => {
  fetchMatchJobs();
}, []);

const fetchMatchJobs = async () => {
  const response = await fetch('/api/match-jobs', {
    method: 'GET',  // This now returns cached data only
  });
  // ...
};
```

#### ✅ **NEW WAY (Only calls API when user clicks search):**
```typescript
// For initial load - just get cached data
useEffect(() => {
  fetchCachedMatches();
}, []);

// For user-initiated search - explicitly request fresh data
const handleSearch = async () => {
  await fetchFreshMatches();
};

const fetchCachedMatches = async () => {
  try {
    const response = await fetch('/api/match-jobs', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    
    if (data.success) {
      if (data.matches && data.matches.length > 0) {
        setJobs(data.matches);
      } else {
        // Show message: "No matches found. Click search to find new jobs."
        setMessage(data.message || 'No matches found. Click search to find new jobs.');
      }
    }
  } catch (error) {
    console.error('Error fetching cached matches:', error);
  }
};

const fetchFreshMatches = async (location?: string) => {
  try {
    setLoading(true);
    setError(null);
    
    const response = await fetch('/api/match-jobs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        force_refresh: true,  // REQUIRED to trigger API call
        location: location || '',
        max_results: 20,
        min_score: 0.0,
      }),
    });
    
    if (response.status === 429) {
      // Duplicate request - show message
      const data = await response.json();
      setError('Search already in progress. Please wait.');
      return;
    }
    
    const data = await response.json();
    
    if (data.success) {
      setJobs(data.matches || []);
      setMessage(null);
    } else {
      setError(data.error || 'Failed to fetch matches');
    }
  } catch (error) {
    console.error('Error fetching fresh matches:', error);
    setError('Failed to search for jobs');
  } finally {
    setLoading(false);
  }
};
```

### 2. Request Deduplication (Frontend)

#### Option A: Using React Hook with Debouncing
```typescript
import { useState, useRef, useCallback } from 'react';

const useMatchJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<string>('');

  const fetchFreshMatches = useCallback(async (location?: string) => {
    // Cancel previous request if still in progress
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Create request key for deduplication
    const requestKey = `${location || ''}_${Date.now()}`;
    
    // Prevent duplicate requests within 1 second
    if (lastRequestRef.current === requestKey) {
      console.log('Duplicate request prevented');
      return;
    }
    lastRequestRef.current = requestKey;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/match-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          force_refresh: true,
          location: location || '',
          max_results: 20,
          min_score: 0.0,
        }),
        signal: abortController.signal,
      });

      if (response.status === 429) {
        const data = await response.json();
        setError('Search already in progress. Please wait.');
        return;
      }

      const data = await response.json();

      if (!abortController.signal.aborted && data.success) {
        setJobs(data.matches || []);
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Error fetching matches:', error);
        setError('Failed to search for jobs');
      }
    } finally {
      if (!abortController.signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  return { jobs, loading, error, fetchFreshMatches };
};
```

#### Option B: Using a Custom Hook with Request Queue
```typescript
import { useState, useRef, useCallback } from 'react';

const useRequestQueue = () => {
  const queueRef = useRef<Map<string, Promise<any>>>(new Map());

  const enqueue = useCallback(async <T,>(
    key: string,
    requestFn: () => Promise<T>
  ): Promise<T> => {
    // If request is already in queue, return existing promise
    if (queueRef.current.has(key)) {
      return queueRef.current.get(key)!;
    }

    // Create new request
    const promise = requestFn().finally(() => {
      // Remove from queue after completion
      queueRef.current.delete(key);
    });

    queueRef.current.set(key, promise);
    return promise;
  }, []);

  return { enqueue };
};

// Usage in component
const { enqueue } = useRequestQueue();

const handleSearch = async () => {
  const requestKey = `match-jobs-${location}`;
  
  await enqueue(requestKey, async () => {
    return fetchFreshMatches(location);
  });
};
```

### 3. React Component Example

```typescript
import React, { useState, useEffect } from 'react';

interface JobMatch {
  job: {
    id: string;
    title: string;
    company: string;
    location: string;
    description: string;
    url: string;
  };
  match_score: number;
  match_reasons: string[];
}

const JobMatchesPage: React.FC = () => {
  const [jobs, setJobs] = useState<JobMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Load cached matches on mount
  useEffect(() => {
    loadCachedMatches();
  }, []);

  const loadCachedMatches = async () => {
    try {
      const response = await fetch('/api/match-jobs', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      });

      const data = await response.json();

      if (data.success) {
        if (data.matches && data.matches.length > 0) {
          setJobs(data.matches);
          setMessage(null);
        } else {
          // Show message from backend
          setMessage(data.message || 'No matches found. Click search to find new jobs.');
          setJobs([]);
        }
      }
    } catch (error) {
      console.error('Error loading cached matches:', error);
    }
  };

  const handleSearch = async (location?: string) => {
    if (isSearching) {
      return; // Prevent duplicate clicks
    }

    setIsSearching(true);
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('/api/match-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({
          force_refresh: true,  // REQUIRED
          location: location || '',
          max_results: 20,
          min_score: 0.0,
        }),
      });

      if (response.status === 429) {
        const data = await response.json();
        setError('Search already in progress. Please wait.');
        return;
      }

      const data = await response.json();

      if (data.success) {
        setJobs(data.matches || []);
        if (data.matches.length === 0) {
          setMessage('No jobs found matching your criteria.');
        }
      } else {
        setError(data.error || 'Failed to search for jobs');
      }
    } catch (error: any) {
      console.error('Error searching jobs:', error);
      setError('Failed to search for jobs. Please try again.');
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  return (
    <div>
      <h1>Job Matches</h1>
      
      {/* Search Button - Only triggers API call */}
      <button 
        onClick={() => handleSearch()} 
        disabled={isSearching || loading}
      >
        {isSearching ? 'Searching...' : 'Search for Jobs'}
      </button>

      {/* Show message if no cached matches */}
      {message && (
        <div className="info-message">
          {message}
        </div>
      )}

      {/* Show error */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Show loading state */}
      {loading && (
        <div>Loading matches...</div>
      )}

      {/* Display jobs */}
      {jobs.length > 0 && (
        <div className="jobs-list">
          {jobs.map((match) => (
            <div key={match.job.id} className="job-card">
              <h3>{match.job.title}</h3>
              <p>{match.job.company}</p>
              <p>Match Score: {match.match_score}%</p>
              <a href={match.job.url} target="_blank" rel="noopener noreferrer">
                View Job
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobMatchesPage;
```

### 4. Prevent React Strict Mode Double Calls

If you're using React 18+ with Strict Mode, it may cause double renders in development:

```typescript
// Option 1: Disable Strict Mode in production
// In your main.tsx or index.tsx:
if (process.env.NODE_ENV === 'production') {
  // Don't use StrictMode in production
  root.render(<App />);
} else {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

// Option 2: Use a ref to prevent double calls
const hasMountedRef = useRef(false);

useEffect(() => {
  if (hasMountedRef.current) return;
  hasMountedRef.current = true;
  
  loadCachedMatches();
}, []);
```

### 5. Debounce Search Input (If applicable)

If you have a search input that triggers API calls:

```typescript
import { useDebouncedCallback } from 'use-debounce';

const [searchLocation, setSearchLocation] = useState('');

const debouncedSearch = useDebouncedCallback(
  (location: string) => {
    handleSearch(location);
  },
  500 // Wait 500ms after user stops typing
);

const handleLocationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const location = e.target.value;
  setSearchLocation(location);
  // Don't auto-search - only search on button click
  // debouncedSearch(location); // Only if you want auto-search
};
```

## 📋 Summary of Changes

### Backend ✅
- [x] Cache-first strategy (GET returns cached, POST with force_refresh triggers API)
- [x] Location validation (prevents empty country string errors)
- [x] Request deduplication (prevents duplicate API calls)

### Frontend Required Changes 📱
- [ ] Update API calls to use GET for cached data
- [ ] Use POST with `force_refresh: true` only when user clicks search
- [ ] Implement request deduplication/debouncing
- [ ] Handle 429 status (duplicate request)
- [ ] Show appropriate messages when no cached matches exist
- [ ] Prevent duplicate button clicks during search

## 🧪 Testing Checklist

- [ ] Initial page load shows cached matches (no API call)
- [ ] Clicking search button triggers API call (POST with force_refresh)
- [ ] Multiple rapid clicks don't cause duplicate API calls
- [ ] Empty location doesn't cause errors
- [ ] 429 status is handled gracefully
- [ ] Error messages are displayed correctly
- [ ] Loading states work properly

## 📝 API Response Examples

### GET /api/match-jobs (Cached)
```json
{
  "success": true,
  "matches": [...],
  "location": "South Africa",
  "cached": true,
  "created_at": "2026-01-22T14:28:17Z",
  "last_seen": "2026-01-22T14:46:30Z"
}
```

### GET /api/match-jobs (No Cache)
```json
{
  "success": true,
  "matches": [],
  "location": "",
  "cached": false,
  "message": "No matches found. Click search to find new jobs."
}
```

### POST /api/match-jobs (Fresh Search)
```json
{
  "success": true,
  "matches": [...],
  "location": "South Africa",
  "cached": false,
  "matching_method": "semantic_ai"
}
```

### POST /api/match-jobs (Duplicate Request)
```json
{
  "success": false,
  "error": "Request already in progress. Please wait.",
  "in_progress": true
}
```
Status: 429
