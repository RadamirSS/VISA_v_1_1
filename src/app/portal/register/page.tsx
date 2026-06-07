import { Suspense } from "react";
import { RegisterForm } from "@/components/portal/register-form";
import { Section } from "@/components/ui/primitives";

export default function PortalRegisterPage({
  searchParams
}: {
  searchParams?: { invite?: string };
}) {
  return (
    <Section eyebrow="Portal Access" title="Регистрация по приглашению" description="Реальная аутентификация не подключена. Это mock-слой, который легко заменить позже.">
      <Suspense fallback={null}>
        <RegisterForm initialInvite={searchParams?.invite ?? ""} />
      </Suspense>
    </Section>
  );
}
