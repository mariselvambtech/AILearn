<!-- converted from Scenario based learning.docx -->

1. Systran / faster-distil-whisper-large-v3
This is a "distilled" (compressed) version of OpenAI's massive Whisper Large V3 model. The researchers specifically tuned it to run fast while removing the famous Whisper "hallucination loops" (where it invents words during silence or background noise).
Why choose it? It is the path of least resistance. Because your audio_aligner.py already uses the faster-whisper library, upgrading to this model is literally a one-line string change.
The Catch: Even though it is compressed, it is still based on a large architecture. If your local machine doesn't have a dedicated GPU or high RAM, it might take a few seconds longer to process your voice snippets compared to the tiny base.en model.
2. SenseVoice (Alibaba / FunAudioLLM)
SenseVoice is built on a completely different architecture (non-autoregressive). Instead of predicting words one by one like Whisper (which is what caused it to guess "tripcord"), it processes chunks of audio simultaneously.
Why choose it? It is an absolute powerhouse for speed and accents. If you speak with an Indian accent, or occasionally mix in regional words, SenseVoice handles it flawlessly. Because it is incredibly lightweight, it will process your automation commands almost instantly on any standard laptop CPU.
The Catch: You cannot use your current faster-whisper code. You would have to install Alibaba's FunASR library, rewrite the transcription function in audio_aligner.py, and adjust how you extract the timestamps for alignment.


Python
result = await ai(task_text, page=page, options={"max_rounds": 25})

switch between Systran / faster-distil-whisper-large-v3 or SenseVoice (Alibaba / FunAudioLLM)


Option 1: Use SenseVoice (Alibaba)
To use the lightning-fast SenseVoice model (which you just installed):
PowerShell
$env:VOICE_MODEL="sensevoice"
.\.venv\Scripts\python.exe .\run_autonomous.py
Note: The first time you run this, it will pause for a minute to download the SenseVoiceSmall model weights from the ModelScope hub to your local cache.
Option 2: Switch back to Whisper (Systran)
If you need broader language support (like Hindi/Tamil) or just want to go back to the Whisper model:
PowerShell
$env:VOICE_MODEL="whisper"
.\.venv\Scripts\python.exe .\run_autonomous.py
Option 3: Permanently set a default (Optional)
If you decide you love SenseVoice and want it to be your default every time you open a terminal without typing $env:VOICE_MODEL every time, you can add it to your Windows User Environment Variables:
Press your Windows key and type "Environment Variables".
Click "Edit the system environment variables".
Click the "Environment Variables..." button.
Under the top section (User variables), click New.
Set Variable name to VOICE_MODEL and Variable value to sensevoice.
Click OK. (You will need to restart VS Code or your terminal for it to take effect).

