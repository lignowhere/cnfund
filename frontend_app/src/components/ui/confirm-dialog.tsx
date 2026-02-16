"use client";

import * as Dialog from "@radix-ui/react-dialog";

import { Button } from "@/components/ui/button";

type ConfirmDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: "primary" | "danger";
  onConfirm: () => void;
  isPending?: boolean;
};

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Xác nhận",
  cancelLabel = "Hủy",
  confirmVariant = "primary",
  onConfirm,
  isPending = false,
}: ConfirmDialogProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[95] bg-black/40 data-[state=open]:animate-[overlay-in_160ms_ease-out]" />
        <Dialog.Content className="fixed inset-x-0 bottom-0 z-[96] max-h-[90vh] overflow-y-auto rounded-t-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 shadow-2xl data-[state=open]:animate-[fade-up_220ms_ease-out] md:inset-x-auto md:left-1/2 md:top-1/2 md:w-[420px] md:-translate-x-1/2 md:-translate-y-1/2 md:rounded-2xl">
          <Dialog.Title className="text-base font-semibold">{title}</Dialog.Title>
          {description ? <Dialog.Description className="mt-2 text-sm text-[var(--color-muted)]">{description}</Dialog.Description> : null}
          <div className="mt-4 flex gap-2">
            <Button
              type="button"
              variant={confirmVariant === "danger" ? "danger" : "primary"}
              className="flex-1"
              onClick={onConfirm}
              disabled={isPending}
            >
              {confirmLabel}
            </Button>
            <Dialog.Close asChild>
              <Button type="button" variant="secondary" className="flex-1" disabled={isPending}>
                {cancelLabel}
              </Button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
