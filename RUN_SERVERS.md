# How to Run the MathFlow AI Tutor Servers

Follow these steps to start both the backend API and the frontend application.

## 🚀 Quick Start (Automated Scripts)

If you prefer to start things in one go, you can use these bundled scripts:

### For Linux / macOS
- **Start**: `./start_servers.sh`
- **Stop**: `./stop_servers.sh`

---

## 🛠️ Manual Start (Step-by-Step)

## 1. Start the Backend API (FastAPI)

1. Open a new terminal and navigate to the project root.
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
4. Start the FastAPI server using Uvicorn:
   ```bash
   python3 -m app.main
   ```
   - The API will be available at: `http://localhost:8000`
   - Interactive docs (Swagger): `http://localhost:8000/docs`

---

## 2. Start the Frontend Application (React + Vite)

1. Open a **second** terminal and navigate to the project root.
2. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
3. (Optional) If you haven't installed dependencies recently:
   ```bash
   npm install
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - The frontend will be available at: `http://localhost:5173`

---

## 3. How to Terminate the Servers

To stop either the backend or the frontend server, follow these steps in the respective terminal window:

1. Press `Ctrl + C` on your keyboard.
2. The terminal will return to the command prompt, indicating the server has stopped.

### Port Cleanup (If Needed)
If you find a port (8000 or 5173) is still in use after termination, you can kill the process using:
```bash
# For backend (8000)
fuser -k 8000/tcp

# For frontend (5173)
fuser -k 5173/tcp
```

---

## Port Summary
- **Backend API**: 8000
- **Frontend App**: 5173
- **ChromaDB**: Managed internally by the backend (persistent file storage).
