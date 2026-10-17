# Ripple console design

The investigation page scrolls as one document. Its zones are the hero and primary
action, incident summary, quiet statistics and decision stepper, dependency graph,
timeline/recovery columns, then action constraints. At tablet sizes the columns
stack; navigation becomes a keyboard-operated drawer at 900px and below.

`frontend/src/viewport.css` owns the presentation tokens and responsive layout.
The main text uses bundled Inter; IDs, timestamps and code use JetBrains Mono.
Font licenses ship in `frontend/public/fonts/`. There are no external font calls.

- Background: `#0A0F0D` to `#0D1512`; surface: `#111A16`.
- Accent: `#2DD4A7`; warning: `#F2C179`; failure/block: `#F3A3A3`.
- Body: 15–16px; secondary text: 14px; labels: at least 12px.
- Hero: 40–48px; section titles: 20–24px; card radius: 18px.
- Section spacing: 48px; column gaps: 24px; card padding: 24–32px.
- Graph canvas: 480px on desktop, 640px in the compact layout. Controls float in
  reserved space below the nodes, keeping every service label unobstructed.
- Main buttons and icon buttons have a minimum 44px target. Reduced-motion
  preferences disable entrance animation and transitions.

The two old banners are combined into one dismissible notice. The header retains
the Replay/Preview/Live status after dismissal. Recovery explanations, event
history, citations and policy text have no internal height cap. Evidence dialogs,
navigation drawers and horizontally wide result tables remain bounded as needed.

The palette audit reports WCAG AA normal-text contrast ratios of 15.47:1 for body
text, 8.01:1 for secondary text, 7.09:1 for labels, 8.24:1 for the primary button,
and 7.53:1 for graph metadata against its lighter node surface. These checks cover
the specified core palette, rather than claiming a complete accessibility certification.

Run `node frontend/scripts/audit-design.mjs` with the local backend serving the
compiled frontend. It checks font loading, minimum type size, document overflow,
graph readability and expanded evidence at 1440, 1366, 768, 390 and 360px widths;
screenshots go to `artifacts/`. Browser tests also cover drawer focus trapping,
Escape dismissal, scenarios, source inspection, disabled replay actions and the
existing late-response guard. Investigation handlers, data, API routes, model
behavior and simulator transitions are unchanged.
