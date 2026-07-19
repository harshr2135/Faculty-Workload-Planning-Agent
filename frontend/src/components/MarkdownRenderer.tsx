import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const markdownComponents: Components = {
  h1: ({ children }: ComponentPropsWithoutRef<"h1">) => (
    <h1 className="mt-2 mb-3 border-b border-slate-200 pb-2 text-2xl font-semibold text-slate-900">
      {children}
    </h1>
  ),
  h2: ({ children }: ComponentPropsWithoutRef<"h2">) => (
    <h2 className="mt-6 mb-2 border-b border-slate-100 pb-1 text-lg font-semibold text-slate-800">
      {children}
    </h2>
  ),
  h3: ({ children }: ComponentPropsWithoutRef<"h3">) => (
    <h3 className="mt-4 mb-2 text-base font-semibold text-slate-700">{children}</h3>
  ),
  p: ({ children }: ComponentPropsWithoutRef<"p">) => (
    <p className="my-2 text-sm leading-relaxed text-slate-700">{children}</p>
  ),
  ul: ({ children }: ComponentPropsWithoutRef<"ul">) => (
    <ul className="my-2 list-disc space-y-1 pl-5 text-sm text-slate-700">{children}</ul>
  ),
  ol: ({ children }: ComponentPropsWithoutRef<"ol">) => (
    <ol className="my-2 list-decimal space-y-1 pl-5 text-sm text-slate-700">{children}</ol>
  ),
  li: ({ children }: ComponentPropsWithoutRef<"li">) => (
    <li className="leading-relaxed">{children}</li>
  ),
  strong: ({ children }: ComponentPropsWithoutRef<"strong">) => (
    <strong className="font-semibold text-slate-900">{children}</strong>
  ),
  em: ({ children }: ComponentPropsWithoutRef<"em">) => (
    <em className="text-slate-600">{children}</em>
  ),
  hr: () => <hr className="my-6 border-slate-200" />,
  a: ({ children, href }: ComponentPropsWithoutRef<"a">) => (
    <a href={href} className="text-blue-600 underline hover:text-blue-800">
      {children}
    </a>
  ),
  table: ({ children }: ComponentPropsWithoutRef<"table">) => (
    <div className="my-3 overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }: ComponentPropsWithoutRef<"thead">) => (
    <thead className="bg-slate-100">{children}</thead>
  ),
  th: ({ children, style }: ComponentPropsWithoutRef<"th">) => (
    <th
      className="border-b border-slate-200 px-3 py-2 text-left font-semibold text-slate-700"
      style={style}
    >
      {children}
    </th>
  ),
  td: ({ children, style }: ComponentPropsWithoutRef<"td">) => (
    <td className="border-b border-slate-100 px-3 py-2 align-top text-slate-700" style={style}>
      {children}
    </td>
  ),
  tr: ({ children }: ComponentPropsWithoutRef<"tr">) => (
    <tr className="even:bg-slate-50/60">{children}</tr>
  ),
  code: ({ children }: ComponentPropsWithoutRef<"code">) => (
    <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-xs text-slate-800">
      {children}
    </code>
  ),
  blockquote: ({ children }: ComponentPropsWithoutRef<"blockquote">) => (
    <blockquote className="my-3 border-l-4 border-slate-200 pl-4 text-sm italic text-slate-600">
      {children}
    </blockquote>
  ),
};

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
