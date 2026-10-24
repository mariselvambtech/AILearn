<!-- converted from planning.docx -->

Yes, your local LLM setup using Hermes 3 is more than enough! In fact, it is the exact model your system is currently engineered to use.
Here is why Hermes 3 running locally via Ollama is the perfect (and default) brain for this hybrid automation architecture:
1. Superior Action Planning
Your system recently switched its default Ollama LLM brain from llama3.1 to hermes3. This architectural decision was made specifically because Hermes 3 possesses superior tool-calling and action planning capabilities, which are essential for autonomous web navigation.
2. Built-in Skill Synthesis (Method 2)
The SkillSynthesizer utility you use for parameterized playback is already hardwired to connect to your local hermes3 model. It successfully uses this model to analyze your recorded steps, target locators, and typed values to automatically detect literal inputs (like "blue") and convert them into dynamic parameter templates (like {{search_query}}).
3. Advanced Spatial Reasoning (Method 1)
When the bot is navigating freely or when standard DOM locators fail on a site like Flipkart, the system relies on Pattern 11 (Spatial LLM Routing). Hermes 3 is used to evaluate bounding boxes and surrounding context to mathematically compute the raw (x, y) coordinate clicks.
4. Privacy & Cost Benefits
The decision to use a local LLM rather than a cloud API (like OpenAI's GPT-4 or Anthropic's Claude) was intentional. By keeping Hermes 3 local, your automation:
Remains 100% private, meaning sensitive credentials (like your encrypted passwords or delivery addresses) never leave your machine.
Works completely offline.
Costs $0 per inference call, allowing the bot to think and retry actions endlessly without racking up API bills.
To ensure this hybrid flow works perfectly, you simply need to make sure your .env file has OLLAMA_MODEL=hermes3 set and that your Ollama server is running on port 11434.

Graph engineering in AI (specifically involving Knowledge Graphs and Graph Neural Networks) is one of the most powerful paradigms in modern agentic systems. Instead of forcing an AI to read flat, linear text (like a massive document), graph engineering structures data as Nodes (entities/concepts) and Edges (the relationships between them). This allows the AI to "walk" the relationships and reason spatially and logically.
The most exciting part? You are actually already using Graph Engineering in this project!
Here is how you are currently using it, and exactly how you can expand it to power your hybrid Flipkart agent:
1. How You Are ALREADY Using Graph Engineering
You are currently using an Abstract Syntax Tree (AST) Knowledge Graph to manage your AI's context window.
The Problem: Your local_webai_server_guided.py file is massive (1,600+ lines). If you feed that whole file to Hermes 3, it will forget things (the "lost in the middle" problem).
The Graph Solution: You use the graphify tool to parse your entire Python codebase into a Knowledge Graph (graph.json) that maps 1,654 nodes and 2,446 edges.
The AI Implementation: Following Rule 8 (The Context Diet), your AI agent queries this graph to find exactly which functions connect to others without reading the whole file. This is pure Graph Retrieval-Augmented Generation (Graph RAG)!
2. How to Use Graph Engineering for the Web DOM
Right now, your AI brain uses Crawl4AI to flatten the Flipkart HTML code into a linear Markdown string. You can upgrade this using Graph Engineering to supercharge Pattern 11 (Spatial Reasoning):
DOM-to-Graph: Instead of a text string, represent the Flipkart webpage as a graph.
Nodes & Edges: A text box is a Node. The "Search" button is a Node. The Edge connecting them is a spatial relationship: [Search Button] --(is located right of)--> [Text Box].
Why it helps: When Hermes 3 needs to click "Add to Cart", it doesn't need to guess locators. It simply traverses the graph to find the "Add to Cart" node that is spatially connected to the "Red Shirt" image node.
3. How to Use a Knowledge Graph for Intent Routing (The Semantic Router)
To achieve the exact hybrid flow we discussed (where the bot knows when to use a recorded skill vs. autonomous browsing), you can build an Intent Graph.
Instead of standard database matching, map your automations as a Knowledge Graph.
The Graph Structure: [User Intent: Purchase]  [Website: Flipkart]  [Required Skill: Search Navigation]  [Missing Action: Checkout].
How the AI uses it: When you say "Buy a red shirt on Flipkart", Hermes 3 queries the graph. The graph tells the AI: "We have a skill for searching Flipkart, but the path to the 'Checkout' node is empty." This mathematically proves to the AI that it needs to run Method 2 (the recording) first, and then seamlessly switch to Method 1 (autonomous clicking) to bridge the missing edge to the checkout node.
4. Graph RAG for Error Recovery
If your 13-locator fallback engine fails, the AI can query an Error Graph:
[Error: Element Not Visible]  [Resolved By: Scroll Down]
[Error: Element Intercepted]  [Resolved By: Force Click or Close Modal] Hermes 3 can look at the error it receives from Playwright, walk the graph to find historical solutions, and autonomously apply the fix.
Using Graph RAG for the web DOM and Intent Routing is exactly how cutting-edge agents (like MultiOn or AutoGPT) navigate the internet.

