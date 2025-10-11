import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Spinner } from "@/components/ui/shadcn-io/spinner";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

const Schema = z.object({
  path: z.string().min(3, "Please paste a valid folder path"),
  relevance: z
    .string()
    .optional()
    .transform((v) => (v && v.trim() ? Number(v) : 3)),
});

export default function HomePage() {
  const spinner = () => (
    <div className="flex flex-col items-center justify-center space-y-3 py-6">
      <Spinner variant="infinite" className="w-10 h-10 text-emerald-800" />
      <p className="text-gray-500 text-sm font-medium animate-pulse">
        Generating Response...
      </p>
    </div>
  );
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
          relevance: Number(values.relevance),
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
    <div className="max-w-3xl mx-auto p-8 space-y-8 bg-gradient-to-b from-background to-muted/30 rounded-2xl shadow-lg border border-border/40 mt-10">
      {/* Spinner */}
      {loading && spinner()}

      {/* Title */}
      <h1 className="text-3xl font-extrabold tracking-tight text-center bg-gradient-to-r from-emerald-500 to-teal-400 bg-clip-text text-transparent">
        README Generator (Local)
      </h1>

      {/* Form */}
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="space-y-6 bg-card p-6 rounded-xl border border-border/50 shadow-sm hover:shadow-md transition-shadow"
        >
          <FormField
            control={form.control}
            name="path"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="font-semibold text-foreground">
                  Project Folder Path
                </FormLabel>
                <FormControl>
                  <Input
                    placeholder="e.g. C:\\Users\\you\\project"
                    {...field}
                    className="focus-visible:ring-emerald-500 transition-all"
                  />
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
                <FormLabel className="font-semibold text-foreground">
                  Relevance Threshold
                </FormLabel>

                <Select
                  onValueChange={field.onChange}
                  defaultValue={field.value}
                >
                  <FormControl>
                    <SelectTrigger className="focus-visible:ring-emerald-500 transition-all">
                      <SelectValue placeholder="Select a threshold" />
                    </SelectTrigger>
                  </FormControl>

                  <SelectContent>
                    <SelectItem value="2">
                      Balanced (some potential noise)
                    </SelectItem>
                    <SelectItem value="3">Recommended</SelectItem>
                  </SelectContent>
                </Select>

                <FormDescription className="text-sm text-muted-foreground">
                  Controls how selective the README generator is about which
                  files to include.
                  <br />
                  <span className="italic text-foreground">
                    {field.value === "2"
                      ? "A bit looser, more context."
                      : "Tight, higher-quality subset."}
                  </span>
                </FormDescription>

                <FormMessage />
              </FormItem>
            )}
          />

          <Button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.99]"
          >
            {!loading ? "🚀 Generate README" : "Generating response..."}
          </Button>
        </form>
      </Form>

      {/* Error message */}
      {err && (
        <p className="text-red-600 text-sm font-medium text-center">❌ {err}</p>
      )}

      {/* Logs */}
      {logs.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground">Logs</h2>
          <div className="rounded-lg border border-border/40 bg-muted/30 p-3 max-h-64 overflow-auto text-sm font-mono">
            <pre className="whitespace-pre-wrap">{logs.join("\n")}</pre>
          </div>
        </div>
      )}

      {/* README output */}
      {readme && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            README.md{" "}
            {outPath && (
              <span className="text-xs text-muted-foreground font-normal">
                ({outPath})
              </span>
            )}
          </h2>
          <div className="rounded-lg border border-border/40 bg-white/90 dark:bg-background p-4 max-h-[60vh] overflow-auto text-sm font-mono shadow-inner">
            <pre className="whitespace-pre-wrap">{readme}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
