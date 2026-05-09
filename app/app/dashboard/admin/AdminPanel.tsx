"use client";

import { useState } from "react";

// ── Static config ────────────────────────────────────────────────────────────

const SIMPLE_SPORTS = ["NFL", "NCAAF", "BASEBALL", "HOCKEY", "NBA", "NCAAB"] as const;

const FIGHT_LEAGUES = [
  { key: "mma_mixed_martial_arts", label: "MMA" },
  { key: "boxing_boxing",          label: "Boxing" },
];

const SOCCER_LEAGUES = [
  { key: "soccer_epl",                        label: "EPL" },
  { key: "soccer_spain_la_liga",              label: "La Liga" },
  { key: "soccer_germany_bundesliga",         label: "Bundesliga" },
  { key: "soccer_italy_serie_a",              label: "Serie A" },
  { key: "soccer_france_ligue_one",           label: "Ligue 1" },
  { key: "soccer_usa_mls",                    label: "MLS" },
  { key: "soccer_brazil_campeonato",          label: "Brazil" },
  { key: "soccer_argentina_primera_division", label: "Argentina" },
  { key: "soccer_efl_champ",                  label: "Championship" },
  { key: "soccer_england_league1",            label: "League 1" },
  { key: "soccer_england_league2",            label: "League 2" },
  { key: "soccer_fifa_world_cup",             label: "World Cup" },
  { key: "soccer_uefa_champs_league",         label: "UCL" },
  { key: "soccer_uefa_europa_league",         label: "Europa" },
  { key: "soccer_netherlands_eredivisie",     label: "Eredivisie" },
  { key: "soccer_portugal_primeira_liga",     label: "Primeira Liga" },
  { key: "soccer_turkey_super_league",        label: "Süper Lig" },
];

// ── Sub-components ───────────────────────────────────────────────────────────

function SectionHeader({ title }: { title: string }) {
  return (
    <h2 className="font-display text-base font-semibold text-text-primary mb-4">{title}</h2>
  );
}

