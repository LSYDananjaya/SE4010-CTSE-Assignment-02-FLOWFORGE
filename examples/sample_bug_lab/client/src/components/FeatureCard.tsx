export function FeatureCard(props: { title: string; severity: "low" | "medium" | "high" }) {
  const palette = {
    low: "#22c55e",
    medium: "#f59e0b",
    // BUG B6: High severity should not reuse a calm cyan tone.
    high: "#22d3ee"
  };

  return (
    <article style={{ borderColor: palette[props.severity], borderWidth: 2, borderStyle: "solid" }}>
      <h3>{props.title}</h3>
      <span>{props.severity}</span>
    </article>
  );
}
