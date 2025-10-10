import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/button";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";


const Schema = z.object({
  path: z.string().min(3, "Please paste a valid folder path"),
  relevance: z
    .string()
    .optional()
    .transform((v) => (v && v.trim() ? Number(v) : 3))
});

export default function HomePage() {
  const form = useForm({
    resolver: zodResolver(Schema),
    defaultValues: { path: "", relevance: "3" },
  });

  const [logs, setLogs] = useState([]);
  const [readme, setReadme] = useState("");
  const [outPath, setOutPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function onSubmit(values) {
    setLoading(true);
    setErr("");
    setLogs([]);
    setReadme("");
    setOutPath("");

    try {
      const res = await fetch("http://localhost:5000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: values.path,
          relevance: Number(values.relevance ?? 3),
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error(data.error || "Generation failed");
      }
      setLogs(data.logs || []);
      setReadme(data.readme || "");
      setOutPath(data.out_path || "");
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">README Generator (Local)</h1>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="path"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Project Folder Path</FormLabel>
                <FormControl>
                  <Input placeholder="e.g. C:\Users\you\project" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="relevance"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Relevance Threshold (default 3)</FormLabel>
                <FormControl>
                  <Input placeholder="3" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" disabled={loading}>
            {loading ? "Generating…" : "Generate README"}
          </Button>
        </form>
      </Form>

      {err && <p className="text-red-600 text-sm">❌ {err}</p>}

      {/* Logs */}
      {logs.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Logs</h2>
          <div className="rounded border bg-muted p-3 max-h-64 overflow-auto">
            <pre className="whitespace-pre-wrap text-sm">
              {logs.join("\n")}
            </pre>
          </div>
        </div>
      )}

      {/* README output */}
      {readme && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">
            README.md {outPath ? <span className="text-xs text-muted-foreground">({outPath})</span> : null}
          </h2>
          <div className="rounded border bg-background p-3 max-h-[60vh] overflow-auto">
            <pre className="whitespace-pre-wrap text-sm">{readme}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
