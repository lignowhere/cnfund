export const THEME_STORAGE_KEY = "cnfund-theme";

export function getThemeBootScript() {
  return `
  (() => {
    try {
      const raw = localStorage.getItem("${THEME_STORAGE_KEY}");
      let preference = "system";
      if (raw) {
        const parsed = JSON.parse(raw);
        const fromStore = parsed?.state?.preference;
        if (fromStore === "light" || fromStore === "dark" || fromStore === "system") {
          preference = fromStore;
        }
      }
      const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const resolved = preference === "system" ? (isDark ? "dark" : "light") : preference;
      document.documentElement.dataset.theme = resolved;
      document.documentElement.style.colorScheme = resolved;
    } catch {
      document.documentElement.dataset.theme = "light";
      document.documentElement.style.colorScheme = "light";
    }
  })();
`;
}
