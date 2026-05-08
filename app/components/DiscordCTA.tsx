import DiscordIcon from "./DiscordIcon";

interface Props {
  variant?: "compact" | "full";
  heading?: string;
  subtext?: string;
  href?: string;
}

export default function DiscordCTA({
  variant = "compact",
  heading = "Get real-time alerts on Discord",
  subtext = "Free to join. No credit card required.",
  href = "#",
}: Props) {
  if (variant === "compact") {
    return (
      <div className="rounded-[12px] border border-[rgba(88,101,242,0.25)] bg-[rgba(88,101,242,0.05)] px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-display font-semibold text-text-primary text-sm">{heading}</p>
          <p className="text-text-muted text-xs mt-0.5">{subtext}</p>
        </div>
        <a
          href={href}
          className="shrink-0 inline-flex items-center gap-2 font-display font-semibold text-sm px-5 py-2.5 rounded-[8px] bg-discord text-white transition-all hover:bg-[#4752c4] hover:-translate-y-[1px] hover:shadow-[0_4px_16px_rgba(88,101,242,0.4)]"
        >
          <DiscordIcon size={16} />
          Join Discord
        </a>
      </div>
    );
  }

  return (
    <section className="relative py-[100px] bg-bg-primary overflow-hidden">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(88,101,242,0.06) 0%, transparent 60%)",
        }}
      />
      <div className="relative max-w-[600px] mx-auto px-6 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[rgba(88,101,242,0.12)] border border-[rgba(88,101,242,0.2)] text-discord mb-6">
          <DiscordIcon size={28} />
        </div>
        <h2 className="font-display text-[clamp(1.4rem,3vw,2rem)] font-semibold text-text-primary mb-3">
          {heading}
        </h2>
        <p className="text-text-secondary mb-8 leading-[1.7] text-[1.05rem]">{subtext}</p>
        <a
          href={href}
          className="btn-pulse relative z-10 inline-flex items-center gap-2.5 font-display font-semibold text-[1.05rem] px-9 py-4 rounded-[12px] bg-discord text-white border-2 border-discord transition-all duration-250 hover:bg-[#4752c4] hover:border-[#4752c4] hover:-translate-y-[2px] hover:shadow-[0_6px_30px_rgba(88,101,242,0.4)]"
        >
          <DiscordIcon size={22} />
          Join Discord — It&apos;s Free
        </a>
        <p className="text-text-muted text-[0.85rem] mt-5">Free to join. No credit card required.</p>
      </div>
    </section>
  );
}
