# Design Guidelines

_Last updated: 2026-03-13_

---

## 1. Tech Stack UI

- **Component library:** shadcn/ui (Radix UI primitives) — lightly customized
- **Styling:** Tailwind CSS v4 với CSS custom properties (design tokens)
- **Charts:** Recharts
- **Icons:** Lucide React
- **Fonts:** Manrope (headings) + Noto Sans (body) — cả hai hỗ trợ Vietnamese subset

---

## 2. Color System

Dùng CSS custom properties (variables), không hardcode màu trong Tailwind classes. Hỗ trợ light + dark mode.

### Light Mode (`:root`)

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#0a5c8f` | Buttons, links, active nav |
| `--color-primary-700` | `#084a73` | Hover states |
| `--color-primary-50` | `#e6f4fb` | Light backgrounds |
| `--color-accent` | `#1e88e5` | Secondary interactive |
| `--color-success` | `#157347` | Positive values, confirm |
| `--color-danger` | `#b42318` | Errors, destructive actions |
| `--color-warning` | `#b54708` | Warnings |
| `--color-text` | `#0f172a` | Primary text |
| `--color-muted` | `#4b5563` | Secondary text |
| `--color-border` | `#d7e6f0` | Borders |
| `--color-surface` | `#fefefe` | Card backgrounds |
| `--color-surface-2` | `#f3f8fc` | Page background |
| `--color-surface-3` | `#e8f1f8` | Deeper surface |

### Dark Mode (`[data-theme="dark"]`)

| Token | Value |
|-------|-------|
| `--color-primary` | `#5ea8df` |
| `--color-text` | `#e8edf4` |
| `--color-surface` | `#111b25` |
| `--color-surface-2` | `#0d151f` |
| `--color-border` | `#2f4154` |

Dark mode applied via `data-theme="dark"` attribute on `<html>`. Flash of unstyled content (FOUC) prevented bằng inline script trong `<head>` (`lib/theme.ts → getThemeBootScript()`).

### Chart Colors

6 shades của blue palette: `--chart-1` (#0f4c81) đến `--chart-6` (#b8daef). Consistent với brand color.

### Status Colors

Mỗi status (danger, success, warning) có 3 tokens: `-bg`, `-border`, `-text` cho full context styling.

```css
/* Example: danger state */
background: var(--color-danger-bg);     /* #fff1f2 */
border: 1px solid var(--color-danger-border);  /* #fecdd3 */
color: var(--color-danger-text);        /* #9f1239 */
```

---

## 3. Typography

| Context | Font | Weights |
|---------|------|---------|
| Headings | Manrope (CSS var `--font-heading`) | 500, 600, 700 |
| Body | Noto Sans (CSS var `--font-body`) | 400, 500, 600 |

CSS vars được set qua Next.js `next/font/google` → class variables `--font-heading`, `--font-body`.

**Vietnamese:** Cả hai font load subset `latin` + `vietnamese`. Dùng `lang="vi"` trên `<html>`.

---

## 4. Spacing & Borders

Design tokens (dùng cho cards và controls):

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-card` | `20px` | Card border radius |
| `--radius-control` | `14px` | Buttons, inputs border radius |
| `--shadow-card` | box shadow | Card default shadow |
| `--shadow-card-hover` | box shadow | Card hover shadow |
| `--space-*` | 0.5rem – 2rem | Consistent spacing scale |

---

## 5. Component Patterns

### Button Variants
`frontend_app/src/components/ui/button.tsx` — variants:
- `primary` — filled, `--color-primary`
- `secondary` — outlined
- `ghost` — transparent, hover background
- `danger` — red destructive action

Sizes: `sm`, `md` (default), `lg`.

### Cards
`components/ui/card.tsx` — uses `--radius-card`, `--shadow-card`. Pattern: `CardHeader` + `CardContent` từ shadcn/ui.

### Loading / Empty / Error States
`components/ui/states.tsx` — centralizes: `LoadingState`, `EmptyState`, `ErrorState` components. Dùng nhất quán trên tất cả pages thay vì inline conditionals.

### Confirm Dialogs
`components/ui/confirm-dialog.tsx` — wraps Radix Dialog. Dùng cho destructive actions (delete, restore, apply fees).

### Toast Notifications
`components/ui/toast-viewport.tsx` — toast notifications cho success/error feedback. Hiển thị ở bottom-right.

### Form Inputs
`components/ui/input.tsx` — base input wrapper. Vietnamese currency input dùng `NumberInput` helper (formats as `1.000.000` VND, không dùng native number input).

---

## 6. Responsive Strategy

- **Mobile-first:** Default styles cho mobile, breakpoints cho larger screens
- **Breakpoints:** Tailwind defaults (`sm`: 640px, `md`: 768px, `lg`: 1024px, `xl`: 1280px)
- **Sidebar:** Collapsible trên mobile, persistent trên desktop
- **Tables:** Horizontal scroll trên mobile
- **PWA:** `manifest.webmanifest`, service worker, installable trên Android/iOS

---

## 7. Vietnamese Locale Handling

- HTML `lang="vi"` (set trong `layout.tsx`)
- Vietnamese currency: format `1.234.567 VND` (dấu chấm cho thousands)
- `NumberInput` component xử lý input formatting cho VND amounts
- Dates: hiển thị `DD/MM/YYYY` pattern trong UI (Vietnamese convention)
- Error messages: nhiều messages tiếng Việt trong `api.ts` (e.g. "Phiên đăng nhập đã hết hạn")
- Form labels: tiếng Việt
- Fonts: Noto Sans với Vietnamese subset support

---

## 8. Hero / Login Page

Login page có hero gradient background:
```css
--hero-start: #0f4c81
--hero-mid: #145a94
--hero-end: #1b6ca8
```

Với decorative orbs (`--hero-orb-a`, `--hero-orb-b`) và muted text color (`--hero-text-muted`).

---

## 9. Dark Mode Implementation

1. Default: light mode
2. User preference: `localStorage` key `theme` → `"dark"` | `"light"` | `"system"`
3. `getThemeBootScript()` inject inline script vào `<head>` để set `data-theme` trước khi render — prevents FOUC
4. Toggle: không có UI toggle visible trong current build (implementation có trong `lib/theme.ts` nhưng trigger UI chưa được thêm vào sidebar)

---

## 10. PWA Configuration

- `app/manifest.ts` — generates `/manifest.webmanifest`
- Icons: `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` ở `public/icons/`
- Service worker: `public/sw.js` — registered bởi `components/pwa/sw-register.tsx`
- Theme color: `#0a5c8f` (light) / `#11385a` (dark)
- App name: "CNFund Web"
- Display: `standalone` (installable, no browser chrome)
