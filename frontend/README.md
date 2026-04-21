# JARVIS Frontend

Next.js 14 + TypeScript frontend for the JARVIS AI Life Management System.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **Vercel** - Deployment platform

## Design

The UI follows the Jarvis laptop design:
- Purple gradient background (`#120122` → `#1a0132`)
- Translucent purple cards (`rgba(42, 7, 72, 0.4)`)
- Neon yellow buttons (`#FFC300`)
- Soft white text (`#F2EAFB`)
- Glow effects on interactive elements

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm start
```

### Deploy to Vercel

```bash
vercel
```

## Project Structure

```
frontend/
├── app/                 # Next.js App Router
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── ...              # Route pages
├── src/
│   ├── components/
│   │   ├── ui/          # shadcn/ui components
│   │   └── jarvis/      # Jarvis-specific components
│   ├── layout/          # Layout components (Sidebar, TopBar, etc.)
│   ├── lib/             # Utilities
│   └── api/             # API client
├── public/              # Static assets
├── next.config.js       # Next.js configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json         # Dependencies
```

## Backend Integration

The frontend expects the backend to be running on `http://localhost:8000`.

API endpoints:
- `GET /briefing/today` - Today's briefing
- `GET /finance/snapshot` - Financial snapshot
- `GET /agents/status` - Agent statuses
- `POST /query` - Send chat message

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_JARVIS_API_BASE=http://localhost:8000
```

## Deployment

- **Frontend**: Deployed on Vercel (Next.js)
- **Backend**: Hosted locally or on Railway/Cloud

## Architecture

- **Next.js 14 App Router** - File-based routing
- **Server Components** - Default for better performance
- **Client Components** - For interactivity (marked with 'use client')
- **API Routes** - Next.js API routes for backend integration

