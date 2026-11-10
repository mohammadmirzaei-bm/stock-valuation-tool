import * as React from "react";
import { TriangleAlert } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

/**
 * Confirmation step for destructive actions (resetting the workflow wipes the
 * student's persisted work). Flat surface per the design spec; the confirm
 * button carries the destructive tone and the cancel button is the safe exit.
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  cancelLabel = "انصراف",
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  cancelLabel?: string;
  onConfirm: () => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <TriangleAlert className="h-4 w-4 shrink-0 text-warning" aria-hidden />
            {title}
          </DialogTitle>
          <DialogDescription className="leading-6">{description}</DialogDescription>
        </DialogHeader>
        <div className="flex flex-wrap justify-end gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            {confirmLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/** The shared wording for the one destructive action in the app today. */
export const RESET_DIALOG_COPY = {
  title: "بازنشانی گردش کار؟",
  description:
    "تمام پیش‌بینی‌ها، WACC، اطلاعات ترازنامه و بازه‌های جمع‌شده پاک می‌شوند و پیشرفت گام‌ها از نو شروع می‌شود. این کار قابل بازگشت نیست.",
  confirmLabel: "بله، بازنشانی کن",
} as const;

/** Small helper so pages can wire the dialog with one state hook. */
export function useConfirmDialog() {
  const [open, setOpen] = React.useState(false);
  return { open, onOpenChange: setOpen, request: () => setOpen(true) };
}