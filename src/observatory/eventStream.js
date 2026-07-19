export class ObservatoryStream {
    constructor() {
        this.events = [];
        this.listeners = [];
    }

    emit(event) {
        this.events.push(event);

        this.listeners.forEach(
            listener => listener(event)
        );
    }

    subscribe(listener) {
        this.listeners.push(listener);
    }
}
