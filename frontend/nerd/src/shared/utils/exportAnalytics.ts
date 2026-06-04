export const exportCsv = <T extends object>(data: T[], filename: string): void => {
  if (!data.length) return
  const headers = Object.keys(data[0])
  const rows = data.map((row) =>
    headers.map((h) => JSON.stringify((row as Record<string, unknown>)[h] ?? "")).join(",")
  )
  const csv = [headers.join(","), ...rows].join("\n")
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = `${filename}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export const exportPng = (svgElement: SVGElement, filename: string): void => {
  const svgData = new XMLSerializer().serializeToString(svgElement)
  const { width, height } = svgElement.getBoundingClientRect()
  const canvas = document.createElement("canvas")
  canvas.width = width || 800
  canvas.height = height || 400
  const ctx = canvas.getContext("2d")
  if (!ctx) return
  const img = new Image()
  img.onload = () => {
    ctx.fillStyle = "#1a1a2e"
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(img, 0, 0)
    const a = document.createElement("a")
    a.href = canvas.toDataURL("image/png")
    a.download = `${filename}.png`
    a.click()
  }
  img.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgData)))}`
}

export const exportPdf = (containerRef: HTMLElement, title: string): void => {
  const iframe = document.createElement("iframe")
  iframe.style.cssText = "position:fixed;width:0;height:0;border:0;"
  document.body.appendChild(iframe)
  const doc = iframe.contentWindow?.document
  if (!doc) {
    document.body.removeChild(iframe)
    return
  }
  doc.open()
  doc.write(
    `<html><head><title>${title}</title><style>body{font-family:sans-serif;padding:16px}</style></head><body>${containerRef.innerHTML}</body></html>`
  )
  doc.close()
  iframe.contentWindow?.focus()
  iframe.contentWindow?.print()
  setTimeout(() => document.body.removeChild(iframe), 1000)
}
