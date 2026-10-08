
import { StreamLanguage, type StreamParser } from "@codemirror/language"
import type { Extension } from "@codemirror/state"

import type { Syntax } from "@/lib/manifestFormat"

const LOADERS: Record<Syntax, () => Promise<Extension>> = {
  json: () => import("@codemirror/lang-json").then((m) => m.json()),
  xml: () => import("@codemirror/lang-xml").then((m) => m.xml()),
  yaml: () => import("@codemirror/lang-yaml").then((m) => m.yaml()),
  toml: () => import("@codemirror/legacy-modes/mode/toml").then((m) => StreamLanguage.define(m.toml)),
  ruby: () => import("@codemirror/legacy-modes/mode/ruby").then((m) => StreamLanguage.define(m.ruby)),
  groovy: () => import("@codemirror/legacy-modes/mode/groovy").then((m) => StreamLanguage.define(m.groovy)),
  kotlin: () => import("@codemirror/legacy-modes/mode/clike").then((m) => StreamLanguage.define(m.kotlin)),
  gomod: async () => StreamLanguage.define(goMod),
  requirements: async () => StreamLanguage.define(requirements),
}

const loaded = new Map<Syntax, Promise<Extension>>()

export function loadLanguage(syntax: Syntax): Promise<Extension> {
  let language = loaded.get(syntax)
  if (!language) {
    language = LOADERS[syntax]()
    loaded.set(syntax, language)
  }
  return language
}

/** requirements.txt: `name[extras] >= 1.2 ; marker  # comment`, plus `-r file` / `--index-url` options. */
const requirements: StreamParser<{ seenName: boolean }> = {
  name: "requirements",
  startState: () => ({ seenName: false }),
  token(stream, state) {
    if (stream.sol()) state.seenName = false
    if (stream.eatSpace()) return null
    if (stream.match(/^#.*/)) return "comment"
    if (stream.match(/^;.*/)) return "meta"
    if (stream.sol() && stream.match(/^--?[\w-]+/)) return "keyword"
    if (stream.match(/^[a-z][\w+.-]*:\/\/\S+/i)) return "string"
    if (stream.match(/^(===|==|~=|!=|<=|>=|<|>|@)/)) return "operator"
    if (stream.match(/^\[[^\]]*\]/)) return "attribute"
    if (!state.seenName && stream.match(/^[A-Za-z0-9][\w.-]*/)) {
      state.seenName = true
      return "def"
    }
    if (stream.match(/^[\w.*+!-]+/)) return "number"
    stream.next()
    return "punctuation"
  },
}

/** go.mod: directives, module paths, versions and `// indirect` comments. */
const goMod: StreamParser<unknown> = {
  name: "go.mod",
  token(stream) {
    if (stream.eatSpace()) return null
    if (stream.match(/^\/\/.*/)) return "comment"
    if (stream.match(/^(module|go|toolchain|require|replace|exclude|retract|godebug)\b/)) return "keyword"
    if (stream.match(/^=>/)) return "operator"
    if (stream.match(/^v\d+\.\d+\.\d+[\w.+-]*/)) return "number"
    if (stream.match(/^\d+(\.\d+)+/)) return "number"
    if (stream.match(/^[()]/)) return "bracket"
    if (stream.match(/^[^\s()]+/)) return "def"
    stream.next()
    return null
  },
}
