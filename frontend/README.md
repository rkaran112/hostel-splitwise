# Frontend

Next.js (App Router) + Tailwind CSS, mobile-first. Every page is a client component that calls the Python API.

```powershell
npm install
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"   # where the API runs
npm run dev                                          # http://localhost:3000
```

| Path | What it is |
|---|---|
| `app/page.tsx` | home: demo button, create a group, usage counter |
| `app/g/[id]/page.tsx` | one group: balances, expenses, add expense, people |
| `app/g/[id]/settle/page.tsx` | settle up: before/after picture, payment tickets, step-by-step walkthrough |
| `components/` | the pieces those pages use (form, ticket, diagram, stepper, loading/empty/error states) |
| `lib/api.ts` | the only file that talks to the API, plus the types of what it sends back |
| `lib/money.ts` | paise to rupees text, rupees text to paise (whole-number maths only) |
