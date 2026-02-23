import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  CircleDollarSign,
  CreditCard,
  Landmark,
  LineChart,
  ShieldCheck,
  UserCog,
} from "lucide-react";

import type { UserRole } from "@/lib/types";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

type RoleAwareNavItem = NavItem & {
  roles: UserRole[];
  inBottomNav?: boolean;
};

const navItems: RoleAwareNavItem[] = [
  { href: "/dashboard", label: "Tổng quan", icon: BarChart3 },
  { href: "/transactions", label: "Giao dịch", icon: CreditCard },
  { href: "/investors", label: "Nhà đầu tư", icon: Landmark },
  { href: "/fees", label: "Phí", icon: CircleDollarSign },
  { href: "/reports", label: "Báo cáo", icon: LineChart },
  { href: "/backup", label: "Sao lưu", icon: ShieldCheck },
  { href: "/accounts", label: "Tài khoản", icon: UserCog },
].map((item) => {
  if (item.href === "/reports") {
    return {
      ...item,
      roles: ["viewer", "admin", "fund_manager", "investor"] as UserRole[],
      inBottomNav: true,
    };
  }
  if (item.href === "/accounts") {
    return { ...item, roles: ["admin"] as UserRole[], inBottomNav: false };
  }
  if (item.href === "/backup") {
    return { ...item, roles: ["viewer", "admin", "fund_manager"] as UserRole[], inBottomNav: false };
  }
  return {
    ...item,
    roles: ["viewer", "admin", "fund_manager"] as UserRole[],
    inBottomNav: true,
  };
});

export function getPrimaryNav(role?: UserRole | null): NavItem[] {
  const effectiveRole = role ?? "viewer";
  return navItems
    .filter((item) => item.inBottomNav && item.roles.includes(effectiveRole))
    .map(({ href, label, icon }) => ({ href, label, icon }));
}

export function getDrawerNav(role?: UserRole | null): NavItem[] {
  const effectiveRole = role ?? "viewer";
  return navItems
    .filter((item) => item.roles.includes(effectiveRole))
    .map(({ href, label, icon }) => ({ href, label, icon }));
}
