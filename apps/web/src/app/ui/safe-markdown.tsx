import { Fragment, type ReactNode } from "react";

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, index) => {
    if (part.startsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    return <Fragment key={index}>{part}</Fragment>;
  });
}

/** Restricted Markdown renderer. Raw HTML and model-provided links are never interpreted. */
export function SafeMarkdown({ content }: { content: string }) {
  return <div className="safe-markdown">{content.split("\n").filter(Boolean).map((line, index) => {
    if (/^#{1,3} /.test(line)) return <h4 key={index}>{inline(line.replace(/^#+ /, ""))}</h4>;
    if (/^[-*] /.test(line)) return <div className="markdown-bullet" key={index}>• <span>{inline(line.slice(2))}</span></div>;
    if (/^\d+\. /.test(line)) return <p key={index}>{inline(line)}</p>;
    return <p key={index}>{inline(line)}</p>;
  })}</div>;
}