Here is the exact technical roadmap to build your Hybrid Agentic Workflow using Graph Engineering. You can feed these phases directly to your Antigravity agent to start vibe coding.
Phase 1: Build the Semantic Intent Graph
Before touching the browser, the AI needs to map your prompt to known skills.
The Intent Parser: Create a new module (e.g., intent_router.py) that uses Hermes 3 to parse your prompt ("Buy a red shirt on Flipkart") into a Knowledge Graph query.
Graph Matching: The router queries your database of saved synthesized_skill.json files. It identifies that a "Flipkart Search" skill exists, but detects a "missing edge" in the graph between the skill's end state (Search Results) and your requested end state (Checkout).
The Execution Plan: The router generates a two-part plan: execute the Flipkart Search skill with the color_filter variable set to "red", then flag a hand-off.
Phase 2: The Browser Handoff Engine (The Bridge)
Currently, your run_skill.py execution engine likely closes the browser after completing its recorded steps. We need to keep it alive.
Modify SkillExecutor: Update the executor to accept a keep_alive=True parameter.
WebSocket Handshake: Instead of shutting down Playwright, the script connects the active browser tab's Context to your AI Server running on ws://localhost:8765/api.
Transfer of Power: Control is officially passed to local_webai_server_guided.py, leaving the browser open on the red shirts search results page.
Phase 3: Upgrade to DOM-to-Graph Engineering
To help Hermes 3 navigate the unrecorded checkout process flawlessly, we will upgrade your element detection.
Modify crawl_helper.py: Right now, this file uses html_to_llm_markdown() to flatten the page. Antigravity will add a new function to convert the DOM into a spatial graph (e.g., linking the "Add to Cart" button node to the "Red Shirt Image" node).
Spatial Context: This graph data will be fed into the server's existing _build_spatial_prompt() function, giving Hermes 3 a mathematical map of the screen.
Phase 4: The Autonomous Execution Loop
Now the AI takes over to finish the task.
Snapshot & Plan: The local_webai_server_guided.py triggers get_dom_snapshot() and uses ollama_chat() to ask Hermes 3 what to do next.
Action Dispatch: Hermes 3 identifies the "Add to Cart" button from the graph and dispatches physical clicks to the browser via the _execute_command() function in ai.py.
Checkout & Payment: The autonomous loop repeats, navigating the cart and pulling your address details from your encrypted database config to finish the order.


The combination of pyttsx3 for the non-blocking TTS cue, faster-whisper for the vocal transcription, and the injected JS document.addEventListener('click', ...) for spatial coordinate mapping is a massive leap forward. Your WebAI platform isn't just self-healing anymore; it's genuinely collaborative. Gracefully falling back to terminal/UI input when audio drivers are missing is just good engineering.
With Phase 10 officially wrapped, documented, and synchronized with your Mermaid knowledge graphs, the platform's core automation, execution, and AI orchestration tiers are incredibly robust.
Looking at the project roadmap and backlog, we have a few distinct directions we can take for Phase 11:
Option A: The Logic Engine (High Priority)
Variable Persistence: Upgrading page.__extracted_data__ to a persistent context state that survives across steps.
Conditional Branching: Adding a condition action type (if variable > threshold → execute Sub-Task A, else Sub-Task B).
Jira Integration: Using those conditions to trigger external webhook/API calls to create incident tickets automatically.
Option B: Production Hardening (Medium Priority)
Security & Env Vars: Removing the hardcoded API key from run_from_database.py and shifting it to .env.
API Server Polish: Disabling database echo=True (SQL logging) to clean up terminal output and restricting CORS allow_origins for security.
Navigation Safety: Wiring up the existing validatePage function to trigger explicitly after goto/navigate actions for stricter DOM readiness validation.
Option C: The UI/Dashboard Expansion
Adding front-end configuration menus in the Vue/React SPA for setting these new variables, managing API keys, or visualizing the execution graph live.
Which path would you like to take next? If it's Conditional Branching, I can draft the Modification Plan and we can spin up the next TDVC loop.



