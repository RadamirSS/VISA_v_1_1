import { BotSimulator } from "@/components/telegram/bot-simulator";
import { Section } from "@/components/ui/primitives";

export default function TelegramBotDemoPage() {
  return (
    <Section eyebrow="Telegram Bot Demo" title="Прототип бота для записи в консульство" description="Интерфейс имитирует Telegram-поток и доходит до финального шага, где реальная запись и оплата намеренно отключены.">
      <BotSimulator />
    </Section>
  );
}
