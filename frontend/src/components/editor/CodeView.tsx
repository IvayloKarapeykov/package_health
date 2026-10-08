import { Compartment, EditorState, Prec } from "@codemirror/state"
import { EditorView, lineNumbers } from "@codemirror/view"
import { useEffect, useRef } from "react"

import { type CodeLanguage, loadLanguage } from "@/components/editor/languages"
import { editorTheme } from "@/components/editor/theme"

export interface CodeViewProps {
  code: string
  /** Omit for plain text. */
  language?: CodeLanguage
  lineNumbers?: boolean
}

// The editor theme sizes an input box; a code block is as tall as its code.
const blockTheme = Prec.highest(
  EditorView.theme({
    "&": { minHeight: "0", maxHeight: "none" },
    ".cm-content": { padding: "12px 0" },
  }),
)

export default function CodeView({ code, language, lineNumbers: showLineNumbers = false }: CodeViewProps) {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const syntax = new Compartment()
    const view = new EditorView({
      parent: hostRef.current!,
      state: EditorState.create({
        doc: code,
        extensions: [
          showLineNumbers ? lineNumbers() : [],
          EditorState.readOnly.of(true),
          EditorView.editable.of(false),
          blockTheme,
          editorTheme,
          syntax.of([]),
        ],
      }),
    })
    let cancelled = false
    if (language) {
      void loadLanguage(language).then((extension) => {
        if (!cancelled) view.dispatch({ effects: syntax.reconfigure(extension) })
      })
    }
    return () => {
      cancelled = true
      view.destroy()
    }
  }, [code, language, showLineNumbers])

  return <div ref={hostRef} />
}
