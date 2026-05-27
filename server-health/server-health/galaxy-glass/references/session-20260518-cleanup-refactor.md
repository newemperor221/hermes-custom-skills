# 2026-05-18 Session: Dep Cleanup + Style Unification

## Removed Unused Dependencies

Deleted from `package.json` (none were used in production code):

- `@react-three/fiber` + `@react-three/drei` + `three` — Three.js stack, no 3D content
- `@squircle-js/react` + `figma-squircle` — Squircle shape libs, unused (CSS `corner-shape` used instead)
- `gsap` + `ScrollTrigger` — animation migrated to Framer Motion

## GSAP → Framer Motion Migration

The stats bar entrance animation was the only GSAP/ScrollTrigger usage:

**Before (GSAP):**
```tsx
const statsRef = useRef(null);
useEffect(() => {
  gsap.fromTo(cards, { y: 24, opacity: 0 }, {
    y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: "power2.out",
    scrollTrigger: { trigger: statsRef.current, start: "top 88%" },
  });
}, [loading]);
```

**After (Framer Motion):**
```tsx
<motion.div
  initial={{ opacity: 0, y: 16 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: false, margin: "-50px" }}
  transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1], staggerChildren: 0.08 }}
>
  <motion.div variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}><StatCard ... /></motion.div>
  ...
</motion.div>
```

layout.tsx GSAP `ScrollTrigger.config` removed. `gsap` and `gsap/ScrollTrigger` removed from page.tsx imports.

## Tailwind v4 Glass Color Variables Added

Added to `globals.css` `@theme` block so Tailwind utility classes work:

```css
--color-glass-bg: rgba(255,255,255,0.06);
--color-glass-border: rgba(255,255,255,0.10);
--color-glass-raised: rgba(255,255,255,0.10);
```

Now these work: `bg-glass-bg/6`, `border-glass-border/10`, `text-glass-bg/6`, `bg-glass-raised/10`

Old `var(--glass-bg)` CSS vars are kept as fallbacks.

### Key Tailwind conversions done this session:

| Pattern | Old (inline) | New (Tailwind) |
|---------|-------------|----------------|
| Glass card background | `style={{background:"rgba(255,255,255,0.06)", borderRadius:12, backdropFilter:"blur(12px)", border:"1px solid var(--glass-border)"}}` | `className="rounded-[12px] bg-glass-bg/6 backdrop-blur-[12px] border border-glass-border/10"` |
| Text muted | `style={{color:"var(--color-text-muted)"}}` | `text-text-muted` |
| Text accent | `style={{color:"var(--accent)"}}` | `text-accent` |
| Text secondary | `style={{color:"var(--text-secondary)"}}` | `text-text-secondary` |
| Nav button | `style={{border:"1px solid var(--glass-border)", background:"var(--glass-bg)", backdropFilter:"blur(var(--blur-surface))", color:"var(--text-secondary)"}}` | `className="border border-glass-border/10 bg-glass-bg/6 backdrop-blur-[24px] text-text-secondary"` |
| Footer border | `style={{borderTop: "1px solid var(--glass-border)"}}` | `className="border-t border-glass-border/10"` |
| Footer text | `style={{color:"var(--text-muted)"}}` | `text-text-muted` |
| Icon opacity | `style={{opacity:0.6}}` | `opacity-60` |
| Flex height | `style={{height:18}}` | `h-[18px]` |
| Price badge gradient | `style={{background:"linear-gradient(135deg, #10b981, #818cf8)"}}` | `className="bg-gradient-to-r from-[#10b981] to-[#818cf8]"` |

### Components converted:

- **StatCard** — 20 lines inline → pure Tailwind with dynamic class
- **FilterChip** — conditional style → template literal class
- **NodeCard** — glass backgrounds, status dots, text, buttons all Tailwind
- **NodeCard MetricRow** — label/bar/value all Tailwind
- **DetailContent** — poster/video opacity, minor fixes (complex backdropFilter kept inline)

## SSH Deploy Key

`~/.ssh/hermes_admin` is the ONLY working auth method for `31.58.51.127:46748` (root).
`sshpass` password `OX8w$nE9A%tfqb6v` from `deploy.sh` is completely dead — server disabled password auth.

Deploy flow:
```bash
cd /home/woioeow/galaxy-glass/nextjs && npm run build && \
cd out && tar czf - . | ssh -i ~/.ssh/hermes_admin -o StrictHostKeyChecking=no -p 46748 root@31.58.51.127 \
  'rm -rf /opt/komari/data/theme && mkdir -p /opt/komari/data/theme && cd /opt/komari/data/theme && tar xzf -' && \
ssh -i ~/.ssh/hermes_admin -o StrictHostKeyChecking=no -p 46748 root@31.58.51.127 \
  'cp /opt/komari/galaxy-proxy.py /opt/komari/data/theme/galaxy-proxy.py && pkill -f galaxy-proxy' && \
sleep 2 && \
ssh -i ~/.ssh/hermes_admin -o StrictHostKeyChecking=no -p 46748 root@31.58.51.127 \
  'cd /opt/komari/data/theme && python3 galaxy-proxy.py'
```

**Key pitfall:** `rm -rf` deletes `galaxy-proxy.py` from theme dir. Must restore from `/opt/komari/galaxy-proxy.py` (backup copy on remote).
