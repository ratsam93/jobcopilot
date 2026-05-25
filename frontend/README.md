# Job Copilot Frontend

React + Vite frontend for the Job Copilot backend.

## Run

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

For local-only login autofill, set these Vite environment variables in your shell or a local `frontend/.env` file:

```bash
VITE_JOBCOPILOT_DEV_EMAIL=your-dev-admin@example.com
VITE_JOBCOPILOT_DEV_PASSWORD=your-dev-password
```

Production builds leave the login form blank unless a user has a saved session email.
