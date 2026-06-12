import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";
import { FullPageSpinner } from "@/components/common/FullPageSpinner";

export default function LoginPage() {
  return (
    <Suspense fallback={<FullPageSpinner />}>
      <LoginForm />
    </Suspense>
  );
}
