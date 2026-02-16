"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Eye, Loader2, Pencil, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { LocationCombobox, type LocationOption } from "@/components/form/location-combobox";
import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { queryKeys } from "@/lib/query-keys";
import type { InvestorCardDTO } from "@/lib/types";
import { formatCurrency, formatDateTime, formatPercent } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

type InvestorViewMode = "card" | "table";

function normalizeType(type: string) {
  return type
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function isValidVietnamPhone(phone: string): boolean {
  return /^0\d{9}$/.test(phone);
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function buildAddress(addressLine: string, wardName: string, provinceName: string): string {
  const parts = [addressLine, wardName, provinceName]
    .map((part) => part.trim())
    .filter(Boolean);
  return parts.join(", ");
}

function buildAddressLabel(profile: {
  address?: string;
  address_line?: string;
  ward_name?: string;
  province_name?: string;
}) {
  const structured = buildAddress(
    profile.address_line || "",
    profile.ward_name || "",
    profile.province_name || "",
  );
  return structured || profile.address || "Chưa cập nhật";
}

function needsAddressNormalization(profile: {
  province_code?: string;
  ward_code?: string;
  address?: string;
}) {
  const hasLegacyAddress = Boolean((profile.address || "").trim());
  const hasStructured = Boolean((profile.province_code || "").trim()) && Boolean((profile.ward_code || "").trim());
  return hasLegacyAddress && !hasStructured;
}

export default function InvestorsPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [joinDate, setJoinDate] = useState(todayIsoDate());
  const [provinceCode, setProvinceCode] = useState("");
  const [provinceName, setProvinceName] = useState("");
  const [wardCode, setWardCode] = useState("");
  const [wardName, setWardName] = useState("");
  const [addressLine, setAddressLine] = useState("");
  const [editingInvestor, setEditingInvestor] = useState<InvestorCardDTO | null>(null);
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editJoinDate, setEditJoinDate] = useState(todayIsoDate());
  const [editProvinceCode, setEditProvinceCode] = useState("");
  const [editProvinceName, setEditProvinceName] = useState("");
  const [editWardCode, setEditWardCode] = useState("");
  const [editWardName, setEditWardName] = useState("");
  const [editAddressLine, setEditAddressLine] = useState("");
  const [viewMode, setViewMode] = useState<InvestorViewMode>("card");
  const [selectedInvestor, setSelectedInvestor] = useState<InvestorCardDTO | null>(null);
  const [detailNavDigits, setDetailNavDigits] = useState("");
  const [detailNavOverflow, setDetailNavOverflow] = useState(false);
  const [detailNavApplied, setDetailNavApplied] = useState<number | undefined>(undefined);

  const flagsQuery = useQuery({
    queryKey: queryKeys.featureFlags(safeToken),
    queryFn: () => apiClient.featureFlags(safeToken),
    enabled: !!token,
  });

  const tableViewEnabled = flagsQuery.data?.table_view ?? true;

  const cardsQuery = useInfiniteQuery({
    queryKey: queryKeys.investorCards(safeToken),
    initialPageParam: 1,
    queryFn: ({ pageParam }) => apiClient.investorCardsPaginated(safeToken, pageParam, 20),
    getNextPageParam: (lastPage, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.items.length, 0);
      if (loaded >= lastPage.total) {
        return undefined;
      }
      return lastPage.page + 1;
    },
    enabled: !!token,
  });

  const investorDetailQuery = useQuery({
    queryKey: queryKeys.investorDetail(safeToken, selectedInvestor?.id, detailNavApplied),
    queryFn: () => apiClient.investorReport(safeToken, selectedInvestor!.id, detailNavApplied),
    enabled: !!token && !!selectedInvestor,
  });

  const provincesQuery = useQuery({
    queryKey: queryKeys.provinces(safeToken),
    queryFn: () => apiClient.listProvinces(safeToken),
    enabled: !!token,
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 48 * 60 * 60 * 1000,
  });

  const createWardsQuery = useQuery({
    queryKey: queryKeys.wards(safeToken, provinceCode),
    queryFn: () => apiClient.listWards(safeToken, provinceCode),
    enabled: !!token && !!provinceCode,
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 48 * 60 * 60 * 1000,
  });

  const editWardsQuery = useQuery({
    queryKey: queryKeys.wards(safeToken, editProvinceCode),
    queryFn: () => apiClient.listWards(safeToken, editProvinceCode),
    enabled: !!token && !!editingInvestor?.id && !!editProvinceCode,
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 48 * 60 * 60 * 1000,
  });

  const investorItems = useMemo(
    () => cardsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [cardsQuery.data],
  );

  const investorTotal = cardsQuery.data?.pages[0]?.total ?? 0;
  const effectiveViewMode: InvestorViewMode = tableViewEnabled ? viewMode : "card";

  const txStats = useMemo(() => {
    const rows = investorDetailQuery.data?.transactions ?? [];
    const deposits = rows.filter((tx) => {
      const normalized = normalizeType(tx.type);
      return normalized.includes("nap") || normalized.includes("deposit");
    });
    const withdrawals = rows.filter((tx) => {
      const normalized = normalizeType(tx.type);
      return normalized.includes("rut") || normalized.includes("withdraw");
    });
    return {
      deposit_count: deposits.length,
      deposit_amount: deposits.reduce((sum, item) => sum + Math.abs(item.amount), 0),
      withdraw_count: withdrawals.length,
      withdraw_amount: withdrawals.reduce((sum, item) => sum + Math.abs(item.amount), 0),
    };
  }, [investorDetailQuery.data]);

  const provinceOptions = useMemo<LocationOption[]>(
    () => (provincesQuery.data ?? []).map((row) => ({ code: row.code, name: row.name })),
    [provincesQuery.data],
  );
  const createWardOptions = useMemo<LocationOption[]>(
    () => (createWardsQuery.data ?? []).map((row) => ({ code: row.code, name: row.name })),
    [createWardsQuery.data],
  );
  const editWardOptions = useMemo<LocationOption[]>(
    () => (editWardsQuery.data ?? []).map((row) => ({ code: row.code, name: row.name })),
    [editWardsQuery.data],
  );

  const createAddressPreview = buildAddress(addressLine, wardName, provinceName);
  const createPhoneInvalid = phone.trim().length > 0 && !isValidVietnamPhone(phone.trim());
  const createAddressPairInvalid = Boolean(provinceCode) !== Boolean(wardCode);

  const editAddressPreview = buildAddress(editAddressLine, editWardName, editProvinceName);
  const editPhoneInvalid = editPhone.trim().length > 0 && !isValidVietnamPhone(editPhone.trim());
  const editAddressPairInvalid = Boolean(editProvinceCode) !== Boolean(editWardCode);

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient.createInvestor(safeToken, {
        name: name.trim(),
        phone: phone.trim(),
        email: email.trim(),
        join_date: joinDate || undefined,
        province_code: provinceCode || undefined,
        province_name: provinceName || undefined,
        ward_code: wardCode || undefined,
        ward_name: wardName || undefined,
        address_line: addressLine.trim() || undefined,
        address: createAddressPreview || addressLine.trim() || undefined,
      }),
    onSuccess: () => {
      setName("");
      setPhone("");
      setEmail("");
      setJoinDate(todayIsoDate());
      setProvinceCode("");
      setProvinceName("");
      setWardCode("");
      setWardName("");
      setAddressLine("");
      pushToast({ title: "Đã tạo nhà đầu tư", variant: "success" });
      queryClient.invalidateQueries({ queryKey: queryKeys.investorCards(safeToken), exact: true });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(safeToken), exact: true });
    },
    onError: (error) => {
      pushToast({
        title: "Không thể tạo nhà đầu tư",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editingInvestor) {
        throw new Error("Không có nhà đầu tư cần cập nhật.");
      }
      return apiClient.updateInvestor(safeToken, editingInvestor.id, {
        name: editName.trim(),
        phone: editPhone.trim(),
        email: editEmail.trim(),
        join_date: editJoinDate || undefined,
        province_code: editProvinceCode || undefined,
        province_name: editProvinceName || undefined,
        ward_code: editWardCode || undefined,
        ward_name: editWardName || undefined,
        address_line: editAddressLine.trim() || undefined,
        address: editAddressPreview || editAddressLine.trim() || undefined,
      });
    },
    onSuccess: () => {
      const editedId = editingInvestor?.id;
      setEditingInvestor(null);
      pushToast({ title: "Đã cập nhật thông tin nhà đầu tư", variant: "success" });
      queryClient.invalidateQueries({ queryKey: queryKeys.investorCards(safeToken), exact: true });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(safeToken), exact: true });
      if (selectedInvestor?.id && editedId && selectedInvestor.id === editedId) {
        setSelectedInvestor((current) =>
          current
            ? {
                ...current,
                display_name: `${editName.trim()} (ID: ${editedId})`,
                phone: editPhone.trim(),
                email: editEmail.trim(),
                join_date: editJoinDate,
                province_code: editProvinceCode,
                province_name: editProvinceName,
                ward_code: editWardCode,
                ward_name: editWardName,
                address_line: editAddressLine.trim(),
                address: editAddressPreview || editAddressLine.trim(),
              }
            : current,
        );
        queryClient.invalidateQueries({
          queryKey: queryKeys.investorDetail(safeToken, editedId),
          exact: false,
        });
      }
    },
    onError: (error) => {
      pushToast({
        title: "Không thể cập nhật nhà đầu tư",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  function openInvestorDetail(item: InvestorCardDTO) {
    setSelectedInvestor(item);
    setDetailNavDigits("");
    setDetailNavOverflow(false);
    setDetailNavApplied(undefined);
  }

  function openEditInvestor(item: InvestorCardDTO) {
    setEditingInvestor(item);
    setEditName(item.display_name.split(" (ID")[0]);
    setEditPhone(item.phone || "");
    setEditEmail(item.email || "");
    setEditJoinDate((item.join_date || todayIsoDate()).slice(0, 10));
    setEditProvinceCode(item.province_code || "");
    setEditProvinceName(item.province_name || "");
    setEditWardCode(item.ward_code || "");
    setEditWardName(item.ward_name || "");
    setEditAddressLine(item.address_line || "");
  }

  const detailNavNumber = digitsToNumber(detailNavDigits);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Thêm nhà đầu tư</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Tên" value={name} onChange={(e) => setName(e.target.value)} />
          <Input
            placeholder="Số điện thoại"
            value={phone}
            onChange={(e) => setPhone(e.target.value.trim())}
            inputMode="numeric"
            pattern="0[0-9]{9}"
            maxLength={10}
            aria-invalid={createPhoneInvalid}
          />
          <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input type="date" value={joinDate} onChange={(e) => setJoinDate(e.target.value)} />
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <LocationCombobox
            options={provinceOptions}
            value={provinceCode}
            onChange={(option) => {
              setProvinceCode(option?.code || "");
              setProvinceName(option?.name || "");
              setWardCode("");
              setWardName("");
            }}
            placeholder="Chọn Tỉnh/Thành"
            disabled={provincesQuery.isLoading}
            invalid={createAddressPairInvalid}
          />
          <LocationCombobox
            options={createWardOptions}
            value={wardCode}
            onChange={(option) => {
              setWardCode(option?.code || "");
              setWardName(option?.name || "");
            }}
            placeholder="Chọn Phường/Xã"
            disabled={!provinceCode || createWardsQuery.isLoading}
            invalid={createAddressPairInvalid}
          />
        </div>
        <Input
          placeholder="Địa chỉ chi tiết (số nhà, đường...)"
          value={addressLine}
          onChange={(e) => setAddressLine(e.target.value)}
        />
        <p className="input-helper">Địa chỉ đầy đủ: {createAddressPreview || "Chưa có"}</p>
        {createPhoneInvalid ? <p className="inline-error">Số điện thoại phải có định dạng 0xxxxxxxxx.</p> : null}
        {createAddressPairInvalid ? (
          <p className="inline-error">Tỉnh/Thành và Phường/Xã cần chọn đồng thời.</p>
        ) : null}
        <Button
          className="w-full"
          onClick={() => createMutation.mutate()}
          disabled={!name.trim() || createPhoneInvalid || createAddressPairInvalid || createMutation.isPending}
        >
          {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Tạo nhà đầu tư
        </Button>
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title">Danh sách nhà đầu tư</h2>
          {tableViewEnabled ? (
            <div className="flex rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-1">
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${
                  viewMode === "card"
                    ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                    : "text-[var(--color-muted)]"
                }`}
                onClick={() => setViewMode("card")}
                type="button"
              >
                Thẻ
              </button>
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${
                  viewMode === "table"
                    ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]"
                    : "text-[var(--color-muted)]"
                }`}
                onClick={() => setViewMode("table")}
                type="button"
              >
                Bảng
              </button>
            </div>
          ) : (
            <p className="text-xs text-[var(--color-muted)]">Chế độ dạng thẻ</p>
          )}
        </div>

        {cardsQuery.isLoading ? (
          <LoadingState label="Đang tải danh sách nhà đầu tư..." />
        ) : cardsQuery.isError ? (
          <ErrorState message="Không tải được danh sách nhà đầu tư." />
        ) : investorItems.length ? (
          tableViewEnabled && effectiveViewMode === "table" ? (
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="min-w-[780px] text-sm">
                <thead className="sticky top-0 z-20 bg-[var(--color-surface-3)]">
                  <tr>
                    <th className="sticky left-0 z-30 bg-[var(--color-surface-3)] px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Tên</th>
                    <th className="px-3 py-2 text-left">SĐT</th>
                    <th className="px-3 py-2 text-left">Email</th>
                    <th className="px-3 py-2 text-left">Địa chỉ</th>
                    <th className="px-3 py-2 text-left">Giá trị</th>
                    <th className="px-3 py-2 text-left">Lãi/Lỗ</th>
                    <th className="px-3 py-2 text-left">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {investorItems.map((item) => (
                    <tr key={item.id} className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
                      <td className="sticky left-0 z-10 bg-[var(--color-surface)] px-3 py-2">#{item.id}</td>
                      <td className="px-3 py-2">{item.display_name}</td>
                      <td className="px-3 py-2">{item.phone || "-"}</td>
                      <td className="px-3 py-2">{item.email || "-"}</td>
                      <td className="px-3 py-2">{buildAddressLabel(item)}</td>
                      <td className="px-3 py-2">{formatCurrency(item.current_value)}</td>
                      <td className="px-3 py-2">
                        {formatCurrency(item.pnl)} ({formatPercent(item.pnl_percent)})
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-2">
                          <Button variant="secondary" className="h-9 px-3 py-1 text-xs" onClick={() => openInvestorDetail(item)}>
                            <Eye className="mr-1 h-4 w-4" />
                            Chi tiết
                          </Button>
                          <Button variant="secondary" className="h-9 px-3 py-1 text-xs" onClick={() => openEditInvestor(item)}>
                            <Pencil className="mr-1 h-4 w-4" />
                            Sửa
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null
        ) : null}

        {investorItems.length ? (
          <div className={`list-stagger space-y-2 ${effectiveViewMode === "table" ? "hidden" : ""}`}>
            {investorItems.map((item) => (
              <article
                key={item.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <p className="text-sm font-semibold">{item.display_name}</p>
                    <p className="text-xs text-[var(--color-muted)]">{item.phone || "Chưa có số điện thoại"}</p>
                    <p className="text-xs text-[var(--color-muted)]">{item.email || "Chưa có email"}</p>
                    <p className="text-xs text-[var(--color-muted)]">{buildAddressLabel(item)}</p>
                    {needsAddressNormalization(item) ? (
                      <span className="inline-flex rounded-full border border-[var(--color-warning-border)] bg-[var(--color-warning-bg)] px-2 py-1 text-[11px] text-[var(--color-warning-text)]">
                        Địa chỉ cần chuẩn hóa
                      </span>
                    ) : null}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="secondary" className="h-9 w-9 p-0" onClick={() => openInvestorDetail(item)} aria-label="Xem chi tiết">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="secondary"
                      className="h-9 w-9 p-0"
                      onClick={() => openEditInvestor(item)}
                      aria-label="Sửa nhà đầu tư"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-[var(--color-surface)] px-2 py-2">
                    <p className="text-[var(--color-muted)]">Giá trị hiện tại</p>
                    <p className="font-semibold">{formatCurrency(item.current_value)}</p>
                  </div>
                  <div className="rounded-lg bg-[var(--color-surface)] px-2 py-2">
                    <p className="text-[var(--color-muted)]">Lãi / Lỗ</p>
                    <p className="font-semibold">
                      {formatCurrency(item.pnl)} ({formatPercent(item.pnl_percent)})
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Chưa có nhà đầu tư."
            description="Tạo nhà đầu tư đầu tiên để bắt đầu luồng giao dịch."
          />
        )}

        {cardsQuery.hasNextPage ? (
          <div className="space-y-2">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => cardsQuery.fetchNextPage()}
              disabled={cardsQuery.isFetchingNextPage}
            >
              {cardsQuery.isFetchingNextPage ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Tải thêm nhà đầu tư
            </Button>
            <p className="text-center text-xs text-[var(--color-muted)]">
              Đang hiển thị {investorItems.length}/{investorTotal} nhà đầu tư
            </p>
          </div>
        ) : null}
      </Card>

      <Dialog.Root
        open={!!selectedInvestor}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedInvestor(null);
            setDetailNavDigits("");
            setDetailNavOverflow(false);
            setDetailNavApplied(undefined);
          }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-[overlay-in_180ms_ease-out]" />
          <Dialog.Content className="fixed inset-0 z-50 overflow-y-auto border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:h-auto md:max-h-[88vh] md:w-[820px] md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-2xl md:p-5">
            <div className="sticky top-0 z-10 mb-3 flex items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] pb-3">
              <Dialog.Title className="section-title">
                Chi tiết nhà đầu tư
                {selectedInvestor ? ` - #${selectedInvestor.id}` : ""}
              </Dialog.Title>
              <Dialog.Close asChild>
                <Button variant="secondary" className="h-9 w-9 p-0" aria-label="Đóng chi tiết nhà đầu tư">
                  <X className="h-4 w-4" />
                </Button>
              </Dialog.Close>
            </div>

            <div className="mb-3 grid gap-2 md:grid-cols-[1fr_auto]">
              <div>
                <MoneyInput
                  value={detailNavDigits}
                  onValueChange={(value) => {
                    setDetailNavDigits(value.rawDigits);
                    setDetailNavOverflow(value.isOverflow);
                  }}
                  placeholder="2,500,000,000"
                  aria-invalid={detailNavOverflow}
                />
                <p className="input-helper">
                  NAV tùy chọn: {detailNavNumber ? formatCurrency(detailNavNumber) : "Theo NAV hiện tại"}
                </p>
                {detailNavOverflow ? <p className="inline-error">NAV quá lớn (tối đa 15 chữ số).</p> : null}
              </div>
              <Button
                variant="secondary"
                onClick={() => {
                  if (detailNavOverflow) return;
                  setDetailNavApplied(detailNavNumber && detailNavNumber > 0 ? detailNavNumber : undefined);
                }}
                disabled={detailNavOverflow}
              >
                Áp dụng NAV
              </Button>
            </div>

            {investorDetailQuery.isLoading ? (
              <LoadingState label="Đang tải báo cáo chi tiết nhà đầu tư..." />
            ) : investorDetailQuery.isError ? (
              <ErrorState message="Không tải được chi tiết nhà đầu tư." />
            ) : investorDetailQuery.data ? (
              <div className="space-y-3">
                <Card className="space-y-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-base font-semibold">{investorDetailQuery.data.investor.name}</p>
                      <p className="text-xs text-[var(--color-muted)]">
                        Ngày tham gia: {investorDetailQuery.data.investor.join_date}
                      </p>
                    </div>
                    <div className="text-xs text-[var(--color-muted)]">
                      <p>NAV áp dụng: {formatCurrency(investorDetailQuery.data.current_nav)}</p>
                      <p>Giá/đơn vị: {formatCurrency(investorDetailQuery.data.current_price)}</p>
                    </div>
                  </div>
                  <div className="grid gap-2 text-xs sm:grid-cols-3">
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Điện thoại: {investorDetailQuery.data.investor.phone || "Chưa cập nhật"}
                    </p>
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Email: {investorDetailQuery.data.investor.email || "Chưa cập nhật"}
                    </p>
                    <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                      Địa chỉ: {buildAddressLabel(investorDetailQuery.data.investor)}
                    </p>
                  </div>
                  {needsAddressNormalization(investorDetailQuery.data.investor) ? (
                    <span className="inline-flex rounded-full border border-[var(--color-warning-border)] bg-[var(--color-warning-bg)] px-2 py-1 text-[11px] text-[var(--color-warning-text)]">
                      Địa chỉ cần chuẩn hóa lên Tỉnh/Phường
                    </span>
                  ) : null}
                </Card>

                <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                  <Card>
                    <p className="kpi-label">Giá trị hiện tại</p>
                    <p className="kpi-value">{formatCurrency(investorDetailQuery.data.current_balance)}</p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Lãi/Lỗ hiện tại</p>
                    <p className="kpi-value">{formatCurrency(investorDetailQuery.data.current_profit)}</p>
                    <p className="text-xs text-[var(--color-muted)]">
                      {formatPercent(investorDetailQuery.data.current_profit_perc)}
                    </p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Vốn gốc</p>
                    <p className="kpi-value">
                      {formatCurrency(investorDetailQuery.data.lifetime_performance.original_invested)}
                    </p>
                  </Card>
                  <Card>
                    <p className="kpi-label">Tổng phí đã thu</p>
                    <p className="kpi-value">
                      {formatCurrency(investorDetailQuery.data.lifetime_performance.total_fees_paid)}
                    </p>
                  </Card>
                </div>

                <div className="grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <Card className="space-y-2">
                    <h3 className="section-title">Hiệu suất tích lũy</h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Lợi nhuận gộp:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.lifetime_performance.gross_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Lợi nhuận ròng:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.lifetime_performance.net_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tỷ suất gộp:{" "}
                        <span className="font-semibold">
                          {formatPercent(investorDetailQuery.data.lifetime_performance.gross_return)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tỷ suất ròng:{" "}
                        <span className="font-semibold">
                          {formatPercent(investorDetailQuery.data.lifetime_performance.net_return)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng đơn vị hiện tại:{" "}
                        <span className="font-semibold">
                          {investorDetailQuery.data.lifetime_performance.current_units.toFixed(6)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Báo cáo lúc:{" "}
                        <span className="font-semibold">{formatDateTime(investorDetailQuery.data.report_date)}</span>
                      </p>
                    </div>
                  </Card>

                  <Card className="space-y-2">
                    <h3 className="section-title">Nạp/Rút và chỉ số phí</h3>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng nạp ({txStats.deposit_count} GD):{" "}
                        <span className="font-semibold">{formatCurrency(txStats.deposit_amount)}</span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng rút ({txStats.withdraw_count} GD):{" "}
                        <span className="font-semibold">{formatCurrency(txStats.withdraw_amount)}</span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Hurdle value:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.hurdle_value)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        HWM value:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.hwm_value)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Excess profit:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.excess_profit)}
                        </span>
                      </p>
                      <p className="rounded-lg bg-[var(--color-surface-2)] px-2 py-2">
                        Tổng phí:{" "}
                        <span className="font-semibold">
                          {formatCurrency(investorDetailQuery.data.fee_details.total_fee)}
                        </span>
                      </p>
                    </div>
                  </Card>
                </div>

                <Card className="space-y-2">
                  <h3 className="section-title">Lịch sử giao dịch ({investorDetailQuery.data.transactions.length})</h3>
                  {investorDetailQuery.data.transactions.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.transactions.slice(0, 12).map((tx) => (
                        <article
                          key={tx.id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-sm font-semibold">{tx.type}</p>
                            <p className="text-xs text-[var(--color-muted)]">#{tx.id}</p>
                          </div>
                          <p className="text-xs text-[var(--color-muted)]">{formatDateTime(tx.date)}</p>
                          <p className="text-sm">
                            Số tiền: {formatCurrency(tx.amount)} | NAV: {formatCurrency(tx.nav)} | Units:{" "}
                            {tx.units_change.toFixed(6)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Nhà đầu tư chưa có lịch sử nạp/rút." />
                  )}
                </Card>

                <Card className="space-y-2">
                  <h3 className="section-title">Danh mục tranche ({investorDetailQuery.data.tranches.length})</h3>
                  {investorDetailQuery.data.tranches.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.tranches.map((tranche) => (
                        <article
                          key={tranche.tranche_id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2 text-sm"
                        >
                          <p className="font-semibold">Tranche {tranche.tranche_id}</p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Ngày vào: {formatDateTime(tranche.entry_date)} | NAV vào: {formatCurrency(tranche.entry_nav)}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Units: {tranche.units.toFixed(6)} | HWM: {formatCurrency(tranche.hwm)} | Vốn ban đầu:{" "}
                            {formatCurrency(tranche.original_invested_value)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Không có tranche để hiển thị." />
                  )}
                </Card>

                <Card className="space-y-2">
                  <h3 className="section-title">Lịch sử phí ({investorDetailQuery.data.fee_history.length})</h3>
                  {investorDetailQuery.data.fee_history.length ? (
                    <div className="list-stagger space-y-2">
                      {investorDetailQuery.data.fee_history.slice(0, 8).map((fee) => (
                        <article
                          key={fee.id}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2"
                        >
                          <p className="text-sm font-semibold">
                            {fee.period} - {formatCurrency(fee.fee_amount)}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">
                            Ngày tính: {fee.calculation_date} | Units phí: {fee.fee_units.toFixed(6)}
                          </p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <EmptyState title="Nhà đầu tư chưa có lịch sử phí." />
                  )}
                </Card>
              </div>
            ) : (
              <EmptyState title="Chọn nhà đầu tư để xem chi tiết." />
            )}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <Dialog.Root
        open={!!editingInvestor}
        onOpenChange={(open) => {
          if (!open) {
            setEditingInvestor(null);
          }
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-[overlay-in_180ms_ease-out]" />
          <Dialog.Content className="fixed inset-0 z-50 overflow-y-auto border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:h-auto md:max-h-[86vh] md:w-[640px] md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-2xl md:p-5">
            <div className="sticky top-0 z-10 mb-3 flex items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface)] pb-3">
              <Dialog.Title className="section-title">
                Chỉnh sửa nhà đầu tư {editingInvestor ? `#${editingInvestor.id}` : ""}
              </Dialog.Title>
              <Dialog.Close asChild>
                <Button variant="secondary" className="h-9 w-9 p-0" aria-label="Đóng chỉnh sửa nhà đầu tư">
                  <X className="h-4 w-4" />
                </Button>
              </Dialog.Close>
            </div>

            <div className="space-y-3">
              <div className="grid gap-2 sm:grid-cols-2">
                <Input placeholder="Tên" value={editName} onChange={(e) => setEditName(e.target.value)} />
                <Input
                  placeholder="Số điện thoại"
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value.trim())}
                  inputMode="numeric"
                  pattern="0[0-9]{9}"
                  maxLength={10}
                  aria-invalid={editPhoneInvalid}
                />
                <Input placeholder="Email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} />
                <Input type="date" value={editJoinDate} onChange={(e) => setEditJoinDate(e.target.value)} />
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                <LocationCombobox
                  options={provinceOptions}
                  value={editProvinceCode}
                  onChange={(option) => {
                    setEditProvinceCode(option?.code || "");
                    setEditProvinceName(option?.name || "");
                    setEditWardCode("");
                    setEditWardName("");
                  }}
                  placeholder="Chọn Tỉnh/Thành"
                  disabled={provincesQuery.isLoading}
                  invalid={editAddressPairInvalid}
                />
                <LocationCombobox
                  options={editWardOptions}
                  value={editWardCode}
                  onChange={(option) => {
                    setEditWardCode(option?.code || "");
                    setEditWardName(option?.name || "");
                  }}
                  placeholder="Chọn Phường/Xã"
                  disabled={!editProvinceCode || editWardsQuery.isLoading}
                  invalid={editAddressPairInvalid}
                />
              </div>

              <Input
                placeholder="Địa chỉ chi tiết (số nhà, đường...)"
                value={editAddressLine}
                onChange={(e) => setEditAddressLine(e.target.value)}
              />

              <p className="input-helper">Địa chỉ đầy đủ: {editAddressPreview || "Chưa có"}</p>
              {editPhoneInvalid ? <p className="inline-error">Số điện thoại phải có định dạng 0xxxxxxxxx.</p> : null}
              {editAddressPairInvalid ? (
                <p className="inline-error">Tỉnh/Thành và Phường/Xã cần chọn đồng thời.</p>
              ) : null}

              <Button
                className="w-full"
                onClick={() => updateMutation.mutate()}
                disabled={!editName.trim() || editPhoneInvalid || editAddressPairInvalid || updateMutation.isPending}
              >
                {updateMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Lưu thay đổi
              </Button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
