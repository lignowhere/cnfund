"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Loader2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { InvestorCombobox } from "@/components/form/investor-combobox";
import { MoneyInput } from "@/components/form/money-input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import { digitsToNumber } from "@/lib/number-input";
import { queryKeys } from "@/lib/query-keys";
import type { InvestorSelectOption, TransactionCardDTO } from "@/lib/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import { useToastStore } from "@/store/toast-store";

type TxType = "deposit" | "withdraw" | "nav_update";
type TxViewMode = "card" | "table";

function toInvestorOption(displayName: string, id: number): InvestorSelectOption {
  const plainName = displayName.replace(/\s*\(ID:\s*\d+\)\s*$/i, "").trim();
  const label = `${plainName || displayName} · ID ${id}`;
  return {
    id,
    displayName: label,
    searchText: `${displayName} ${plainName} ${id}`,
  };
}

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const safeToken = token || "";
  const pushToast = useToastStore((state) => state.push);

  const [txType, setTxType] = useState<TxType>("deposit");
  const [selectedInvestor, setSelectedInvestor] = useState<InvestorSelectOption | null>(null);
  const [amountDigits, setAmountDigits] = useState("");
  const [amountOverflow, setAmountOverflow] = useState(false);
  const [totalNavDigits, setTotalNavDigits] = useState("");
  const [totalNavOverflow, setTotalNavOverflow] = useState(false);
  const [txDate, setTxDate] = useState(new Date().toISOString().slice(0, 10));
  const [selectedTx, setSelectedTx] = useState<TransactionCardDTO | null>(null);
  const [viewMode, setViewMode] = useState<TxViewMode>("card");
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);

  const flagsQuery = useQuery({
    queryKey: queryKeys.featureFlags(safeToken),
    queryFn: () => apiClient.featureFlags(safeToken),
    enabled: !!token,
  });

  const investorsQuery = useQuery({
    queryKey: queryKeys.investorOptions(safeToken),
    queryFn: async () => {
      const investors = await apiClient.investorCards(safeToken);
      return investors.map((item) => toInvestorOption(item.display_name, item.id));
    },
    enabled: !!token,
  });

  const tableViewEnabled = flagsQuery.data?.table_view ?? true;
  const loadMoreEnabled = flagsQuery.data?.transactions_load_more ?? true;

  const transactionsQuery = useInfiniteQuery({
    queryKey: queryKeys.transactionCards(safeToken),
    initialPageParam: 1,
    queryFn: ({ pageParam }) => apiClient.transactionCards(safeToken, pageParam, 20),
    getNextPageParam: (lastPage, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.items.length, 0);
      if (loaded >= lastPage.total) {
        return undefined;
      }
      return lastPage.page + 1;
    },
    enabled: !!token,
  });

  const txItems = useMemo(
    () => transactionsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [transactionsQuery.data],
  );
  const txTotal = transactionsQuery.data?.pages[0]?.total ?? 0;
  const effectiveViewMode: TxViewMode = tableViewEnabled ? viewMode : "card";

  const amountValue = digitsToNumber(amountDigits);
  const totalNavValue = digitsToNumber(totalNavDigits);
  const investorRequired = txType !== "nav_update";
  const investorInvalid = investorRequired && !selectedInvestor;
  const amountInvalid = txType !== "nav_update" && (!amountValue || amountValue <= 0 || amountOverflow);
  const totalNavInvalid = !totalNavValue || totalNavValue <= 0 || totalNavOverflow;

  async function invalidateAfterMutation() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.transactionCards(safeToken), exact: true }),
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard(safeToken), exact: true }),
      queryClient.invalidateQueries({ queryKey: queryKeys.navHistory(safeToken), exact: true }),
      queryClient.invalidateQueries({
        queryKey: queryKeys.dashboardTransactionsSummary(safeToken),
        exact: true,
      }),
      queryClient.invalidateQueries({ queryKey: queryKeys.investorCards(safeToken), exact: true }),
      queryClient.invalidateQueries({ queryKey: ["transactions-report", safeToken], exact: false }),
      queryClient.invalidateQueries({ queryKey: ["investor-report", safeToken], exact: false }),
      queryClient.invalidateQueries({ queryKey: ["investor-detail", safeToken], exact: false }),
    ]);
  }

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient.createTransaction(safeToken, {
        transaction_type: txType,
        investor_id: txType === "nav_update" ? undefined : selectedInvestor?.id,
        amount: txType === "nav_update" ? undefined : amountValue || undefined,
        total_nav: totalNavValue || 0,
        transaction_date: txDate,
      }),
    onSuccess: async () => {
      setAmountDigits("");
      setAmountOverflow(false);
      setTotalNavDigits("");
      setTotalNavOverflow(false);
      pushToast({ title: "Đã cập nhật giao dịch", variant: "success" });
      await invalidateAfterMutation();
    },
    onError: (error) => {
      pushToast({
        title: "Không thể tạo giao dịch",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteTransaction(safeToken, id),
    onSuccess: async () => {
      setDeleteTarget(null);
      pushToast({ title: "Đã xóa giao dịch", variant: "success" });
      await invalidateAfterMutation();
    },
    onError: (error) => {
      pushToast({
        title: "Không thể xóa giao dịch",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const undoMutation = useMutation({
    mutationFn: (id: number) => apiClient.undoTransaction(safeToken, id),
    onSuccess: async () => {
      pushToast({ title: "Đã hoàn tác giao dịch", variant: "success" });
      await invalidateAfterMutation();
    },
    onError: (error) => {
      pushToast({
        title: "Không thể hoàn tác",
        description: error instanceof Error ? error.message : undefined,
        variant: "error",
      });
    },
  });

  const errorText = useMemo(() => {
    if (createMutation.error instanceof Error) return createMutation.error.message;
    return null;
  }, [createMutation.error]);

  const canSubmit =
    !!token &&
    !!txDate &&
    !totalNavInvalid &&
    (txType === "nav_update" || (!investorInvalid && !amountInvalid)) &&
    !createMutation.isPending;

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Thêm giao dịch / cập nhật NAV</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          <select
            className="control-select"
            value={txType}
            onChange={(e) => {
              const nextType = e.target.value as TxType;
              setTxType(nextType);
              if (nextType === "nav_update") {
                setSelectedInvestor(null);
                setAmountDigits("");
                setAmountOverflow(false);
              }
            }}
          >
            <option value="deposit">Nạp tiền</option>
            <option value="withdraw">Rút tiền</option>
            <option value="nav_update">Cập nhật NAV</option>
          </select>
          <Input
            type="date"
            value={txDate}
            onChange={(e) => setTxDate(e.target.value)}
            className="sm:col-span-2"
          />
        </div>

        {txType !== "nav_update" ? (
          <div className="space-y-2">
            <InvestorCombobox
              options={investorsQuery.data ?? []}
              value={selectedInvestor?.id ?? null}
              onChange={setSelectedInvestor}
              placeholder="Tìm theo tên hoặc ID nhà đầu tư"
              disabled={investorsQuery.isLoading}
              invalid={investorInvalid}
            />
            {investorInvalid ? <p className="inline-error">Vui lòng chọn đúng nhà đầu tư.</p> : null}
          </div>
        ) : null}

        {txType !== "nav_update" ? (
          <div className="space-y-1">
            <MoneyInput
              value={amountDigits}
              onValueChange={(value) => {
                setAmountDigits(value.rawDigits);
                setAmountOverflow(value.isOverflow);
              }}
              placeholder="50,000,000"
              aria-invalid={amountInvalid}
            />
            <p className="input-helper">Giá trị sẽ gửi: {amountValue ? formatCurrency(amountValue) : "Chưa có"}</p>
            {amountOverflow ? <p className="inline-error">Số tiền quá lớn (tối đa 15 chữ số).</p> : null}
            {!amountOverflow && amountInvalid ? <p className="inline-error">Số tiền phải lớn hơn 0.</p> : null}
          </div>
        ) : null}

        <div className="space-y-1">
          <MoneyInput
            value={totalNavDigits}
            onValueChange={(value) => {
              setTotalNavDigits(value.rawDigits);
              setTotalNavOverflow(value.isOverflow);
            }}
            placeholder="2,500,000,000"
            aria-invalid={totalNavInvalid}
          />
          <p className="input-helper">
            Tổng NAV gửi lên hệ thống: {totalNavValue ? formatCurrency(totalNavValue) : "Chưa có"}
          </p>
          {totalNavOverflow ? <p className="inline-error">Tổng NAV quá lớn (tối đa 15 chữ số).</p> : null}
          {!totalNavOverflow && totalNavInvalid ? <p className="inline-error">Tổng NAV phải lớn hơn 0.</p> : null}
        </div>

        {errorText ? <ErrorState message={errorText} /> : null}

        <Button className="w-full" onClick={() => createMutation.mutate()} disabled={!canSubmit}>
          {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Thực hiện
        </Button>
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title">Lịch sử giao dịch</h2>
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

        {transactionsQuery.isLoading ? (
          <LoadingState label="Đang tải giao dịch..." />
        ) : transactionsQuery.isError ? (
          <ErrorState message="Không tải được lịch sử giao dịch." />
        ) : txItems.length ? (
          tableViewEnabled && effectiveViewMode === "table" ? (
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="min-w-[760px] text-sm">
                <thead className="sticky top-0 z-20 bg-[var(--color-surface-3)]">
                  <tr>
                    <th className="sticky left-0 z-30 bg-[var(--color-surface-3)] px-3 py-2 text-left">ID</th>
                    <th className="px-3 py-2 text-left">Nhà đầu tư</th>
                    <th className="px-3 py-2 text-left">Loại</th>
                    <th className="px-3 py-2 text-left">Số tiền</th>
                    <th className="px-3 py-2 text-left">NAV</th>
                    <th className="px-3 py-2 text-left">Ngày</th>
                    <th className="px-3 py-2 text-left">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {txItems.map((tx) => (
                    <tr key={tx.id} className="border-t border-[var(--color-border)] bg-[var(--color-surface)]">
                      <td className="sticky left-0 z-10 bg-[var(--color-surface)] px-3 py-2">#{tx.id}</td>
                      <td className="px-3 py-2">{tx.investor_name}</td>
                      <td className="px-3 py-2">{tx.type}</td>
                      <td className="px-3 py-2">{formatCurrency(tx.amount)}</td>
                      <td className="px-3 py-2">{formatCurrency(tx.nav)}</td>
                      <td className="px-3 py-2">{formatDateTime(tx.date)}</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-2">
                          <Button
                            variant="secondary"
                            className="h-9 px-3 py-1 text-xs"
                            onClick={() => undoMutation.mutate(tx.id)}
                            disabled={undoMutation.isPending}
                            aria-label={`Hoàn tác giao dịch ${tx.id}`}
                          >
                            Hoàn tác
                          </Button>
                          <Button
                            variant="danger"
                            className="h-9 px-3 py-1 text-xs"
                            onClick={() => setDeleteTarget(tx.id)}
                            disabled={deleteMutation.isPending}
                            aria-label={`Xóa giao dịch ${tx.id}`}
                          >
                            Xóa
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

        {txItems.length ? (
          <div className={`list-stagger space-y-2 ${effectiveViewMode === "table" ? "hidden" : ""}`}>
            {txItems.map((tx) => (
              <article
                key={tx.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <button className="w-full text-left" onClick={() => setSelectedTx(tx)} type="button">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold">{tx.investor_name}</p>
                    <p className="text-xs text-[var(--color-muted)]">#{tx.id}</p>
                  </div>
                  <p className="mt-1 text-sm">{tx.type}</p>
                  <p className="text-xs text-[var(--color-muted)]">{formatDateTime(tx.date)}</p>
                </button>
                <div className="mt-3 flex gap-2">
                  <Button
                    variant="secondary"
                    className="flex-1"
                    onClick={() => undoMutation.mutate(tx.id)}
                    disabled={undoMutation.isPending}
                    aria-label={`Hoàn tác giao dịch ${tx.id}`}
                  >
                    Hoàn tác
                  </Button>
                  <Button
                    variant="danger"
                    className="flex-1"
                    onClick={() => setDeleteTarget(tx.id)}
                    disabled={deleteMutation.isPending}
                    aria-label={`Xóa giao dịch ${tx.id}`}
                  >
                    Xóa
                  </Button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState title="Chưa có giao dịch." description="Thêm giao dịch mới ở phần trên." />
        )}

        {loadMoreEnabled && transactionsQuery.hasNextPage ? (
          <div className="space-y-2">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => transactionsQuery.fetchNextPage()}
              disabled={transactionsQuery.isFetchingNextPage}
            >
              {transactionsQuery.isFetchingNextPage ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Tải thêm giao dịch
            </Button>
            <p className="text-center text-xs text-[var(--color-muted)]">
              Đang hiển thị {txItems.length}/{txTotal} giao dịch
            </p>
          </div>
        ) : null}
      </Card>

      <Dialog.Root open={!!selectedTx} onOpenChange={(open) => !open && setSelectedTx(null)}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40 data-[state=open]:animate-[overlay-in_180ms_ease-out]" />
          <Dialog.Content className="fixed inset-0 z-50 overflow-y-auto border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:h-auto md:max-h-[90vh] md:w-[520px] md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-2xl">
            <div className="sticky top-0 mb-3 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] pb-3">
              <Dialog.Title className="text-base font-semibold">Chi tiết giao dịch</Dialog.Title>
              <Dialog.Close asChild>
                <Button variant="secondary" className="h-9 w-9 p-0" aria-label="Đóng">
                  <X className="h-4 w-4" />
                </Button>
              </Dialog.Close>
            </div>
            {selectedTx ? (
              <div className="space-y-2 text-sm">
                <p>ID: {selectedTx.id}</p>
                <p>Nhà đầu tư: {selectedTx.investor_name}</p>
                <p>Loại: {selectedTx.type}</p>
                <p>Số tiền: {formatCurrency(selectedTx.amount)}</p>
                <p>NAV: {formatCurrency(selectedTx.nav)}</p>
                <p>Đơn vị quỹ: {selectedTx.units_change.toFixed(6)}</p>
                <p>Thời gian: {formatDateTime(selectedTx.date)}</p>
              </div>
            ) : null}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title="Xác nhận xóa giao dịch"
        description="Hành động này có thể ảnh hưởng số liệu quỹ. Bạn có chắc muốn tiếp tục?"
        confirmLabel="Xóa giao dịch"
        confirmVariant="danger"
        onConfirm={() => {
          if (deleteTarget === null) return;
          deleteMutation.mutate(deleteTarget);
        }}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
