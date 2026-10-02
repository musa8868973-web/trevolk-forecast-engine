# Forecast Flow

Act as an expert Frontend Engineer and UI/UX Designer. Build a modern, ultra-minimal B2B SaaS dashboard for a Dynamic Sales Forecasting Engine.

DESIGN DIRECTION & AESTHETICS:

Theme: Premium Light Mode. Use crisp whites, very soft cool grays for backgrounds (e.g., bg-gray-50), and a modern primary color (like an elegant indigo or vivid blue) for accents.

Vibe: High-end, clean SaaS feel. Focus on lots of whitespace, refined typography (Inter or SF Pro), and subtle, soft borders instead of heavy shadows.

Animations (CRITICAL): The dashboard must feel alive and fluid. Use framer-motion (or Tailwind animations) extensively. Include staggered fade-in/slide-up entrance animations for all cards on page load, smooth hover effects on buttons and inputs, and a skeleton loading state when fetching data.

FUNCTIONAL REQUIREMENTS:

Input Panel (Sleek Sidebar or Floating Card): A beautifully spaced form with fields for Store ID (number input), Date (Date picker), Promo (Smooth Toggle switch), School Holiday (Smooth Toggle switch), and Competition Distance (number input). Include a prominent 'Generate Forecast' button that has a click animation and a spinning loading state.

Analytics Dashboard (Main Area):

Display a large, beautiful, fluid line chart using recharts to show 'Predicted Sales' over the upcoming week. The chart should have a subtle gradient fill underneath the line and animate on load.

Add 3 minimal KPI metric cards at the top (e.g., Expected Revenue, Optimal Price Adjustment, Confidence Score) that count up to their values.

API Logic: Add a mock API call function that sends the form data as JSON to http://localhost:8000/api/predict. When the button is clicked, trigger the loading state, simulate a delay, and then update the chart and KPIs

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/d5db6995-5808-40b9-88a1-87da99f1eacd).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
