# Roll-Up Radar 🔎
### AI-Powered Acquisition Intelligence for Private Equity

Roll-Up Radar is a full-stack application designed to help private equity professionals identify promising acquisition targets, discover relationships between companies, evaluate acquisition fit, and explore potential roll-up strategies.

Built as part of the **Caprae Capital Full Stack Developer assignment**, the project focuses on turning company-level data into actionable insights through an interactive interface and data-driven analysis.

## 🎯 Business Problem

Identifying acquisition opportunities often requires reviewing large amounts of company information, evaluating strategic fit, and understanding how potential targets complement an existing portfolio.

Roll-Up Radar aims to simplify this process by bringing company analysis, relationship discovery, acquisition recommendations, and scenario exploration into one workspace.

### Key objectives
- Reduce the effort required to explore potential acquisition targets.
- Help users identify relationships and clusters among companies.
- Support more structured acquisition-fit evaluation.
- Explore how different acquisition decisions may affect a roll-up strategy.
- Make company insights easier to explore through an interactive interface.

## ✨ Features

### 1. Company Analysis
Upload company data in CSV format and explore the available company information through the application.

### 2. Relationship Discovery
Identify potential relationships between companies using the available company data and similarity-based analysis.

### 3. Company Clustering
Explore groups of related companies to identify potential acquisition ecosystems and consolidation opportunities.

### 4. Company Profile & Evidence Explorer
Inspect individual company profiles and review available supporting information to better understand potential opportunities.

### 5. Add-on Recommendations
Explore potential add-on acquisition opportunities that may complement an existing company or acquisition strategy.

### 6. Relationship Graph
Visualize relationships between companies to make potential connections and clusters easier to understand.

### 7. Acquisition Fit Engine
Evaluate potential acquisition targets using the application's acquisition-fit logic to support more structured comparisons.

### 8. Acquisition Strategy Simulator
Explore acquisition scenarios and compare potential strategic outcomes to understand how different choices may affect a roll-up strategy.

### 9. CSV Export
Export analysis results for further review, reporting, or offline analysis.

## 🧰 Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, JavaScript |
| UI and styling | Tailwind CSS |
| Animations | Framer Motion |
| Charts and visualization | Recharts and relationship graph components |
| Backend | Python, FastAPI |
| Data processing | Pandas |
| Company-name similarity | RapidFuzz |
| API support | REST APIs, Uvicorn |
| Data input/output | CSV upload and export |

## 🏗️ Architecture

Roll-Up Radar uses a frontend–backend architecture.

```text
                  User
                   |
                   v
        React + Vite Frontend
                   |
          HTTP / REST API
                   |
                   v
           FastAPI Backend
                   |
          Data Processing
           /           \
          v             v
   Company Analysis   Similarity
          |             |
          +------+------+
                 |
                 v
       Analysis and Results
                 |
                 v
        Interactive Frontend
                 |
                 v
          CSV Export
```

### Frontend
The React frontend provides the interactive workspace for uploading company data, exploring company profiles, viewing relationships, evaluating acquisition fit, and simulating acquisition strategies.

Vite provides the frontend development server and production build tooling.

### Backend
The FastAPI backend exposes API endpoints and processes company data. Pandas supports data manipulation, while RapidFuzz supports similarity-based matching.

### Data flow
1. The user uploads a company dataset through the frontend.
2. The frontend communicates with the backend through HTTP API requests.
3. The backend processes the available company information.
4. Analysis results are returned to the frontend.
5. The user explores results, compares opportunities, and exports relevant data.

*Note: The diagram represents the high-level architecture. Specific implementation details and individual API routes should be verified against the source code.*

## 📁 Project Structure

```text
roll-up-radar/
├── backend/
│   ├── main.py
│   └── sample_companies.csv
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docs/
├── .gitignore
└── README.md
```

The files shown above illustrate the intended structure. Additional source files, configuration files, and tests may exist in the actual project.

## ⚙️ Getting Started

### Prerequisites

Install the following:

- Python 3.10 or a compatible version supported by the backend dependencies.
- Node.js and npm.
- Git.

### 1. Clone the repository

```bash
git clone https://github.com/SunidhiVyas/roll-up-radar.git
cd roll-up-radar
```

### 2. Set up the backend

Open a terminal in the project root.

**Windows PowerShell:**

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi "uvicorn[standard]" pandas rapidfuzz python-multipart
```

If PowerShell blocks virtual-environment activation, use:

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi "uvicorn[standard]" pandas rapidfuzz python-multipart
```

Start the backend:

```powershell
python -m uvicorn main:app --reload
```

The backend should be available at:

`http://localhost:8000`

FastAPI interactive API documentation is normally available at:

`http://localhost:8000/docs`

If the project includes a `requirements.txt`, prefer installing its pinned dependencies with `python -m pip install -r requirements.txt`.

### 3. Set up the frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically:

`http://localhost:5173`

Keep both development servers running while using the application.

### 4. Try the sample dataset

Use the sample company CSV, if included in the repository, to explore the data-analysis workflow before uploading your own compatible dataset.

For reliable results, follow the column requirements expected by the application's CSV-processing code.

## 🔌 API and Configuration

The frontend communicates with the backend using HTTP requests. The FastAPI application provides the API documentation endpoint when the development server is running.

Before deploying the application, verify that:
- The frontend points to the correct backend URL.
- Cross-origin requests are configured appropriately.
- File-upload validation and error handling work as expected.
- Production environment variables are configured securely.

Do not commit API keys, passwords, or local `.env` files to GitHub.

## 🧪 Testing and Quality

The frontend has previously passed **52 unit tests**, and its production build completed successfully in the development environment.

Recommended verification before submission:
- Run the frontend test suite.
- Run the frontend lint command.
- Create a production frontend build.
- Test the backend endpoints and CSV-processing workflow.
- Verify the acquisition-fit and strategy-simulation features.
- Test CSV export and invalid-input handling.

Use the scripts defined in `frontend/package.json` and the actual backend test configuration when running these checks.

## 🚀 Deployment

The application can be deployed using separate frontend and backend services:

- **Frontend:** A static hosting platform capable of serving the production Vite build.
- **Backend:** A Python-compatible application hosting platform that supports FastAPI and Uvicorn.
- **Configuration:** Set the production API URL and configure CORS for the deployed frontend domain.

A deployment URL should be added here once the application has been deployed and verified.

## 🔮 Future Improvements

- Integrate external company and market-data sources.
- Add configurable acquisition-fit weights and evaluation criteria.
- Expand scenario comparisons with sensitivity analysis.
- Introduce user accounts and saved acquisition scenarios.
- Improve validation, explainability, and evidence traceability.
- Add additional automated backend tests and end-to-end tests.
- Explore secure persistence of saved analyses.

## ⚠️ Disclaimer

Roll-Up Radar is a decision-support prototype intended to assist with acquisition research and strategic exploration. Its results depend on the input data and implemented analytical logic. Outputs should be independently validated and should not be treated as investment, legal, tax, or financial advice.

## 👩‍💻 Author

**Sunidhi Vyas**

- GitHub: [SunidhiVyas](https://github.com/SunidhiVyas)
- Portfolio: [View Portfolio](https://portfolio-beryl-two-kdsfkznp8b.vercel.app/)
- LeetCode: [Sunidhi_Vyas](https://leetcode.com/u/Sunidhi_Vyas/)

---

*Developed as part of the Caprae Capital Full Stack Developer assignment.*