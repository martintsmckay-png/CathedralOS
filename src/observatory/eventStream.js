export class ObservatoryStream {
    constructor() {
        this.listeners = new Map();
        this.events = [];
    }

    subscribe(type, callback) {
        if (!this.listeners.has(type)) {
            this.listeners.set(type, []);
        }

        this.listeners.get(type).push(callback);

        return () => {
            const current = this.listeners.get(type) || [];
            this.listeners.set(
                type,
                current.filter(cb => cb !== callback)
            );
        };
    }

    emit(event) {
        this.events.push(event);

        const callbacks = this.listeners.get(event.type) || [];

        callbacks.forEach(cb => {
            try {
                cb(event);
            } catch (err) {
                console.error(err);
            }
        });
    }

    getMetrics() {
        return {
            packets: this.events.length,
            channels: this.listeners.size
        };
    }
}

export const EventStream = new ObservatoryStream();
