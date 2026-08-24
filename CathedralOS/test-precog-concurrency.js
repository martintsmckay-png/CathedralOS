// test-precog-concurrency.js
import { PrecogEngine } from './src/subsystems/precog-runtime/precog-engine.js';
import { precogBus } from './src/subsystems/precog-runtime/core-bus.js';

console.log('⚙️ Initializing Precog Concurrency Live Bus Test...');

// 1. Instantiate the real engine with a custom logger
const testEngine = new PrecogEngine({
  bus: precogBus,
  historyLimit: 10,
  forkThreshold: 0.65,
  mergeThreshold: 0.70,
  onLedgerFragment: (logMessage, component) => {
    console.log(`📜 [${component}]: ${logMessage}`);
  }
});

// 2. Fire up the engine listeners
testEngine.start();

// 3. Setup a timed sequence to inject events into the live bus
console.log('\n📡 Injecting baseline stable event...');
precogBus.publish('anomaly', { severity: 'low', signalType: 'SYSTEM_OK' });

// Inject high-drift event to trigger the moonwalk fork split after 150ms
setTimeout(() => {
  console.log('\n💥 Injecting high-drift critical failure event...');
  precogBus.publish('anomaly', { severity: 'critical', signalType: 'BROWSER_CRASH' });
}, 150);

// Inject a stabilizing event to align predictions and force a consensus merge after 300ms
setTimeout(() => {
  console.log('\n🛡️ Injecting stabilizing event to trigger weighted consensus...');
  // Force the engine oracle to evaluate matching recovery trajectories
  precogBus.publish('anomaly', { severity: 'low', signalType: 'RECOVERY_SUCCESS' });
}, 300);

// 4. Inspect final channel state after the timeline plays out
setTimeout(() => {
  testEngine.stop();
  console.log('\n🛑 Simulation window complete.');
  
  console.log('\n--- Final Channel Registry State ---');
  for (const [id, channel] of testEngine.channels.entries()) {
    console.log(`Lane ID: [${id}] -> Status: [${channel.status}]`);
  }
  
  console.log('\n✅ Concurrency pipeline verification complete.');
  process.exit(0);
}, 500);

