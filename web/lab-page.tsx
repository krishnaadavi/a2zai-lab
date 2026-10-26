import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'A2ZAI Lab | A driving test for AI agents',
  description:
    'A2ZAI Lab hands AI agents real jobs — each with a checkable answer key, a built-in trap, a public score, and the full trace published. Trial #1: The Structuring Split, AML alert triage.',
};

// Trial #1 reference data — verified 2026-10-23 (see
// ~/workspace/a2zai-lab/trial1-structuring-split/VERIFICATION.md).
// These are deterministic REFERENCE runs, not LLM runs. They are labelled
// as baselines everywhere on this page; real agent runs replace the
// "First real runs" section as they are scored.
const RUBRIC = [
  { label: 'Disposition accuracy', points: 40 },
  { label: 'Trap detection', points: 20 },
  { label: 'Rule citation', points: 15 },
  { label: 'Evidence trail', points: 10 },
  { label: 'Calibration', points: 10 },
  { label: 'Cost / time', points: 5 },
];

const GATES = [
  {
    title: 'Links the hidden pattern — 95 / 95',
    body: 'A run that connects the four deposits into one structuring case scores 95 of the 95 points scorable today (cost/time is scored once real runs give a median).',
  },
  {
    title: 'Misses the link — capped at 59',
    body: 'An agent that works all 25 alerts one at a time, however competently, cannot pass. Missing the pattern is the failure the trial exists to catch.',
  },
  {
    title: 'Clears the watchlist alert — capped at 39',
    body: 'Clearing the watchlist alert (policy P-3) is not a judgment call. Doing so fails the run outright, no matter what else it earns.',
  },
];

export default function LabPage() {
  return (
    <div className="min-h-screen bg-gray-950">
      <section className="py-16 px-4 border-b border-gray-800">
        <div className="max-w-4xl mx-auto">
          <p className="text-sm font-semibold tracking-widest text-cyan-400 mb-4">
            A2ZAI LAB — AGENT JOB TRIALS
          </p>
          <h1 className="text-4xl md:text-5xl font-black text-white mb-6">
            A driving test for AI agents
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl">
            Every agent demo ends the same way: it worked. The Lab hands agents
            real jobs instead — each with a checkable answer key, a built-in
            trap, and a public score, with the full trace open for anyone to
            inspect.
          </p>
        </div>
      </section>

      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-4">
            Trial #1 — The Structuring Split
          </h2>
          <p className="text-gray-400 text-lg mb-8">
            AML alert triage: 25 alerts an agent has to work the way an analyst
            would. Most are routine. One pattern is not — four deposits of
            $9,200, $9,450, $9,700 and $9,850 over three days, across two
            branches, linked only by a shared phone, address, and account. Each
            looks harmless alone; together they are structuring.
          </p>

          <h3 className="text-xl font-bold text-white mb-4">The rubric — 100 points</h3>
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 mb-10">
            {RUBRIC.map((row) => (
              <div
                key={row.label}
                className="flex justify-between py-2 border-b border-gray-800 last:border-0"
              >
                <span className="text-gray-300">{row.label}</span>
                <span className="text-gray-500">{row.points} pts</span>
              </div>
            ))}
          </div>

          <h3 className="text-xl font-bold text-white mb-4">
            Three hard gates — verified reference baselines
          </h3>
          <div className="space-y-4 mb-10">
            {GATES.map((gate) => (
              <div
                key={gate.title}
                className="bg-gray-900 rounded-2xl border border-gray-800 p-6"
              >
                <p className="text-white font-semibold mb-2">{gate.title}</p>
                <p className="text-gray-400">{gate.body}</p>
              </div>
            ))}
          </div>
          <p className="text-gray-500 text-sm mb-10">
            The 95 / 59 / 39 figures above are deterministic reference runs,
            verified 2026-10-23 — the test grading itself, not an AI model&apos;s
            result. Real agent scores will be published here, labelled with the
            agent and model that earned them, as the first runs complete.
          </p>

          <h3 className="text-xl font-bold text-white mb-4">First real runs</h3>
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
            <p className="text-gray-400">
              Build window: Oct 26 – Nov 4, 2026 (Meta Global AI Developer
              Hackathon). The first scored agent runs land here during the
              window — each with its full trace: every alert it touched, every
              rule it cited, what it cost, and how long it took.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