function Toggle({ on, onClick }: { on: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        on ? "bg-accent" : "bg-[rgba(255,255,255,0.12)]"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white shadow transition-transform ${
          on ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

function Checkbox({ checked, onChange, label }: { checked: boolean; onChange: () => void; label: string }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer group select-none">
      <div
        onClick={onChange}
        className={`w-4 h-4 rounded border flex items-center justify-center transition-all flex-shrink-0 ${
          checked ? "bg-accent border-accent" : "border-[rgba(255,255,255,0.2)] group-hover:border-[rgba(0,212,170,0.4)]"
        }`}
      >
        {checked && (
          <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
            <path d="M1 4L3.5 6.5L9 1" stroke="#060912" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
      <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">{label}</span>
    </label>
  );
}

// ── Types ────────────────────────────────────────────────────────────────────

type Config = Record<string, string>;

function parseActiveSports(val: string): Set<string> {
  return new Set(val.split(",").map(s => s.trim().toUpperCase()).filter(Boolean));
}

function parseLeagues(val: string): Set<string> {
  return new Set(val.split(",").map(s => s.trim()).filter(Boolean));
}

// ── Main component ───────────────────────────────────────────────────────────

export default function AdminPanel({ initialConfig }: { initialConfig: Config }) {
  const [dayMinutes,  setDayMinutes]  = useState(initialConfig.day_poll_minutes  ?? "15");
  const [nightMinutes, setNightMinutes] = useState(initialConfig.night_poll_minutes ?? "120");

  const [activeSports, setActiveSports] = useState<Set<string>>(
    parseActiveSports(initialConfig.active_sports ?? "BASEBALL,HOCKEY,NBA,SOCCER,FIGHTS")
  );
  const [fightLeagues, setFightLeagues] = useState<Set<string>>(
    parseLeagues(initialConfig.leagues_fights ?? "mma_mixed_martial_arts,boxing_boxing")
  );
  const [soccerLeagues, setSoccerLeagues] = useState<Set<string>>(
    parseLeagues(initialConfig.leagues_soccer ?? "soccer_epl")
  );
  const [tennisText, setTennisText] = useState(initialConfig.leagues_tennis ?? "");

  const [saving, setSaving] = useState(false);
  const [saved,  setSaved]  = useState(false);
  const [error,  setError]  = useState<string | null>(null);

  function toggleSport(sport: string) {
    setActiveSports(prev => {
      const next = new Set(prev);
      next.has(sport) ? next.delete(sport) : next.add(sport);
      return next;
    });
  }

  function toggleSet(set: Set<string>, setFn: (s: Set<string>) => void, key: string) {
    const next = new Set(set);
    next.has(key) ? next.delete(key) : next.add(key);
    setFn(next);
  }

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const res = await fetch("/api/admin/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          day_poll_minutes:  dayMinutes,
          night_poll_minutes: nightMinutes,
          active_sports:     [...activeSports].join(","),
          leagues_fights:    [...fightLeagues].join(","),
          leagues_soccer:    [...soccerLeagues].join(","),
          leagues_tennis:    tennisText.trim(),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-[680px]">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary mb-1">Worker Config</h1>
          <p className="text-text-secondary text-sm">Changes take effect on the next Railway poll cycle.</p>
        </div>
        <div className="flex items-center gap-3">
          {saved  && <span className="text-accent text-sm font-display font-semibold">Saved ✓</span>}
          {error  && <span className="text-red-400 text-sm">{error}</span>}
          <button
            onClick={handleSave}
            disabled={saving}
            className="font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-accent text-bg-primary border-2 border-accent hover:bg-accent-hover hover:border-accent-hover transition-all hover:-translate-y-[1px] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* Poll Cadence */}
      <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 mb-4">
        <SectionHeader title="Poll Cadence" />
        <div className="flex gap-8">
          <div>
            <label className="text-text-muted text-xs font-display font-semibold uppercase tracking-[0.08em] block mb-2">Day (minutes)</label>
            <input
              type="number" min={1} max={120} value={dayMinutes}
              onChange={e => setDayMinutes(e.target.value)}
              className="w-24 bg-bg-primary border border-qbl-border rounded-[8px] px-3 py-2 text-text-primary font-display font-semibold text-sm focus:outline-none focus:border-accent transition-colors"
            />
          </div>
          <div>
            <label className="text-text-muted text-xs font-display font-semibold uppercase tracking-[0.08em] block mb-2">Night (minutes)</label>
            <input
              type="number" min={1} max={240} value={nightMinutes}
              onChange={e => setNightMinutes(e.target.value)}
              className="w-24 bg-bg-primary border border-qbl-border rounded-[8px] px-3 py-2 text-text-primary font-display font-semibold text-sm focus:outline-none focus:border-accent transition-colors"
            />
          </div>
        </div>
        <p className="text-text-muted text-xs mt-3">Night window: 10 PM – 7 AM Eastern</p>
      </section>

      {/* Active Sports */}
      <section className="bg-bg-surface border border-qbl-border rounded-[12px] p-6 mb-4">
        <SectionHeader title="Active Sports" />
        <div className="space-y-4">

          {/* Simple sports — toggle only */}
          <div className="grid grid-cols-2 gap-3">
            {SIMPLE_SPORTS.map(sport => (
              <div key={sport} className="flex items-center justify-between py-2 px-3 rounded-[8px] bg-bg-primary border border-qbl-border">
                <span className="font-display font-semibold text-sm text-text-primary">{sport}</span>
                <Toggle on={activeSports.has(sport)} onClick={() => toggleSport(sport)} />
              </div>
            ))}
          </div>

          <div className="border-t border-qbl-border" />

          {/* FIGHTS */}
          <div>
            <div className="flex items-center justify-between py-2 px-3 rounded-[8px] bg-bg-primary border border-qbl-border mb-2">
              <span className="font-display font-semibold text-sm text-text-primary">FIGHTS</span>
              <Toggle on={activeSports.has("FIGHTS")} onClick={() => toggleSport("FIGHTS")} />
            </div>
            {activeSports.has("FIGHTS") && (
              <div className="ml-4 pl-4 border-l-2 border-accent border-opacity-30 grid grid-cols-2 gap-2 py-2">
                {FIGHT_LEAGUES.map(l => (
                  <Checkbox
                    key={l.key}
                    checked={fightLeagues.has(l.key)}
                    onChange={() => toggleSet(fightLeagues, setFightLeagues, l.key)}
                    label={l.label}
                  />
                ))}
              </div>
            )}
          </div>

          {/* SOCCER */}
          <div>
            <div className="flex items-center justify-between py-2 px-3 rounded-[8px] bg-bg-primary border border-qbl-border mb-2">
              <span className="font-display font-semibold text-sm text-text-primary">SOCCER</span>
              <Toggle on={activeSports.has("SOCCER")} onClick={() => toggleSport("SOCCER")} />
            </div>
            {activeSports.has("SOCCER") && (
              <div className="ml-4 pl-4 border-l-2 border-accent border-opacity-30 py-2">
                <div className="grid grid-cols-3 gap-2">
                  {SOCCER_LEAGUES.map(l => (
                    <Checkbox
                      key={l.key}
                      checked={soccerLeagues.has(l.key)}
                      onChange={() => toggleSet(soccerLeagues, setSoccerLeagues, l.key)}
                      label={l.label}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* TENNIS */}
          <div>
            <div className="flex items-center justify-between py-2 px-3 rounded-[8px] bg-bg-primary border border-qbl-border mb-2">
              <span className="font-display font-semibold text-sm text-text-primary">TENNIS</span>
              <Toggle on={activeSports.has("TENNIS")} onClick={() => toggleSport("TENNIS")} />
            </div>
            {activeSports.has("TENNIS") && (
              <div className="ml-4 pl-4 border-l-2 border-accent border-opacity-30 py-2">
                <label className="text-text-muted text-xs font-display font-semibold uppercase tracking-[0.08em] block mb-2">
                  League slugs (comma-separated)
                </label>
                <input
                  type="text"
                  value={tennisText}
                  onChange={e => setTennisText(e.target.value)}
                  placeholder="tennis_atp_us_open,tennis_wta_us_open"
                  className="w-full bg-bg-primary border border-qbl-border rounded-[8px] px-3 py-2 text-text-primary text-sm font-mono focus:outline-none focus:border-accent transition-colors placeholder:text-text-muted"
                />
                <p className="text-text-muted text-xs mt-1.5">Find slugs at the-odds-api.com/sports</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
