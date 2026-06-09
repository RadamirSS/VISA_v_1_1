import { formatProviderDisplayName } from "../lib/cabinet";
import type { ConsulateOption, CountryOption } from "../lib/types";

export function CountryCard({
  country,
  isActive,
  onSelect
}: {
  country: CountryOption | { code: string; name_ru: string; suits_for_ru: string };
  isActive: boolean;
  onSelect: () => void;
}) {
  return (
    <button className={isActive ? "surface-card option-card active" : "surface-card option-card"} onClick={onSelect} type="button">
      <div>
        <h3>{country.name_ru}</h3>
        <p className="muted-text">{country.suits_for_ru}</p>
      </div>
    </button>
  );
}

export function ConsulateCard({
  consulate,
  isActive,
  onSelect
}: {
  consulate: ConsulateOption;
  isActive: boolean;
  onSelect: () => void;
}) {
  return (
    <button className={isActive ? "surface-card option-card active" : "surface-card option-card"} onClick={onSelect} type="button">
      <div className="card-row">
        <div>
          <h3>{consulate.city}</h3>
          <p className="muted-text">Визовый центр: {formatProviderDisplayName(consulate.provider)}</p>
          <p className="muted-text">
            Статус: {consulate.verification_status === "verified" ? "Проверено" : "Требует проверки менеджером"}
          </p>
        </div>
        <span className={consulate.verification_status === "verified" ? "chip verified" : "chip warning"}>
          {consulate.verification_status === "verified" ? "Проверено" : "Менеджер уточнит"}
        </span>
      </div>
      {consulate.verification_status === "needs_verification" ? (
        <p className="muted-text">Доступность этого города менеджер уточнит перед подтверждением записи.</p>
      ) : null}
    </button>
  );
}
