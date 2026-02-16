import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  CircleDollarSign,
  CreditCard,
  Landmark,
  LineChart,
  ShieldCheck,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

export const primaryNav: NavItem[] = [
  { href: "/dashboard", label: "Tổng quan", icon: BarChart3 },
  { href: "/transactions", label: "Giao dịch", icon: CreditCard },
  { href: "/investors", label: "Nhà đầu tư", icon: Landmark },
  { href: "/fees", label: "Phí", icon: CircleDollarSign },
];

export const drawerNav: NavItem[] = [
  ...primaryNav,
  { href: "/reports", label: "Báo cáo", icon: LineChart },
  { href: "/backup", label: "Sao lưu", icon: ShieldCheck },
];
