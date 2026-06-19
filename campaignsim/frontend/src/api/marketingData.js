/**
 * marketingData.js
 * Loads and aggregates the bundled marketing campaign CSV dataset.
 * Returns totals/averages for: spend, impressions, clicks, conversions, click-rate.
 *
 * Dataset source: synthetic marketing campaign data (open-licensed)
 * placed at: src/assets/data/marketing_dataset.csv
 */

/**
 * Parse a raw CSV string into an array of objects keyed by header names.
 * @param {string} text - raw CSV content
 * @returns {Array<Object>}
 */
function parseCSV(text) {
  const lines = text.trim().split('\n')
  if (lines.length < 2) return []

  const headers = lines[0].split(',').map(h => h.trim())
  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim())
    return headers.reduce((obj, header, i) => {
      obj[header] = values[i] ?? ''
      return obj
    }, {})
  })
}

/**
 * Fetch and parse the marketing dataset, then return aggregated metrics.
 * All numeric fields are case-insensitively matched so the CSV columns
 * can be: Impressions, impressions, IMPRESSIONS, etc.
 *
 * @returns {Promise<{
 *   totalSpend: number,
 *   totalImpressions: number,
 *   totalClicks: number,
 *   totalConversions: number,
 *   clickRate: number
 * } | null>}
 */
export async function getMarketingMetrics() {
  try {
    // Vite exposes files in /public or imported directly.
    // We use a relative URL so it works for both dev and production builds.
    const url = new URL('../assets/data/marketing_dataset.csv', import.meta.url).href
    const response = await fetch(url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const text = await response.text()
    const rows = parseCSV(text)

    if (rows.length === 0) return null

    // Normalise header lookup (case-insensitive)
    const key = (row, ...candidates) => {
      const rowKeys = Object.keys(row)
      for (const c of candidates) {
        const found = rowKeys.find(k => k.toLowerCase() === c.toLowerCase())
        if (found !== undefined) return parseFloat(row[found]) || 0
      }
      return 0
    }

    let totalSpend = 0
    let totalImpressions = 0
    let totalClicks = 0
    let totalConversions = 0

    rows.forEach(row => {
      totalSpend        += key(row, 'Spend', 'spend', 'Cost', 'cost')
      totalImpressions  += key(row, 'Impressions', 'impressions')
      totalClicks       += key(row, 'Clicks', 'clicks')
      totalConversions  += key(row, 'Conversions', 'conversions', 'Total_Conversion', 'Approved_Conversion')
    })

    const clickRate = totalImpressions > 0 ? totalClicks / totalImpressions : 0

    return {
      totalSpend: Math.round(totalSpend * 100) / 100,
      totalImpressions: Math.round(totalImpressions),
      totalClicks: Math.round(totalClicks),
      totalConversions: Math.round(totalConversions),
      clickRate: Math.round(clickRate * 10000) / 10000  // 4 decimal precision
    }
  } catch (err) {
    console.warn('[marketingData] Failed to load dataset:', err.message)
    return null
  }
}
