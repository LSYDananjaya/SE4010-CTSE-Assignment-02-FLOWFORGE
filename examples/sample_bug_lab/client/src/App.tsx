import { AuthGate } from "./components/AuthGate";
import { EditTaskModal } from "./components/EditTaskModal";
import { FeatureCard } from "./components/FeatureCard";
import { FilterBar } from "./components/FilterBar";

export function App() {
  return (
    <AuthGate>
      <main>
        <FilterBar />
        <FeatureCard title="Task dashboard" severity="high" />
        <EditTaskModal />
      </main>
    </AuthGate>
  );
}
