import type { ScutellataProfile } from "@/app/lib/catalog";

/**
 * O perfil scutellata mostrado como grandeza, não como badge.
 *
 * Cada eixo traz a **escala visível** e a unidade. `recruitment` é o único
 * numérico de verdade (1..=32, faixa nativa do Buzz), então tem barra; os outros
 * três são ordinais de três níveis e ganham degraus, que é a forma honesta de
 * mostrar ordinal — barra contínua sugeriria uma precisão que o dado não tem.
 */

const THRESHOLD_ORDER = ["high", "medium", "low"] as const;
const PERSISTENCE_ORDER = ["short", "medium", "long"] as const;
const PROPAGATION_ORDER = ["low", "medium", "high"] as const;

const RECRUITMENT_MAX = 32;

function Steps({
  levels,
  value,
  label,
  hint,
}: {
  levels: readonly string[];
  value: string;
  label: string;
  hint: string;
}) {
  const index = levels.indexOf(value);
  return (
    <div className="axis">
      <div className="axis-head">
        <span className="axis-name">{label}</span>
        <span className="axis-value">{value}</span>
      </div>
      <div className="axis-steps" role="img" aria-label={`${label}: ${value}`}>
        {levels.map((level, i) => (
          <span key={level} className="step" data-on={i <= index || undefined} />
        ))}
      </div>
      <p className="axis-hint">{hint}</p>
    </div>
  );
}

export function ProfileMeter({ profile }: { profile: ScutellataProfile }) {
  const recruitmentPct = Math.round((profile.recruitment / RECRUITMENT_MAX) * 100);

  return (
    <div className="profile">
      <div className="axis">
        <div className="axis-head">
          <span className="axis-name">recruitment</span>
          <span className="axis-value">
            {profile.recruitment}
            <span className="axis-unit"> / {RECRUITMENT_MAX} parallel</span>
          </span>
        </div>
        <div
          className="axis-bar"
          role="img"
          aria-label={`recruitment: ${profile.recruitment} of ${RECRUITMENT_MAX} parallel conversations`}
        >
          <span className="axis-fill" style={{ inlineSize: `${recruitmentPct}%` }} />
        </div>
        <p className="axis-hint">
          Compiles to the agent&apos;s native <code>parallelism</code> field. The 1–32 range is
          Buzz&apos;s, not ours.
        </p>
      </div>

      <Steps
        levels={THRESHOLD_ORDER}
        value={profile.threshold}
        label="threshold"
        hint="How little it takes to get a response. Low means it reacts to everything in its channels, not only to mentions."
      />
      <Steps
        levels={PERSISTENCE_ORDER}
        value={profile.persistence}
        label="persistence"
        hint="How long it stays on a task. Compiles to idle and turn timeouts."
      />
      <Steps
        levels={PROPAGATION_ORDER}
        value={profile.propagation}
        label="propagation"
        hint="Catalog metadata only. Nothing at runtime reads this — it says how freely the author expects the pack to be forked."
      />
    </div>
  );
}