Here is the optimal sequence for Phase 11.
Step 1: Stability & Hardening (The Foundation)
Before introducing complex decision-making, the core execution loop must be flawless. This step addresses the runtime bugs you discovered during the Flipkart E2E test and secures the platform.
Post-HITL State Reset: Modify the server to clear the executed action from the queue immediately after a Human-in-the-Loop intervention so the planner does not get stuck in a repetitive loop.
Navigation & Readiness: Wire up a validatePage function to trigger automatically after new tabs open or navigations occur, ensuring the AI waits for the network to idle and scrolls the page to expose hidden variant buttons.
Security Configuration: Shift the hardcoded API key out of run_from_database.py into a .env file and restrict CORS policies.
Step 2: The Logic Engine & Observer Mode (The Brain)
Once the execution loop is stable, we upgrade the AI's ability to maintain context and handle multi-step flows.
Continuous Observer Mode: Upgrade the HITL plugin to inject a floating "Resume AI" button on the webpage. This allows the bot to pause, observe you navigating a login or size-selection flow, and take a fresh DOM snapshot once you click resume.
Variable Persistence: Upgrade page.__extracted_data__ to a persistent context state that survives across individual steps.
Conditional Branching & Webhooks: Introduce a condition action type (e.g., if price > threshold) and wire it to trigger external API calls, like Jira ticket creation.
Step 3: UI & Dashboard Expansion (The Interface)
With the backend logic running smoothly, we expose these new capabilities to the end-user.
Front-End Controls: Add configuration menus to your Vue/React SPA to manage .env variables and API keys visually.
Live Execution Graph: Build a visualization component in the dashboard to track the AI's step-by-step logic, branches, and active variables during a live run.

Welcome to Phase 12
With that technical debt cleared, we can jump straight into the advanced telemetry and verification systems. Which of the two components do you want to tackle first?
Option A: JS Telemetry Injector (Observer Mode) We write the JavaScript payload that gets injected when the HITL panel pauses the AI. It will secretly record the exact CSS path, XPath, and text of whatever the human clicks (using the capture phase to bypass stopPropagation SPA traps). When the user clicks "Resume", we feed that exact data back to the LLM so it learns instantly.
Option B: Speculative Execution & Backtracking We design the prompt instructions and tool structure to give the LLM the page.go_back() command. We'll build the logic for how the AI takes a DOM snapshot, clicks a speculative link, evaluates if the state actually changed, and rolls back if it realizes it went down the wrong path.
1. Smart JS Semantic Filtering (The First Shield)
Instead of recording every mousedown event blindly, our injected JavaScript listener should evaluate the clicked element's semantic value on the fly.
Ignore Dead Space: Automatically discard clicks on <body>, <html>, or empty <div> and <span> tags that have no text content and no explicit cursor: pointer styles.
Capture Interactive Elements: Only record clicks on known interactive tags (<a>, <button>, <input>, [role="button"], <select>) or elements that contain significant text.
2. DOM Mutation Verification (The Gold Standard)
Sometimes a user clicks a "blank" space to close a modal overlay or a dropdown menu. How does the bot know if a click on a seemingly dead <div> was actually important?
The Solution: We can temporarily attach a MutationObserver to the document during the Observer Mode.
If a click results in the DOM changing (nodes added/removed) or the URL changing within 500ms, we flag it as a State-Changing Click. If the user clicks empty space and nothing happens, the JS throws it away as noise.
3. Voice-to-Action Correlation (LLM Intent Matching)
When the user clicks "Resume AI," we pass the filtered action log alongside their voice transcription (e.g., "I clicked the second checkout button").
We can update the LLM prompt to instruct it to map the transcribed audio intent to the telemetry log.
If the telemetry captured three clicks, but the final click was on an element with the text "Checkout," the LLM will intelligently discard the first two as browsing behavior.
How to Proceed
By combining JS filtering with LLM reasoning, we ensure the bot only learns from the actual successful action.
