"use client";

import { useEffect, useState } from "react";

type Sample = {
    id: number;
    name: string;
    actual_label: "normal" | "attack";
    attack_category: string;
    record: Record<string, string | number>;
};

type Prediction = {
    prediction: "normal" | "attack";
    attack_probability: number;
    threshold: number;
};

const API_URL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Home() {
    const [samples, setSamples] = useState<Sample[]>([]);
    const [selectedId, setSelectedId] = useState("");
    const [result, setResult] = useState<Prediction | null>(null);
    const [loading, setLoading] = useState(true);
    const [predicting, setPredicting] = useState(false);
    const [error, setError] = useState("");

    const selectedSample = samples.find(
        (sample) => String(sample.id) === selectedId
    );

    // Fetch the demo records when the page opens.
    useEffect(() => {
        const controller = new AbortController();

        async function loadSamples() {
            try {
                const response = await fetch(`${API_URL}/samples`, {
                    signal: controller.signal,
                });

                if (!response.ok) {
                    throw new Error(`Could not load samples (${response.status}).`);
                }

                const data: Sample[] = await response.json();

                if (!controller.signal.aborted) {
                    setSamples(data);
                    setSelectedId(data.length ? String(data[0].id) : "");
                }
            } catch (err) {
                if (!controller.signal.aborted) {
                    setError(
                        err instanceof Error ? err.message : "Could not load samples."
                    );
                }
            } finally {
                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            }
        }

        loadSamples();

        // Cancel the request if the component is removed.
        return () => controller.abort();
    }, []);

    async function runPrediction() {
        if (!selectedSample || predicting) return;

        setPredicting(true);
        setResult(null);
        setError("");

        try {
            const response = await fetch(`${API_URL}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },

                // Send features only; the dataset label stays in the UI.
                body: JSON.stringify({ record: selectedSample.record }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : `Prediction failed (${response.status}).`
                );
            }

            setResult(data as Prediction);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Could not run prediction."
            );
        } finally {
            setPredicting(false);
        }
    }

    return (
        <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100">
            <div className="mx-auto max-w-2xl space-y-8">
                <header>
                    <p className="text-sm font-medium text-cyan-400">
                        UNSW-NB15 · XGBoost
                    </p>
                    <h1 className="mt-2 text-3xl font-semibold">
                        Network Intrusion Detection
                    </h1>
                    <p className="mt-3 text-slate-400">
                        Select a recorded network flow and run detection.
                    </p>
                </header>

                <section className="space-y-5 rounded-xl border border-slate-700 p-6">
                    <label htmlFor="sample" className="block font-medium">
                        Sample network flow
                    </label>

                    <select
                        id="sample"
                        value={selectedId}
                        disabled={loading || predicting || samples.length === 0}
                        onChange={(event) => {
                            setSelectedId(event.target.value);
                            // Clear the previous flow's result when selection changes.
                            setResult(null);
                            setError("");
                        }}
                        className="w-full rounded-lg border border-slate-600 bg-slate-900 p-3 disabled:opacity-50"
                    >
                        {samples.length === 0 && (
                            <option value="">
                                {loading ? "Loading samples…" : "No samples available"}
                            </option>
                        )}

                        {samples.map((sample) => (
                            <option key={sample.id} value={sample.id}>
                                {sample.name}
                            </option>
                        ))}
                    </select>

                    {selectedSample && (
                        <dl className="grid grid-cols-3 gap-4 text-sm">
                            {["proto", "service", "state"].map((field) => (
                                <div key={field}>
                                    <dt className="text-slate-400">
                                        {field === "proto" ? "Protocol" : field}
                                    </dt>
                                    <dd className="mt-1 font-medium">
                                        {selectedSample.record[field]}
                                    </dd>
                                </div>
                            ))}
                        </dl>
                    )}

                    <button
                        type="button"
                        onClick={runPrediction}
                        disabled={!selectedSample || predicting}
                        className="rounded-lg bg-cyan-400 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {predicting ? "Analyzing…" : "Run detection"}
                    </button>

                    {error && (
                        <p role="alert" className="text-sm text-red-300">
                            {error}
                        </p>
                    )}
                </section>

                <div aria-live="polite">
                    {result && selectedSample && (
                        <section className="space-y-4 rounded-xl border border-slate-700 p-6">
                            <h2 className="text-lg font-medium">Prediction result</h2>

                            <p
                                className={`text-3xl font-bold ${result.prediction === "attack"
                                    ? "text-orange-300"
                                    : "text-emerald-300"
                                    }`}
                            >
                                {result.prediction.toUpperCase()}
                            </p>

                            <dl className="grid grid-cols-2 gap-4">
                                <div>
                                    <dt className="text-sm text-slate-400">
                                        Estimated attack probability
                                    </dt>
                                    <dd className="mt-1 text-xl">
                                        {(result.attack_probability * 100).toFixed(2)}%
                                    </dd>
                                </div>
                                <div>
                                    <dt className="text-sm text-slate-400">
                                        Decision threshold
                                    </dt>
                                    <dd className="mt-1 text-xl">
                                        {(result.threshold * 100).toFixed(0)}%
                                    </dd>
                                </div>
                            </dl>

                            <p className="text-sm text-slate-300">
                                Dataset label: {selectedSample.actual_label}
                                {" · "}
                                {result.prediction === selectedSample.actual_label
                                    ? "Prediction matches the dataset label."
                                    : "Prediction differs from the dataset label."}
                            </p>
                        </section>
                    )}
                </div>

                <footer className="text-sm leading-6 text-slate-400">
                    Benchmark demonstration using recorded flows. On the official test
                    set, the model detected 98.27% of attacks and flagged 25.53% of normal
                    flows as attacks.
                </footer>
            </div>
        </main>
    );
}