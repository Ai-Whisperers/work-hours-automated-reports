# Work Hours Reports - Frontend

Next.js frontend for the Work Hours Automated Reports system.

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# or
yarn install
```

### Development

```bash
# Start development server
npm run dev

# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Features

- Real-time report generation status
- Service health monitoring
- Multiple report format support (Excel, HTML, JSON)
- Date range selection
- Dark theme UI with Tailwind CSS

## API Integration

The frontend connects to the FastAPI backend running on port 8000. The Next.js rewrites configuration proxies `/api/*` requests to `http://localhost:8000/api/*`.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Date Handling**: date-fns
