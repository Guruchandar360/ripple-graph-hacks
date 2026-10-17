import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  Check,
  CheckCheck,
  ChevronRight,
  Clock3,
  ExternalLink,
  FileCheck2,
  LoaderCircle,
  LockKeyhole,
  Rocket,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { api } from "../api";
type CheckItem = {
  id: string;
  title: string;
  ready: boolean;
  detail: string;
  url: string | null;
  human_required: boolean;
};
type Readiness = {
  checks: CheckItem[];
  ready: number;
  total: number;
  primary_track: string;
  deadline: string;
  note: string;
  verification: { url?: string; label?: string } | null;
};
export function LaunchReadiness({ onConfigure }: { onConfigure: () => void }) {
  const [data, setData] = useState<Readiness | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api<Readiness>("/readiness")
      .then((d) => {
        if (active) setData(d);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <>
      <section className="page-intro">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            FROM PROTOTYPE TO PROOF
          </div>
          <h1>Ready for the spotlight.</h1>
          <p>Every requirement. An honest status. A clear next step.</p>
        </div>
        <span className="hero-icon">
          <Rocket size={28} />
        </span>
      </section>
      <div className="launch-banner">
        <div className="launch-orbit">
          <ShieldCheck size={28} />
        </div>
        <div>
          <span className="eyebrow">SUBMISSION READINESS</span>
          <h2>
            {data
              ? `${data.ready} of ${data.total} preparation checks complete`
              : "Checking the evidence…"}
          </h2>
          <p>
            {data?.note ??
              "Source files, runtime connections and measured artifacts are checked separately."}
          </p>
        </div>
        <div className="deadline">
          <Clock3 size={15} />
          <span>
            SUBMIT BEFORE<strong>18 Oct · 11:59 PM IST</strong>
          </span>
        </div>
      </div>
      {error && (
        <div className="inline-warning">
          <TriangleAlert size={15} />
          {error}
        </div>
      )}
      {!data && !error && (
        <div className="loading-block">
          <LoaderCircle className="spin" size={22} />
          Checking submission materials…
        </div>
      )}
      <div className="readiness-grid">
        {data?.checks.map((item, i) => (
          <article
            className={`readiness-card ${item.ready ? "ready" : ""}`}
            key={item.id}
          >
            <div className="readiness-card-top">
              <span className="mono-counter">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span
                className={`readiness-state ${item.ready ? "done" : item.human_required ? "human" : ""}`}
              >
                {item.ready ? (
                  <>
                    <Check size={12} />
                    Prepared
                  </>
                ) : item.human_required ? (
                  <>
                    <LockKeyhole size={12} />
                    Participant step
                  </>
                ) : (
                  <>
                    <Clock3 size={12} />
                    Pending
                  </>
                )}
              </span>
            </div>
            <h3>{item.title}</h3>
            <p>{item.detail}</p>
            {item.url && (
              <a href={item.url} target="_blank" rel="noreferrer">
                {item.id === "repository"
                  ? "View public source"
                  : "Open official registration"}
                <ArrowUpRight size={13} />
              </a>
            )}
            {["graph", "model"].includes(item.id) && !item.ready && (
              <button onClick={onConfigure}>
                Connection details
                <ChevronRight size={13} />
              </button>
            )}
          </article>
        ))}
      </div>
      <div className="launch-links">
        <article>
          <FileCheck2 size={22} />
          <div>
            <strong>Know what you are submitting.</strong>
            <p>
              The contributor guide explains the model, native queries,
              execution guards and limits.
            </p>
          </div>
          <a
            href="https://github.com/Guruchandar360/ripple-graph-hacks/blob/main/docs/CONTRIBUTOR_GUIDE.md"
            target="_blank"
            rel="noreferrer"
          >
            Read the guide
            <ExternalLink size={13} />
          </a>
        </article>
        <article>
          <CheckCheck size={22} />
          <div>
            <strong>Proof before promises.</strong>
            <p>
              CI runs the real database tests. Live model results require a
              separate configured run.
            </p>
          </div>
          <a
            href="https://github.com/Guruchandar360/ripple-graph-hacks/actions"
            target="_blank"
            rel="noreferrer"
          >
            Open CI
            <ExternalLink size={13} />
          </a>
        </article>
      </div>
    </>
  );
}
