"use client";

import { useState } from "react";

type BatchResult = {
    summary: {
        total: number;
        normal: number;
        attack: number;
    };
    results: {
        row: number;
        prediction: "normal" | "attack";
        attack_probability: number;
        threshold: number;
    }[];
};

export default function BatchUpload({ apiUrl }: { apiUrl: string }) {
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<BatchResult | null>(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");

    async function runBatchPrediction() {
        if (!file || uploading) return;

        setError("");
        setResult(null);

        if (file.size > 2 * 1024 * 1024) {
            setError("Choose a CSV no larger than 2 MiB.");
            return;
        }

        setUploading(true);

        try {
            // The field name must match the API's "file" parameter.
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(`${apiUrl}/predict-batch`, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : `Batch prediction failed (${response.status}).`
                );
            }

            setResult(data as BatchResult);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Could not process the CSV."
            );
        } finally {
            setUploading(false);
        }
    }

    return (
        <section
            aria-labelledby="batch-heading"
            className="space-y-5 rounded-xl border border-slate-700 p-6"
        >
            <h2 id="batch-heading" className="text-xl font-semibold">
                Analyze a CSV
            </h2>

            <p id="csv-help" className="text-sm leading-6 text-slate-400">
                Upload a UTF-8 CSV containing the 41 input features, with one
                network flow per row. Maximum: 1,000 flows and 2 MiB.
                Exclude identifiers and dataset labels.
            </p>

            <label htmlFor="csv-file" className="block text-sm font-medium">
                Network-flow CSV
            </label>

            <input
                id="csv-file"
                type="file"
                accept=".csv"
                aria-describedby="csv-help"
                disabled={uploading}
                onChange={(event) => {
                    setFile(event.target.files?.[0] ?? null);
                    // Results always belong to the currently selected file.
                    setResult(null);
                    setError("");
                }}
                className="block w-full text-sm text-slate-300 file:mr-4 file:rounded-lg file:border-0 file:bg-slate-800 file:px-4 file:py-2 file:text-slate-100"
            />

            <button
                type="button"
                onClick={runBatchPrediction}
                disabled={!file || uploading}
                className="rounded-lg bg-cyan-400 px-5 py-3 font-semibold text-slate-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
                {uploading ? "Analyzing CSV…" : "Analyze CSV"}
            </button>

            {error && (
                <p role="alert" className="text-sm text-red-300">
                    {error}
                </p>
            )}

            <div role="status">
                {result && (
                    <p>
                        Total: <strong>{result.summary.total}</strong>
                        {" · "}Predicted normal: <strong>{result.summary.normal}</strong>
                        {" · "}Predicted attack: <strong>{result.summary.attack}</strong>
                    </p>
                )}
            </div>

            {result && (
                <div
                    tabIndex={0}
                    role="region"
                    aria-label="Scrollable batch predictions"
                    className="max-h-96 overflow-auto rounded-lg border border-slate-700"
                >
                    <table className="w-full text-left text-sm">
                        <caption className="p-3 text-left text-slate-400">
                            Row numbers exclude the CSV header.
                        </caption>
                        <thead className="bg-slate-800">
                            <tr>
                                <th scope="col" className="p-3">Row</th>
                                <th scope="col" className="p-3">Prediction</th>
                                <th scope="col" className="p-3">
                                    Estimated attack probability
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {result.results.map((item) => (
                                <tr key={item.row} className="border-t border-slate-800">
                                    <td className="p-3">{item.row}</td>
                                    <td
                                        className={`p-3 font-medium ${item.prediction === "attack"
                                            ? "text-orange-300"
                                            : "text-emerald-300"
                                            }`}
                                    >
                                        {item.prediction}
                                    </td>
                                    <td className="p-3">
                                        {(item.attack_probability * 100).toFixed(2)}%
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </section>
    );
}