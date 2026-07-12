// src/subsystems/chat-runtime/ai-character-chat-core.js

// 1. Dependency & Plugin Registration Core
export const loadDependencies = { import: 'ai-character-chat-dependencies-v1' };
export const aiTextPlugin = { import: 'ai-text-plugin' };
export const textToImagePlugin = { import: 'text-to-image-plugin' };
export const commentsPlugin = { import: 'comments-plugin' };
export const tabbedCommentsPlugin = { import: 'tabbed-comments-plugin-v1' };
export const uploadPlugin = { import: 'upload-plugin' }; 
export const superFetch = { import: 'super-fetch-plugin' }; 
export const fullscreenButtonPlugin = { import: 'fullscreen-button-plugin' };
export const combineEmojis = { import: 'combine-emojis-plugin' };
export const bugReport = { import: 'bug-report-plugin' };

// Named Character Storage Directory
export const urlNamedCharacters = {
  assistant: "assistant",
  psychologist: "615fdef95fa7e75cbbaf943dc44d72be.gz",
  "ai-adventure": "b33c6ff0c14f92e8095ca90765848485.gz",
  "coding-assistant": "570b3c67b8ed9ed8f83ef652be549b1c.gz",
  "story-writer": "76b20593b117ab083d746312df4df296.gz",
  "world-war-simulator": "e1cf5213432a7eb9e310ec269fe38672.gz",
  therapist: "5cdaa39f9aabc7424c3b2e1b780a1e29.gz"
};

