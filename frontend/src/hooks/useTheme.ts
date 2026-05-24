import { useEffect, useState } from "react";

export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">(() => {
    return (localStorage.getItem("dashboard-theme") as "light" | "dark" | "system") ?? "system";
  });
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    localStorage.setItem("dashboard-theme", theme);
    if (theme === "light") {
      root.setAttribute("data-theme", "light");
      root.classList.remove("dark");
      setIsDark(false);
    } else if (theme === "dark") {
      root.setAttribute("data-theme", "dark");
      root.classList.add("dark");
      setIsDark(true);
    } else {
      root.removeAttribute("data-theme");
      root.classList.remove("dark");
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      setIsDark(mq.matches);
      const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme]);

  const toggle = () => setTheme(isDark ? "light" : "dark");

  return { isDark, toggle };
}
