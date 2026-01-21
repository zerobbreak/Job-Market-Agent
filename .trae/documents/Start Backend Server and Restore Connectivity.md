I will fix the connection errors by starting the backend server and ensuring the environment is correctly set up.

### 1. **Start the Backend Server**
The `net::ERR_CONNECTION_REFUSED` errors occur because the Python backend (port 8000) is not running.
- **Action**: Open a new terminal and start the server.
- **Command**: `python main.py`
- **Dependency Check**: I will first ensure all required packages are installed (`pip install -r requirements.txt`).

### 2. **Verify Appwrite Configuration**
The `401 Unauthorized` error from Appwrite suggests an authentication issue.
- **Action**: Once the backend is running, you should try **logging out and logging back in** on the frontend to refresh your session token.
- **Verification**: I will check that the frontend (`.env` or `vite.config.ts`) and backend (`.env`) are pointing to the same Appwrite project and endpoint.

### 3. **Frontend-Backend Connection**
- **Action**: The frontend is configured to talk to `http://localhost:8000/api`. Starting the backend will resolve the `Failed to fetch` errors in `RootLayout`, `Dashboard`, etc.

### Execution Steps
1.  Install dependencies: `pip install -r requirements.txt`
2.  Start the API server: `python main.py`
3.  (User Action) Refresh the browser and log in again.
