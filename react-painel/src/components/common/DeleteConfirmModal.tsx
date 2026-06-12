import {
  Button,
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@chakra-ui/react";

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onOpenChange: (details: { open: boolean }) => void;
  onConfirm: () => void;
  title?: string;
  description?: string;
  isDeleting?: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  onOpenChange,
  onConfirm,
  title = "Confirmar Exclusão",
  description = "Tem certeza que deseja excluir este registro? Essa ação não pode ser desfeita.",
  isDeleting = false,
}: DeleteConfirmModalProps) {
  return (
    <DialogRoot open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <p>{description}</p>
        </DialogBody>
        <DialogFooter>
          <DialogActionTrigger asChild>
            <Button variant="outline" disabled={isDeleting}>
              Cancelar
            </Button>
          </DialogActionTrigger>
          <Button colorPalette="red" loading={isDeleting} onClick={onConfirm}>
            Excluir
          </Button>
        </DialogFooter>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
}
