class ExecutionRingBuffer {
  constructor(capacity = 2000) {
    this.capacity = capacity;
    this.buffer = new Array(capacity);
    this.head = 0;
    this.size = 0;
  }

  push(item) {
    const overwritten = this.size === this.capacity ? this.buffer[this.head] : null;

    this.buffer[this.head] = item;
    this.head = (this.head + 1) % this.capacity;
    this.size = Math.min(this.size + 1, this.capacity);

    return overwritten;
  }

  values() {
    const out = [];
    const start = (this.head - this.size + this.capacity) % this.capacity;
    for (let i = 0; i < this.size; i++) {
      out.push(this.buffer[(start + i) % this.capacity]);
    }
    return out;
  }

  clear() {
    this.buffer.fill(undefined);
    this.head = 0;
    this.size = 0;
  }
}

module.exports = { ExecutionRingBuffer };

