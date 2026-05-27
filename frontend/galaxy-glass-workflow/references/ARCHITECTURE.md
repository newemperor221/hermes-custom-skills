# Architecture of the GalaxyGlass project. Full details at the project's ARCHITECTURE.md.

Architecture: see project repository's ARCHITECTURE.md for full details on the ITCSS CSS architecture, build pipeline, JS architecture, deployment architecture, and development workflow. This copy is a session-specific snapshot for agent context.

Key points: ITCSS layered CSS (settings→base→layout→components→states→utilities→web→mobile), single-file app.js (IIFE), build.sh compiles src/ into index.html with {{CSS}}{{JS}}{{BODY}} placeholders, deploy.sh does build + scp to both GalaxyGlass/dist/ and theme/ root.