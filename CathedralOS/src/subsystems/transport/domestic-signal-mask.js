/**
 * CathedralOS Core Subsystem: DomesticSignalMask (v2.0)
 * Context: Alpha Base Signal Isolation Frame
 * Design Protocol: Reversible symmetric XOR array mask for domestic noise protection
 */

export class DomesticSignalMask {
    constructor(rootStream = null, options = {}) {
        this.rootStream = rootStream;
        this.mandibularPlating = options.mandibularPlating || false;
        this.maskKey = 0x42; // Reversible structural cipher byte
    }

    /**
     * Masks an outgoing raw byte packet using the fixed structural key
     */
    maskPacket(packet) {
        if (!packet || !packet.payload) {
            return { ...packet, payload: new Uint8Array() };
        }

        // Apply XOR transformations across the payload buffer
        const rawData = packet.payload instanceof Uint8Array 
            ? packet.payload 
            : new Uint8Array(packet.payload);

        const maskedData = rawData.map(byte => byte ^ this.maskKey);

        return {
            ...packet,
            payload: maskedData,
            masked: true
        };
    }

    /**
     * Decrypts an incoming masked byte array using the same reversible home-vibe key
     */
    decryptWithHomeVibe(data) {
        if (!data) return new Uint8Array();
        
        const dataBuffer = data instanceof Uint8Array 
            ? data 
            : new Uint8Array(data);

        // XOR is completely symmetric; applying 0x42 twice restores the original text bytes
        return dataBuffer.map(byte => byte ^ this.maskKey);
    }
}

