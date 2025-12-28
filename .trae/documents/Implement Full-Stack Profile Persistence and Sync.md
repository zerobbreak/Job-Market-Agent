I will implement a robust "Full-Stack Data Persistence and Synchronization" solution to resolve the profile data issues. This involves fixing both the frontend state synchronization and the backend data storage to ensure extracted CV data (Name, Email, Phone, Location, etc.) is correctly saved and reloaded.

### Phase 1: Frontend State Synchronization (React)
The Profile page currently initializes its form state only once on mount. Since the profile data loads asynchronously, the form remains empty even after data arrives.
- **Action**: Modify `src/pages/Profile.tsx` to implement a `useEffect` hook that actively watches for changes in the `profile` context.
- **Logic**: When the `profile` data becomes available, the effect will automatically update the `editForm` state, ensuring the UI reflects the loaded data immediately.

### Phase 2: Backend Data Persistence (Python/Appwrite)
The current backend implementation successfully extracts `name`, `email`, `phone`, and `location` from the CV but **fails to save them** to the database. It only saves `skills`, `education`, etc.
- **Step 1: Schema Update**: Modify `ensure_database_schema` in `main.py` to add new string attributes (`name`, `email`, `phone`, `location`) to the Appwrite `profiles` collection.
- **Step 2: Save Logic**: Update the `analyze_cv` endpoint in `main.py` to persist these extracted fields into the database when a CV is uploaded.
- **Step 3: Retrieval Logic**: Update the `get_structured_profile` endpoint in `main.py` to include these fields in the API response, ensuring the frontend receives the full profile.

### Verification
1.  **Restart Backend**: To apply schema changes and new logic.
2.  **Reload Frontend**: To test the new synchronization hook.
3.  **Upload CV**: Verify that all fields (including Name and Location) are extracted and displayed.
4.  **Refresh Page**: Verify that all data persists after a page reload (proving DB storage works).
