"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Loader2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { apiClient } from "@/lib/api";
import type { TransactionCardDTO } from "@/lib/types";
import { formatCurrency, formatDateTime } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";

type TxType = "deposit" | "withdraw" | "nav_update";
type TxViewMode = "card" | "table";

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.accessToken);
  const [txType, setTxType] = useState<TxType>("deposit");
  const [investorId, setInvestorId] = useState("");
  const [amount, setAmount] = useState("");
  const [totalNav, setTotalNav] = useState("");
  const [txDate, setTxDate] = useState(new Date().toISOString().slice(0, 10));
  const [selectedTx, setSelectedTx] = useState<TransactionCardDTO | null>(null);
  const [viewMode, setViewMode] = useState<TxViewMode>("card");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const flagsQuery = useQuery({
    queryKey: ["feature-flags"],
    queryFn: () => apiClient.featureFlags(token || ""),
    enabled: !!token,
  });

  const tableViewEnabled = flagsQuery.data?.table_view ?? true;
  const loadMoreEnabled = flagsQuery.data?.transactions_load_more ?? true;

  const transactionsQuery = useInfiniteQuery({
    queryKey: ["transaction-cards", token],
    initialPageParam: 1,
    queryFn: ({ pageParam }) => apiClient.transactionCards(token || "", pageParam, 20),
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

  const createMutation = useMutation({
    mutationFn: () =>
      apiClient.createTransaction(token || "", {
        transaction_type: txType,
        investor_id: txType === "nav_update" ? undefined : Number(investorId),
        amount: txType === "nav_update" ? undefined : Number(amount),
        total_nav: Number(totalNav),
        transaction_date: txDate,
      }),
    onSuccess: () => {
      setAmount("");
      setTotalNav("");
      setStatusMessage("Đã cập nhật giao dịch thành công.");
      queryClient.invalidateQueries({ queryKey: ["transaction-cards", token] });
    },
    onError: () => setStatusMessage(null),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteTransaction(token || "", id),
    onSuccess: () => {
      setStatusMessage("Đã xoá giao dịch.");
      queryClient.invalidateQueries({ queryKey: ["transaction-cards", token] });
    },
  });

  const undoMutation = useMutation({
    mutationFn: (id: number) => apiClient.undoTransaction(token || "", id),
    onSuccess: () => {
      setStatusMessage("Đã hoàn tác giao dịch.");
      queryClient.invalidateQueries({ queryKey: ["transaction-cards", token] });
    },
  });

  const errorText = useMemo(() => {
    if (createMutation.error instanceof Error) return createMutation.error.message;
    return null;
  }, [createMutation.error]);

  return (
    <div className="app-page">
      <Card className="space-y-3">
        <h2 className="section-title">Thêm giao dịch / cập nhật NAV</h2>
        <div className="grid gap-2 sm:grid-cols-3">
          <select
            className="control-select"
            value={txType}
            onChange={(e) => setTxType(e.target.value as TxType)}
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
          <div className="grid gap-2 sm:grid-cols-2">
            <Input
              placeholder="ID nhà đầu tư"
              value={investorId}
              onChange={(e) => setInvestorId(e.target.value)}
            />
            <Input
              placeholder="Số tiền"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
        ) : null}
        <Input
          placeholder="Tổng NAV sau giao dịch"
          value={totalNav}
          onChange={(e) => setTotalNav(e.target.value)}
        />
        {errorText ? (
          <ErrorState message={errorText} />
        ) : null}
        {statusMessage ? (
          <p className="status-success">
            {statusMessage}
          </p>
        ) : null}
        <Button
          className="w-full"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          {createMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          Thực hiện
        </Button>
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="section-title">Lịch sử giao dịch</h2>
          {tableViewEnabled ? (
            <div className="hidden rounded-xl border border-[var(--color-border)] bg-white p-1 md:flex">
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${viewMode === "card" ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]" : "text-[var(--color-muted)]"}`}
                onClick={() => setViewMode("card")}
                type="button"
              >
                Thẻ
              </button>
              <button
                className={`rounded-lg px-3 py-1 text-xs font-medium ${viewMode === "table" ? "bg-[var(--color-primary-50)] text-[var(--color-primary)]" : "text-[var(--color-muted)]"}`}
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
            <div className="hidden overflow-x-auto rounded-xl border border-[var(--color-border)] md:block">
              <table className="min-w-full text-sm">
                <thead className="bg-[var(--color-surface-3)]">
                  <tr>
                    <th className="px-3 py-2 text-left">ID</th>
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
                    <tr key={tx.id} className="border-t border-[var(--color-border)] bg-white">
                      <td className="px-3 py-2">#{tx.id}</td>
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
                          >
                            Hoàn tác
                          </Button>
                          <Button
                            variant="danger"
                            className="h-9 px-3 py-1 text-xs"
                            onClick={() => deleteMutation.mutate(tx.id)}
                            disabled={deleteMutation.isPending}
                          >
                            Xoá
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
          <div className={`list-stagger space-y-2 ${effectiveViewMode === "table" ? "md:hidden" : ""}`}>
            {txItems.map((tx) => (
              <article
                key={tx.id}
                className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3"
              >
                <button
                  className="w-full text-left"
                  onClick={() => setSelectedTx(tx)}
                  type="button"
                >
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
                  >
                    Hoàn tác
                  </Button>
                  <Button
                    variant="danger"
                    className="flex-1"
                    onClick={() => deleteMutation.mutate(tx.id)}
                    disabled={deleteMutation.isPending}
                  >
                    Xoá
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
              {transactionsQuery.isFetchingNextPage ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
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
          <Dialog.Content className="fixed inset-x-4 bottom-4 z-50 rounded-2xl border border-[var(--color-border)] bg-white p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:w-[520px] md:-translate-x-1/2 md:-translate-y-1/2">
            <div className="mb-3 flex items-center justify-between">
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
    </div>
  );
}
