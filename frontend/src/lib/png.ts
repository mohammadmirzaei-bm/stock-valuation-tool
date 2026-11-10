/**
 * PNG export for ECharts canvases (football field and portfolio charts).
 * `chart.getDataURL` returns a `data:` URL that we hand to the shared download
 * helper.
 */

import { triggerDownload } from "./csv";

export interface DataUrlProvider {
  getDataURL: (opts: { backgroundColor?: string; pixelRatio?: number }) => string;
}

export function exportChartPng(
  chart: DataUrlProvider,
  filename: string,
  backgroundColor = "#171E2E",
): void {
  const url = chart.getDataURL({ backgroundColor, pixelRatio: 2 });
  triggerDownload(url, filename);
}
