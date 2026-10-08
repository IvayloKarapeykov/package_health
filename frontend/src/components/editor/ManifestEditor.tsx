import { defaultKeymap, history, historyKeymap } from "@codemirror/commands"
import { bracketMatching, foldGutter, foldKeymap, indentOnInput } from "@codemirror/language"
import { Compartment, EditorState } from "@codemirror/state"
import {
  drawSelection,
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
  placeholder,
} from "@codemirror/view"
import { FileCode2 } from "lucide-react"
import { useDeferredValue, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react"

import { loadLanguage } from "@/components/editor/languages"
import { editorTheme } from "@/components/editor/theme"
import { ECOSYSTEM_BY_ID } from "@/lib/ecosystems"
import { detectManifestFormat } from "@/lib/manifestFormat"

export interface ManifestEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  ariaLabel: string
}

export default function ManifestEditor({ value, onChange, placeholder: hint = "", ariaLabel }: ManifestEditorProps) {
  const hostRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const languageRef = useRef(new Compartment())
  // The last text the editor itself reported, to tell typing apart from outside changes (e.g. an example).
  const emittedRef = useRef(value)
  const onChangeRef = useRef(onChange)
  useLayoutEffect(() => {
    onChangeRef.current = onChange
  })

  const [lines, setLines] = useState(() => countLines(value))
  // Detection may lag a keystroke behind while typing; it only drives highlighting and the tab.
  const deferredValue = useDeferredValue(value)
  const format = useMemo(() => detectManifestFormat(deferredValue), [deferredValue])

  // Create the editor once; React only feeds it outside changes from then on.
  useEffect(() => {
    const view = new EditorView({
      parent: hostRef.current!,
      state: EditorState.create({
        doc: emittedRef.current,
        extensions: [
          lineNumbers(),
          foldGutter(),
          highlightActiveLine(),
          highlightActiveLineGutter(),
          drawSelection(),
          history(),
          indentOnInput(),
          bracketMatching(),
          keymap.of([...defaultKeymap, ...historyKeymap, ...foldKeymap]),
          placeholder(hint),
          EditorView.contentAttributes.of({ "aria-label": ariaLabel, spellcheck: "false" }),
          editorTheme,
          languageRef.current.of([]),
          EditorView.updateListener.of((update) => {
            if (!update.docChanged) return
            const text = update.state.doc.toString()
            emittedRef.current = text
            setLines(update.state.doc.lines)
            onChangeRef.current(text)
          }),
        ],
      }),
    })
    viewRef.current = view
    return () => {
      view.destroy()
      viewRef.current = null
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Outside change (loading an example, clearing): replace the document.
  useEffect(() => {
    const view = viewRef.current
    if (!view || value === emittedRef.current) return
    emittedRef.current = value
    view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } })
  }, [value])

  // Swap the highlighter when the detected format changes; languages load on first use.
  const syntax = format?.syntax
  useEffect(() => {
    const view = viewRef.current
    if (!view) return
    if (!syntax) {
      view.dispatch({ effects: languageRef.current.reconfigure([]) })
      return
    }
    let cancelled = false
    void loadLanguage(syntax).then((language) => {
      if (!cancelled) viewRef.current?.dispatch({ effects: languageRef.current.reconfigure(language) })
    })
    return () => {
      cancelled = true
    }
  }, [syntax])

  return (
    <div className="glass-inset overflow-hidden rounded-xl">
      <EditorTab name={format?.name} registry={format ? ECOSYSTEM_BY_ID[format.ecosystem].label : undefined} lines={lines} />
      <div ref={hostRef} />
    </div>
  )
}

function EditorTab({ name, registry, lines }: { name?: string; registry?: string; lines: number }) {
  return (
    <div className="flex h-9 items-center gap-2 border-b border-border/60 px-3 text-xs">
      <FileCode2 className="size-3.5 shrink-0 text-brand-blue" aria-hidden />
      <span className={name ? "font-mono text-foreground/85" : "font-mono text-muted-foreground"}>
        {name ?? "untitled"}
      </span>
      {registry && (
        <span className="glass-inset rounded-full px-2 py-px text-[10px] font-medium text-muted-foreground">
          {registry}
        </span>
      )}
      <span className="ml-auto font-mono text-muted-foreground tabular-nums">
        {lines} line{lines === 1 ? "" : "s"}
      </span>
    </div>
  )
}

function countLines(text: string): number {
  let count = 1
  for (let i = text.indexOf("\n"); i !== -1; i = text.indexOf("\n", i + 1)) count++
  return count
}
