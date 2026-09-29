/** No bytes (not even keep-alive comments) arrived within the idle timeout. */
export class StreamIdleError extends Error {}

export interface ReadOptions {
  /** Give up when the stream is silent for this long; pair it with server-side pings. */
  idleTimeoutMs?: number
}

export interface ServerSentEvent {
  event: string
  data: string
}

/**
 * Parses a `text/event-stream` body. Unlike `EventSource`, this works with POST requests.
 */
export async function* readServerSentEvents(
  body: ReadableStream<Uint8Array>,
  { idleTimeoutMs }: ReadOptions = {},
): AsyncGenerator<ServerSentEvent> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let pendingCarriageReturn = "" // a "\r" at a chunk edge may be the first half of "\r\n"

  try {
    while (true) {
      let chunk: ReadableStreamReadResult<Uint8Array>
      try {
        chunk = await readWithTimeout(reader, idleTimeoutMs)
      } catch (error) {
        if (error instanceof StreamIdleError) await reader.cancel().catch(() => undefined)
        throw error
      }
      const { value, done } = chunk
      if (done) break
      let text = pendingCarriageReturn + decoder.decode(value, { stream: true })
      pendingCarriageReturn = text.endsWith("\r") ? "\r" : ""
      if (pendingCarriageReturn) text = text.slice(0, -1)
      buffer += text.replace(/\r\n?/g, "\n")

      let boundary = buffer.indexOf("\n\n")
      while (boundary !== -1) {
        const event = parseEventBlock(buffer.slice(0, boundary))
        buffer = buffer.slice(boundary + 2)
        if (event) yield event
        boundary = buffer.indexOf("\n\n")
      }
    }
  } finally {
    reader.releaseLock()
  }
}

function readWithTimeout(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  timeoutMs: number | undefined,
): Promise<ReadableStreamReadResult<Uint8Array>> {
  if (!timeoutMs) return reader.read()
  let timer: ReturnType<typeof setTimeout> | undefined
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new StreamIdleError(`No data for ${timeoutMs} ms`)), timeoutMs)
  })
  return Promise.race([reader.read(), timeout]).finally(() => clearTimeout(timer))
}

function parseEventBlock(block: string): ServerSentEvent | null {
  let event = "message"
  const data: string[] = []

  for (const line of block.split("\n")) {
    if (!line || line.startsWith(":")) continue // comments carry keep-alive pings
    const separator = line.indexOf(":")
    const field = separator === -1 ? line : line.slice(0, separator)
    const value = separator === -1 ? "" : line.slice(separator + 1).replace(/^ /, "")
    if (field === "event") event = value
    else if (field === "data") data.push(value)
  }

  return data.length ? { event, data: data.join("\n") } : null
}
