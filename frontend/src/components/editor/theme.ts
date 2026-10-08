
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language"
import { EditorView } from "@codemirror/view"
import { tags as t } from "@lezer/highlight"

const highlight = HighlightStyle.define([
  { tag: [t.propertyName, t.definition(t.variableName), t.labelName], color: "var(--syntax-key)" },
  { tag: [t.string, t.special(t.string), t.attributeValue, t.url], color: "var(--syntax-string)" },
  { tag: [t.number, t.bool, t.null, t.atom], color: "var(--syntax-number)" },
  { tag: [t.keyword, t.operatorKeyword, t.modifier, t.meta], color: "var(--syntax-keyword)" },
  { tag: [t.tagName, t.typeName, t.className, t.heading], color: "var(--syntax-tag)", fontWeight: "500" },
  { tag: [t.attributeName], color: "var(--syntax-keyword)" },
  { tag: [t.comment, t.lineComment, t.blockComment], color: "var(--syntax-comment)", fontStyle: "italic" },
  { tag: [t.operator, t.punctuation, t.bracket, t.separator, t.angleBracket], color: "var(--syntax-punctuation)" },
])

const theme = EditorView.theme({
  "&": {
    backgroundColor: "transparent",
    color: "var(--foreground)",
    fontSize: "12px",
    minHeight: "14rem",
    maxHeight: "40vh",
  },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": {
    fontFamily: "var(--font-mono, ui-monospace, monospace)",
    lineHeight: "1.65",
    overflow: "auto",
    scrollbarWidth: "thin",
    scrollbarColor: "oklch(from var(--brand-blue) l c h / 0.4) transparent",
  },
  ".cm-content": { padding: "10px 0", caretColor: "var(--brand-blue)" },
  ".cm-line": { padding: "0 14px 0 10px" },
  ".cm-gutters": {
    backgroundColor: "transparent",
    color: "oklch(from var(--muted-foreground) l c h / 0.6)",
    border: "none",
    borderRight: "1px solid oklch(from var(--border) l c h / 0.6)",
  },
  ".cm-lineNumbers .cm-gutterElement": { padding: "0 8px 0 14px", minWidth: "2.5em" },
  ".cm-activeLine": { backgroundColor: "oklch(from var(--brand-cyan) l c h / 0.08)" },
  ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--brand-blue)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--brand-blue)", borderLeftWidth: "2px" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection":
    { backgroundColor: "oklch(from var(--brand-cyan) l c h / 0.28)" },
  ".cm-matchingBracket, &.cm-focused .cm-matchingBracket": {
    backgroundColor: "oklch(from var(--brand-cyan) l c h / 0.25)",
    outline: "none",
  },
  ".cm-foldGutter .cm-gutterElement": { padding: "0 4px", color: "var(--muted-foreground)" },
  ".cm-foldPlaceholder": {
    backgroundColor: "oklch(from var(--brand-cyan) l c h / 0.15)",
    border: "none",
    color: "var(--muted-foreground)",
    padding: "0 6px",
  },
  ".cm-placeholder": { color: "var(--muted-foreground)", whiteSpace: "pre-wrap" },
})

export const editorTheme = [theme, syntaxHighlighting(highlight)]
