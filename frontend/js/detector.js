/* Teachable Machine TensorFlow.js inference. Requires model.json, weights.bin, metadata.json. */
export class NexusDetector {
  constructor() { this.model = null; this.labels = []; this.loading = null; }
  async load() {
    if (this.model) return this;
    if (this.loading) return this.loading;
    this.loading = (async () => {
      if (!window.tf) throw new Error('TensorFlow.js no se cargó');
      const base = new URL('../models/teachable_machine/', import.meta.url);
      const metadata = await fetch(new URL('metadata.json', base));
      if (!metadata.ok) throw new Error('Falta metadata.json del modelo');
      this.labels = (await metadata.json()).labels;
      this.model = await window.tf.loadLayersModel(new URL('model.json', base).href);
      return this;
    })();
    try { return await this.loading; } finally { this.loading = null; }
  }
  async predict(source) {
    await this.load();
    const scores = window.tf.tidy(() => {
      const pixels = window.tf.browser.fromPixels(source).resizeBilinear([224,224]);
      const input = pixels.toFloat().div(127.5).sub(1).expandDims(0);
      const output = this.model.predict(input);
      return Array.from(output.dataSync());
    });
    return this.labels.map((label, i) => ({label, confidence: scores[i]}))
      .sort((a,b) => b.confidence - a.confidence);
  }
}