// 2. Binary Compression & Share Links Subsystem
export const generateShareLinkForCharacter = async (json) => {
  if (!window.CompressionStream) {
    alert("Share links use a feature that's only available in modern browsers. Please upgrade your browser to the latest version to use this feature. If you're using Safari, switch to Chrome instead.");
    return;
  }
  
  let loadingModal = createLoadingModal("⏳ Generating share link...");
  let jsonString = JSON.stringify(json); 
  
  let urlHashData = encodeURIComponent(JSON.stringify(json)).replace(/[!'()*]/g, function(c) {
    return '%' + c.charCodeAt(0).toString(16);
  });
  console.log("shareUrl (hash version):", `https://perchance.org/${window.generatorName}#${urlHashData}`);
  
  let dataUrlJsonString = jsonString.replace(/#/g, "%23");
  let blob = await fetch("data:text/plain;charset=utf-8," + dataUrlJsonString).then(res => res.blob());
  
  let compressedBlob = await compressBlobWithGzip(blob);
  let { url, size, error } = await uploadPlugin(compressedBlob);
  
  if (error) {
    loadingModal.delete();
    alert(`Error: ${error}${error === "disallowed_content" ? ". If you believe this is incorrect, then you may need to edit the character description to explicitly state that the character is 18 or older, since the moderation system can make mistakes if there is ambiguity." : ""}`);
  } else {
    loadingModal.delete(); 
    let fileName = url.replace("https://user.uploads.dev/file/", "");
    let characterName = json.addCharacter.name.replace(/\s+/g, "_").replaceAll("~", "");
    let shareUrl = `https://perchance.org/${window.generatorName}?data=${characterName}~${fileName}`;
    console.log("shareUrl:", shareUrl);

    let colorScheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light";
    await window.prompt2({
      content: { type: "none", html: `<div style="margin-bottom:0.5rem; opacity:0.7; font-size:90%;">Here's a link to this character that you can share with others:</div><div style="display:flex; gap:0.5rem;"><input value="${shareUrl}" style="flex-grow:1; color-scheme:${colorScheme};"> <button onclick="navigator.clipboard.writeText(this.parentElement.querySelector('input').value); this.textContent='copied ✅'; setTimeout(() => { this.textContent='copy url'; }, 2000);">copy url</button> </div>` },
    }, { cancelButtonText: null, submitButtonText: "finished" });
  }
};

export const compressBlobWithGzip = async (blob) => {
  const cs = new CompressionStream('gzip');
  const compressedStream = blob.stream().pipeThrough(cs);
  let outputBlob = await new Response(compressedStream).blob();
  return new Blob([outputBlob], { type: "application/gzip" });
};

export const loadDataFromUrlThatReferencesCloudStorageFile = async () => {
  if (!window.DecompressionStream) {
    alert("Character share links use a browser feature that's only available in modern browsers. Please upgrade your browser to the latest version to allow for loading data from character share links.");
    return null;
  }
  
  let loadingModal = createLoadingModal("Loading character data...");
  
  try {
    let searchParams = new URL(window.location.href).searchParams;
    let dataParamValue = searchParams.get("data");
    if (!dataParamValue) {
      if (searchParams.get("char") && urlNamedCharacters[searchParams.get("char")]) {
        dataParamValue = "foo~" + urlNamedCharacters[searchParams.get("char")];
      } else {
        throw new Error("Invalid share URL.");
      }
    }
    let fileName = dataParamValue.split("~").slice(-1)[0];
    let fileUrl = "https://user.uploads.dev/file/" + fileName;

    let blob = await fetch(fileUrl, { signal: AbortSignal.timeout ? AbortSignal.timeout(15000) : null }).then(res => res.ok ? res.blob() : null).catch(console.error);
    if (!blob) {
      loadingModal.delete();
      await confirmAsync(`It seems you've tried to load a character share URL, but the file specified by the URL does not exist. If you believe it should exist, you can ask for help on the community forum, or check if the file has been quarantined:\n\nperchance.org/quarantined-files`, { hideCancel: true });
      return null;
    }
    let text;
    if (fileUrl.endsWith(".gz")) {
      let decompressedBlob = await decompressBlobWithGzip(blob);
      text = await decompressedBlob.text();
    } else {
      throw new Error("Invalid share URL.");
    }
    let data = JSON.parse(text);
    loadingModal.delete();
    return data;
  } catch (e) {
    alert(`Failed to load chat data: ${e.message}`);
    console.error(e);
  }
  
  loadingModal.delete();
  return null;
};

export const decompressBlobWithGzip = async (blob) => {
  const ds = new DecompressionStream("gzip");
  const decompressedStream = blob.stream().pipeThrough(ds);
  return await new Response(decompressedStream).blob();
};

// 3. Isolated Sandboxed Script Evaluation
export const evaluatePerchanceTextInSandbox = async (text, opts) => {
  if (!opts) opts = {};
  let iframe = document.querySelector('#perchanceCodeEvaluationSandboxIframe');
  if (!iframe) {
    iframe = document.createElement("iframe");
    iframe.src = "https://7deabe31ae18ea5ed27c5f71b9633999.perchance.org/ai-character-chat-sandboxed-executor";
    iframe.id = "perchanceCodeEvaluationSandboxIframe";
    iframe.sandbox = "allow-scripts allow-same-origin";
    iframe.style.cssText = "position:fixed; width:1px; height:1px; opacity:0.01; top:-10px; right:-10px; pointer-events:none; border:0; outline:0; user-select:none;";
    document.body.append(iframe);
    iframe._resolvers = {};
    let iframeLoadResolver;
    let iframeLoadPromise = new Promise(r => iframeLoadResolver = r);
    window.addEventListener('message', (event) => {
      if (event.origin === 'https://7deabe31ae18ea5ed27c5f71b9633999.perchance.org') {
        if (event.data.finishedLoading) {
          iframeLoadResolver();
          return;
        }
        const { requestId, text } = event.data;
        if (iframe._resolvers[requestId]) {
          iframe._resolvers[requestId](text);
          delete iframe._resolvers[requestId];
        }
      }
    });
    await iframeLoadPromise;
  }
  const requestId = Math.random().toString();
  return new Promise((resolve, reject) => {
    iframe._resolvers[requestId] = resolve;
    if (opts.timeout) {
      setTimeout(() => {
        if (iframe._resolvers[requestId]) reject("Sandbox did not respond in time.");
      }, opts.timeout);
    }
    iframe.contentWindow.postMessage({ text, requestId }, 'https://7deabe31ae18ea5ed27c5f71b9633999.perchance.org');
  });
};

// 4. Hierarchical Summary Context Optimization Engine
export const getMessageObjsWithoutSummarizedOnes = (messages, opts) => {
  if (!opts) opts = {};
  messages = messages.slice(0);
  const minimumMessageLevel = opts.minimumMessageLevel || 0;
  
  let messageObjsWithoutSummarizedOnes = [];
  let highestLevelSeen = 0;
  
  while (messages.length > 0) {
    let m = messages.pop();
    let level = m.summariesEndingHere ? Math.max(...Object.keys(m.summariesEndingHere).map(n => Number(n))) : 0;
    if (level < minimumMessageLevel) continue;
    if (level >= highestLevelSeen) {
      messageObjsWithoutSummarizedOnes.unshift(m);
      highestLevelSeen = level;
    }
  }
  return messageObjsWithoutSummarizedOnes;
};

export const injectHierarchicalSummariesAndComputeNextSummariesInBackgroundIfNeeded = async (threadId, opts) => {
  if (!window.__aiHierarchicalSummaryStuff) window.__aiHierarchicalSummaryStuff = {};
  if (!window.__aiHierarchicalSummaryStuff[threadId]) {
    window.__aiHierarchicalSummaryStuff[threadId] = {};
    window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject = [];
  }
  if (!opts) opts = {};
  
  let originalMessages = await db.messages.where({ threadId }).toArray();
  let idToOriginalMessage = originalMessages.reduce((a, v) => (a[v.id] = v, a), {});
  let preparedMessages = await prepareMessagesForBot({ messages: originalMessages });
  for (let m of preparedMessages) {
    let originalMessage = idToOriginalMessage[m.id];
    if (originalMessage.summariesEndingHere) m.summariesEndingHere = originalMessage.summariesEndingHere;
  }
  
  let thread = await db.threads.get(threadId);
  let threadCharacter = await db.characters.get(thread.characterId);
  let userName = thread.userCharacter.name ?? threadCharacter.userCharacter.name ?? (await getUserCharacterObj()).name;
  let characterName = thread.character.name ?? threadCharacter.name;
  let roleInstruction = threadCharacter.roleInstruction.replaceAll("{{char}}", characterName).replaceAll("{{user}}", userName);
  let extraContext = `In case it's useful here's a description of the **${characterName}** character: ` + roleInstruction.replace(/\n+/g, " ");
  
  let idToPreparedMessage = preparedMessages.reduce((a, v) => (a[v.id] = v, a), {});
  
  if (window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject.length > 0) {
    let messagesToUpdate = new Set();
    for (let { summarizedMessages, lastMessageSummarizedId, summary, memories, level } of window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject) {
      if (level <= 0) { console.error("summary level should be 1 or higher"); continue; }
      let lastSummarizedMessageText = summarizedMessages[summarizedMessages.length - 1];
      let lastMessageObjInSummary = idToPreparedMessage[lastMessageSummarizedId];
      if (!lastMessageObjInSummary) {
        console.error(`!lastMessageObjInSummary ????`, { preparedMessages, idToPreparedMessage, lastMessageSummarizedId });
        continue;
      }
      let expectedLastSummarizedText = level === 1 ? `${lastMessageObjInSummary.name}: ${lastMessageObjInSummary.content}` : lastMessageObjInSummary.summariesEndingHere[level - 1];
      if (expectedLastSummarizedText.trim() === lastSummarizedMessageText.trim()) {
        let m = lastMessageObjInSummary;
        if (!m.summariesEndingHere) m.summariesEndingHere = {};
        m.summariesEndingHere[level] = summary;
        if (memories) {
          if (!m.memoriesEndingHere) m.memoriesEndingHere = {};
          if (!m.memoriesEndingHere[level]) m.memoriesEndingHere[level] = [];
          m.memoriesEndingHere[level].push(...(memories || []).map(memText => ({ text: memText, embedding: null })));
        }
        messagesToUpdate.add(m);
      }
    }
    if (window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject.length >= 3) {
      for (let m of messagesToUpdate) {
        if (window.textEmbedderFunction) {
          if (m.memoriesEndingHere) {
            for (let level in m.memoriesEndingHere) {
              for (let memory of m.memoriesEndingHere[level]) {
                if (!memory.embedding) {
                  let [embedding] = await window.embedTexts({ textArr: [memory.text], modelName: thread.textEmbeddingModelName });
                  memory.embedding = embedding;
                }
              }
            }
          }
        }
        let updateObj = { summariesEndingHere: m.summariesEndingHere };
        if (window.textEmbedderFunction && m.memoriesEndingHere) updateObj.memoriesEndingHere = m.memoriesEndingHere;
        await db.messages.update(m.id, updateObj);
      }
      window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject = [];
    }
  }
  
  const { countTokens, idealMaxContextTokens } = root.aiTextPlugin({ getMetaObject: true });
  let tokenCountToIdeallyStayUnder = idealMaxContextTokens - 800;
  
  const numCharsToSummarizeAtATime = 1500;
  const messageTextWithSummaryReplacements = getMessageObjsWithoutSummarizedOnes(preparedMessages).map(m => {
    let level = m.summariesEndingHere ? Math.max(...Object.keys(m.summariesEndingHere).map(n => Number(n))) : 0;
    return level === 0 ? m.content : m.summariesEndingHere[level];
  });
  
  let currentlyUsedContextLength = countTokens(messageTextWithSummaryReplacements.join("\n\n") + (opts.extraTextForAccurateTokenCount || ""));
  if (currentlyUsedContextLength < tokenCountToIdeallyStayUnder) {
    window.summarizationWasNeededLastCheck = false;
    return;
  } else {
    window.summarizationWasNeededLastCheck = true;
  }
      
  (async function() {
    if (window.__aiHierarchicalSummaryStuff[threadId].alreadyDoingSummary) return;
    try {
      window.__aiHierarchicalSummaryStuff[threadId].alreadyDoingSummary = true;
      const allMessageObjs = [];
      let i = 0;
      for (let m of preparedMessages) {
        allMessageObjs.push({
          text: `${m.name}: ${m.content}`,
          index: i++,
          messageId: m.id,
          level: 0,
        });
        let summaryEntries = Object.entries(m.summariesEndingHere || {}).sort((a, b) => Number(a[0]) - Number(b[0]));
        for (let [level, summary] of summaryEntries) {
          level = Number(level);
          allMessageObjs.push({ text: summary, index: i++, messageId: m.id, level });
        }
      }
      
      let summaryLevelToMessageBlocks = new Map();
      let summaryLevelBeingProcessed = 1;
      while (1) {
        const thisLevelAndPreviousLevelMessageObjs = allMessageObjs.filter(m => m.level === summaryLevelBeingProcessed || m.level === summaryLevelBeingProcessed - 1);
        if (thisLevelAndPreviousLevelMessageObjs.length === 0) break;
        
        const blocks = [];
        let currentBlock = [];
        currentBlock.messageData = [];
        for (let m of thisLevelAndPreviousLevelMessageObjs) {
          currentBlock.push(m.text);
          currentBlock.messageData.push(m);
          if (m.level === summaryLevelBeingProcessed) {
            blocks.push(currentBlock);
            currentBlock = [];
            currentBlock.messageData = [];
          }
        }
        blocks.push(currentBlock);
        summaryLevelToMessageBlocks.set(summaryLevelBeingProcessed, blocks);
        summaryLevelBeingProcessed++;
      }
      
      const summaryLevelBlockEntries = [...summaryLevelToMessageBlocks.entries()].sort((a, b) => a[0] - b[0]);
      for (let [summaryLevel, blocks] of summaryLevelBlockEntries) {
        let messagesToSummarizeFromFinalBlock = blocks[blocks.length - 1];
        let numCharsInFinalBlock = messagesToSummarizeFromFinalBlock.reduce((a, v) => a + v.length, 0);
        if (numCharsInFinalBlock < numCharsToSummarizeAtATime) continue;
      
        while (1) {
          if (messagesToSummarizeFromFinalBlock.length <= 1) break;
          let numChars = messagesToSummarizeFromFinalBlock.reduce((a, v) => a + v.length, 0);
          if (numChars < numCharsToSummarizeAtATime) break;
          
          if (numChars > numCharsToSummarizeAtATime * 10) {
            let halfOfMessagesCount = Math.floor(messagesToSummarizeFromFinalBlock.length / 2);
            for (let j = 0; j < halfOfMessagesCount; j++) {
              messagesToSummarizeFromFinalBlock.pop();
              messagesToSummarizeFromFinalBlock.messageData.pop();
            }
          } else {
            messagesToSummarizeFromFinalBlock.pop();
            messagesToSummarizeFromFinalBlock.messageData.pop();
          }
        }

        if (messagesToSummarizeFromFinalBlock.length === 0) continue;

        let lastMessageSummarizedData = messagesToSummarizeFromFinalBlock.messageData[messagesToSummarizeFromFinalBlock.length - 1];
        let lastMessageSummarizedId = lastMessageSummarizedData.messageId;
        
        let exampleBlocksForStartWith = blocks.slice(-3, -1);
        let exampleBlockSummaries = exampleBlocksForStartWith.map(b => b[b.length - 1]);
        
        let summariesAtThisLevelAndAbove = getMessageObjsWithoutSummarizedOnes(preparedMessages, { minimumMessageLevel: summaryLevel }).map(m => {
          let level = m.summariesEndingHere ? Math.max(...Object.keys(m.summariesEndingHere).map(n => Number(n))) : 0;
          return level === 0 ? m.content : m.summariesEndingHere[level];
        });
        
        let instructionSummaries = JSON.parse(JSON.stringify(summariesAtThisLevelAndAbove));
        while (1) {
          if (instructionSummaries.length === 0) break;
          if (exampleBlockSummaries.includes(instructionSummaries[instructionSummaries.length - 1])) {
            instructionSummaries.pop();
            continue;
          }
          break;
        }
        
        let startWithBlocks = exampleBlocksForStartWith.map((block) => ({ messages: block.slice(0, -1), summary: block.slice(-1)[0] }));
        startWithBlocks.push({ messages: messagesToSummarizeFromFinalBlock, summary: "" });
        
        let startWith = startWithBlocks.map(({ messages, summary }, blockI) => {
          let letterLabel = blockI === 0 ? "[A]" : blockI === 1 ? "[B]" : "[C]";
          let messagesText = messages.map((message, mi) => {
            message = message.replace(/\n/g, " ").trim();
            return `${summaryLevel === 1 ? `(${mi + 1}) ` : ""}${message}`;
          }).join(" ");
          summary = summary.replace(/\n/g, " ").trim();
          return `>>> FULL TEXT of ${letterLabel}: ${messagesText}\n>>> SUMMARY of ${letterLabel}: ${summary}`;
        }).join("\n---\n").trim();
        
        let sharedContextPrefixText = [
          `Below is${extraContext ? ` some context, plus` : ""} a summary of some events. You must use this information to complete the '@@@ TASK' specified at the bottom of this instruction.`,
          `${extraContext ? `\n# Potentially Useful Context (may or may not be relevant):\n${extraContext}\n` : ""}`,
          `# Summary of Previous Events:`,
        ].join("\n").trim();

        const summaryTaskPrompt = `@@@ TASK: Your task is to generate some text and then a 'SUMMARY' of that text, and then do that a few more times...`.trim();

        startWith = startWith.slice(0, -1) + " (full, natural, readable sentences with correct grammar):";

        let promptOptions = {
          instruction: [sharedContextPrefixText, (instructionSummaries.length > 0 ? instructionSummaries : ["(None.)"]).join("\n"), ``, summaryTaskPrompt].join("\n").trim(),
          startWith,
          stopSequences: ["\n\n", "\n---", "\n>>> FULL TEXT", "FULL TEXT"],
        };
        
        let data = await aiTextPlugin(promptOptions);
        if (data.stopReason === "error") continue;

        let summary = data.generatedText.trim().replace(/\n+/g, " ").trim().replace(/---$/, "").replace(">>> FULL TEXT", "").replace("FULL TEXT", "").trim();
        if (!summary.trim() || (instructionSummaries[instructionSummaries.length - 1] || "").trim() === summary.trim()) continue;

        if (summary.split(summary.slice(-30)).length > 5) {
          let result = await aiTextPlugin({
            instruction: [`Does the following story summary snippet include repetition?...`, summary].join("\n"),
            stopSequences: ["</fixed_story_summary_snippet>"],
          });
          if (result.stopReason === "error") continue;
          let fixedSummary = result.generatedText.match(/<fixed_story_summary_snippet>(.+)<\/fixed_story_summary_snippet>/s)?.[1].trim();
          if (fixedSummary) summary = fixedSummary;
        }
        
        let messagesSummarizedText = messagesToSummarizeFromFinalBlock.map((message, i) => message.replace(/\n/g, " ").trim()).join(" ");
        
        let memories;
        if (summaryLevel === 1 && opts.shouldCreateMemories) {  
          const memoryTaskPrompt = `@@@ TASK: Your task condense the *NEW_TEXT* below into a series of up to 3 lore/memory/fact entries...`.trim();
          let data = await aiTextPlugin({
            instruction: [sharedContextPrefixText, (summariesAtThisLevelAndAbove.length > 0 ? summariesAtThisLevelAndAbove : ["(None.)"]).join("\n"), ``, memoryTaskPrompt].join("\n").trim(),
            startWith: `# Lore/memory entries from NEW_TEXT:\n1.`,
            stopSequences: ["\n4."],
          });
          if (data.stopReason === "error") continue;
          memories = ("1." + data.generatedText).trim().split("\n").map(l => l.trim()).filter(l => l && /^[0-9]\. .+/.test(l)).map(l => l.replace(/^[0-9]\. /, ""));
        }
        
        window.__aiHierarchicalSummaryStuff[threadId].summariesReadyToInject.push({ summarizedMessages: messagesToSummarizeFromFinalBlock, lastMessageSummarizedId, summary, memories, level: summaryLevel });
      }
    } catch (e) {
      console.error(e);
    } // Removed nested duplicate loop segments during compilation optimization pass
    finally {
      window.__aiHierarchicalSummaryStuff[threadId].alreadyDoingSummary = false;
    }
  })();
};

export const confirmAsync = async (message, opts) => {
  if (!opts) opts = {};
  if (!message) message = "Are you sure?";
  return new Promise(resolve => {
    const overlay = Object.assign(document.createElement("div"), { tabIndex: 0 });
    overlay.style.cssText = `position:fixed;inset:0;z-index:99999999;display:grid;place-items:center;background-color:rgba(0,0,0,.65);font:16px/1.4 system-ui`;
    overlay.innerHTML = `<div style="text-align:left !important;max-width:min(97vw, 450px);padding:15px;border-radius:8px;background-color:light-dark(#fff,#222);color:light-dark(#000,#fff);box-shadow:0 2px 8px rgba(0,0,0,.2);">
      <p style="margin:0 0 20px;white-space:pre-wrap;">${message.replace(/[<>&]/g, m => ({ "<": "&lt;", "&": "&amp;", ">": "&gt;" }[m]))}</p>
      <div style="display:flex;justify-content:flex-end;gap:8px;">
        <button ${opts.hideCancel ? "hidden" : ""} style="padding:6px 16px;border:1px solid light-dark(#ccc,#555);border-radius:6px;background-color:light-dark(#f6f6f6,#333);color:inherit;cursor:pointer;">Cancel</button>
        <button autofocus style="padding:6px 16px;border:none;border-radius:6px;background-color:light-dark(#1677ff,#2b87ff);color:#fff;cursor:pointer;">Okay</button>
      </div>
    </div>`;
    const [cancelBtn, okBtn] = overlay.querySelectorAll("button");
    const finish = val => { overlay.remove(); resolve(val); };
    cancelBtn.onclick = () => finish(false);
    okBtn.onclick = () => finish(true);
    overlay.onkeydown = e => {
      if (e.key === "Escape") finish(false);
      else if (e.key === "Enter") finish(true);
    };
    document.body.append(overlay);
    overlay.focus({ preventScroll: true });
  });
};

export const commentChannels = ["chat", "chill", "rp", "spam", "vent", "share"];

export const defaultCommentOptions = {
  width: "100%",
  height: "100%",
  commentPlaceholderText: "Add a friendly comment...",
  fullscreenButtonStyle: "",
  customEmojis: { import: 'huge-emoji-list' },
  bannedUsers: ["300cb70b21f2d67b1496", "c3fc848cb123db2793f8", "403b16b3422020848cd0"]
};

