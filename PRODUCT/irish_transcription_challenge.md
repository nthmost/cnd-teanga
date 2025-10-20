# The Irish Language Transcription Challenge

**Date:** October 19, 2025
**Status:** Shelved - No viable automated solution found
**Problem:** Automated Speech Recognition for broadcast Irish produces unusable output

---

## Executive Summary

We explored three different approaches to transcribing Irish language audio from Raidió na Gaeltachta broadcasts. All three approaches failed to produce usable Irish transcripts:

1. **Whisper (auto-detect):** Produces Welsh orthography instead of Irish
2. **Whisper (English mode):** Interprets Irish as English words (lossy)
3. **Irish wav2vec2:** Produces Irish-looking gibberish (unusable)

**Conclusion:** Automated Irish transcription for broadcast audio is not currently viable with available models. Manual transcription or human-in-the-loop workflows are required.

---

## Test Setup

### Audio Source
- **Episode:** Barrscéalta (news magazine), October 17, 2025
- **Duration:** 5-minute test clip (60s-360s)
- **Format:** 16kHz mono WAV (Whisper-ready)
- **Quality:** Professional broadcast audio, native Irish speakers

### Hardware
- **GPU:** NVIDIA GeForce RTX 4080 (16GB VRAM)
- **CPU:** AMD Ryzen 7 2700X
- **RAM:** 62GB

---

## Approach 1: Whisper with Auto-Detect

### Method
- **Model:** faster-whisper medium
- **Device:** CUDA (GPU)
- **Language:** None (auto-detect)
- **Rationale:** Let Whisper choose the best language match

### Configuration
```python
transcriber = WhisperTranscriber(model_size='medium', device='cuda')
result = transcriber.transcribe(audio_path, language=None)
```

### Results

**Language Detected:** Welsh (cy) with 58% probability

**Performance:**
- Transcription time: 54 seconds
- Speed: ~5.5x realtime
- Segments: 79

**Sample Output:**
```
ond es i gyd, ta' tosi o'n ddib, cymorthas o'n i'r ychlaer ein newt,
na'n lwysig ymrwy o'r Cholisef Omre o'r grŵpau tras na.
Wel, nid oes i'n closio'n gomse ac ydw i'n gweithio ymlaen,
ac roeddwn i'n gweithio gyda chiol, sa' cwcaim ar ei,
```

**Full output saved to:**
- `data/episodes/rnag_barrscealta_20251017_1100/transcript.txt` (Welsh orthography)
- `data/episodes/rnag_barrscealta_20251017_1100/raw_whisper.json` (with timestamps)
- `data/episodes/rnag_barrscealta_20251017_1100/subtitles.vtt` (timed captions)

### Analysis

**Why Welsh?**
- Irish (language code 'ga') is **not in faster-whisper's supported languages**
- Whisper detects Irish as Welsh (both Celtic languages, similar phonetics)
- Uses Welsh orthography rules to represent Irish sounds

**Quality Assessment:**
- ❌ **Not Irish text** - Uses Welsh spelling conventions
- ✅ **Phonetically accurate** - Captures sounds correctly
- ✅ **Good timestamps** - Word and segment-level timing accurate
- ❌ **Unusable for Irish learners** - Wrong language entirely

**Character Patterns:**
- Welsh digraphs: `dd`, `ch`, `ll`, `ff`
- Welsh diacritics: `ŵ`, `ŷ`
- Welsh words: `ond`, `wel`, `ac`, `yn`

### Why This Failed

Converting Welsh orthography to proper Irish would require:
1. Understanding phonetic mapping (Welsh → Irish)
2. Irish language knowledge (vocabulary, grammar)
3. Context understanding (what makes sense in Irish)

This is essentially **machine translation** from nonsense Welsh to Irish - not viable.

---

## Approach 2: Whisper with English Mode

### Method
- **Model:** faster-whisper medium
- **Device:** CUDA (GPU)
- **Language:** `en` (forced English)
- **Rationale:** Maybe English orthography preserves Irish better than Welsh

### Configuration
```python
transcriber = WhisperTranscriber(model_size='medium', device='cuda')
result = transcriber.transcribe(audio_path, language='en')
```

### Results

**Language Detected:** English (en) with 100% confidence (forced)

**Sample Output:**
```
But listen, there are some people out there who don't know the song at all.
I don't know if you've heard of the band Trasna.
Well, they haven't heard of me and I'm here on the other side.
And I was working with...
```

### Analysis

**What Happened:**
- Whisper **interpreted** Irish speech as English words
- Created English sentences based on phonetic similarity
- Completely lost Irish meaning and structure

**Quality Assessment:**
- ❌ **Not Irish at all** - English interpretation of Irish sounds
- ❌ **Meaning lost** - Made-up English that sounds vaguely similar
- ❌ **Unusable** - Even worse than Welsh approach

**Example Problem:**
Irish audio containing words like "tá", "agus", "an" gets interpreted as English phrases like "there are", "and I was", etc.

### Why This Failed

English mode is even more lossy than auto-detect:
- Loses Irish phonetic nuance
- Imposes English grammar structure
- Creates plausible-sounding but meaningless English
- No path back to original Irish meaning

---

## Approach 3: Irish-Specific wav2vec2 Model

### Method
- **Model:** `Aditya3107/wav2vec2-large-xls-r-1b-ga-ie` (Hugging Face)
- **Device:** CUDA (GPU)
- **Training:** Common Voice Irish + Living Irish Audio dataset
- **Reported WER:** 25.94% on test set
- **Rationale:** Purpose-built for Irish, should produce Irish orthography

### Configuration
```python
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

processor = Wav2Vec2Processor.from_pretrained(
    "Aditya3107/wav2vec2-large-xls-r-1b-ga-ie"
)
model = Wav2Vec2ForCTC.from_pretrained(
    "Aditya3107/wav2vec2-large-xls-r-1b-ga-ie"
)
```

### Results

**Performance:**
- Model load time: 123 seconds (first run, downloads ~1.2GB model)
- Processing: Chunked in 30-second segments
- Total processing time: ~14 seconds for 5 minutes
- Speed: Faster than Whisper but no timestamps

**Sample Output:**
```
an éisigí tá tomhais gain bío comórtas ugainida ch léir inniu nalaos
agam ur cholasibh omala ar an dhúpe treasna bhal ní raibh siad clás
gamsa agus thaimestea ar éim an oidirlín aus bhí mig éisiort leá
cuid am ceoils acú camire iontaga do maiyh beirt fhaidagus aam
galanta na hádáinne atacú agus na baléid agus a léihidí sin bhul
bidhs siad ag ceol an astan na cúirte sa naoiche máire ag searht a
chlog agus ta dheith féide teicit le bronú againn ar dheith éisteat
inniu marsuné beirt a bheis a fáil
```

**Full output saved to:**
- `data/episodes/rnag_barrscealta_20251017_1100/media/transcript_irish_wav2vec2.txt`

### Analysis

**Recognizable Irish Words Found:**
- ✅ `tá` (is/are)
- ✅ `an` (the)
- ✅ `agus` (and)
- ✅ `inniu` (today)
- ✅ `ar` (on/at)
- ✅ `againn` (at us)
- ✅ `ní raibh` (was not)
- ✅ `siad` (they)

**Problems:**
- ❌ **Severe spacing errors** - `ugainida ch léir` should be separate words
- ❌ **Garbled words** - `nalaos`, `cholasibh omala`, `thaimestea ar éim`
- ❌ **Incomplete words** - Many words cut off or merged
- ❌ **No punctuation** - Run-on text
- ❌ **Gibberish phrases** - Not meaningful Irish despite Irish-looking characters

**Quality Assessment:**
- ✅ Irish orthography (correct character set)
- ✅ Some real Irish words detected
- ❌ **Majority is gibberish** - Not comprehensible Irish
- ❌ No timestamps (wav2vec2 limitation)
- ❌ **Unusable for learning materials**

### Why This Failed

**Training Data Mismatch:**
- Model trained on **Common Voice** (volunteers reading prepared sentences)
- Test audio is **broadcast radio** (natural, spontaneous speech)
- Very different acoustic characteristics

**Specific Problems:**
1. **Fast, natural speech** vs. clear, read speech
2. **Broadcast audio quality** (compression, transmission) vs. studio recordings
3. **Multiple speakers** and overlapping audio
4. **Background music** and sound effects
5. **Spontaneous speech patterns** (false starts, corrections, natural flow)

The model essentially fails at the ASR task - it's producing Irish-looking characters but not performing accurate speech recognition.

---

## Comparative Analysis

| Aspect | Whisper (Auto) | Whisper (English) | Irish wav2vec2 |
|--------|---------------|-------------------|----------------|
| **Orthography** | Welsh | English | Irish |
| **Phonetics** | ✅ Accurate | ❌ Lossy | ⚠️ Partial |
| **ASR Quality** | ✅ Excellent | ✅ Excellent | ❌ Poor |
| **Timestamps** | ✅ Yes | ✅ Yes | ❌ No |
| **Usability** | ❌ Wrong lang | ❌ Wrong lang | ❌ Gibberish |
| **Speed (GPU)** | 5.5x realtime | 5.5x realtime | 21x realtime |

---

## Root Cause Analysis

### The Core Problem

**Irish broadcast ASR is a hard problem that requires:**

1. **Irish-specific acoustic model** (exists but poorly trained)
2. **Broadcast-quality training data** (doesn't exist in quantity)
3. **Language model for Irish** (weak - small corpus)
4. **Dialect handling** (Ulster, Connacht, Munster variations)

### Why Current Solutions Fail

**Whisper:**
- No Irish in training languages
- Falls back to closest match (Welsh)
- Excellent ASR but wrong language
- Post-processing won't fix fundamental language mismatch

**wav2vec2:**
- Trained on clean, read speech
- Fails on natural, broadcast speech
- Small training dataset (~5,000 utterances)
- Overfits to Common Voice recording style

### The Training Data Gap

**What exists:**
- Common Voice Irish: ~5,000 utterances (read sentences)
- Living Irish Audio: Unknown quantity, likely similar quality

**What's needed:**
- Hundreds of hours of transcribed broadcast Irish
- Professional transcription (expensive)
- Dialect diversity
- Natural speech patterns

**Current gap:** Orders of magnitude insufficient training data

---

## Attempted Solutions (Abandoned)

### 1. AI Post-Processing (Claude/GPT-4)

**Idea:** Use Claude or GPT-4 to:
- Convert Welsh orthography → Irish
- Clean up wav2vec2 gibberish
- Leverage AI's multilingual capabilities

**Why Abandoned:**
- Welsh → Irish conversion is essentially **machine translation from nonsense**
- AI would be **guessing/hallucinating** Irish content
- No ground truth to validate against
- High risk of plausible-sounding but incorrect Irish
- Defeats purpose of automated transcription

### 2. Hybrid Approach

**Idea:** Combine multiple models:
- Whisper for timing/structure
- wav2vec2 for Irish characters
- AI to merge both

**Why Abandoned:**
- Whisper timing is for Welsh words (wrong boundaries)
- wav2vec2 output is gibberish (no useful signal)
- Combining two bad outputs doesn't create one good output
- Overly complex with no quality improvement

### 3. Fine-tuning wav2vec2

**Idea:** Fine-tune the Irish model on broadcast data

**Why Abandoned:**
- Requires transcribed broadcast Irish (which we don't have)
- Expensive (need human transcribers)
- Out of scope for this project
- Chicken-and-egg problem (need transcripts to build transcriber)

---

## What Would Work (Future Research)

### Option 1: Build Broadcast Training Dataset
- Manually transcribe 100-500 hours of RnaG broadcasts
- Fine-tune wav2vec2 or train Whisper adapter
- **Cost:** $50,000-$200,000 (transcription + compute)
- **Timeline:** 6-12 months

### Option 2: Human-in-the-Loop
- Use Whisper timestamps to segment audio
- Human transcribes segments
- Build dataset incrementally
- Eventually fine-tune model
- **Cost:** Ongoing transcription costs
- **Timeline:** Incremental improvement

### Option 3: Wait for Better Models
- OpenAI may add Irish to future Whisper versions
- Meta/others may release better multilingual models
- Irish community may create training datasets
- **Cost:** $0
- **Timeline:** Unknown (years?)

---

## Recommendations

### For This Project (Short-term)

**Accept that automated Irish transcription is not viable.**

**Pivot to:**
1. **Manual transcription workflow** - Humans transcribe samples
2. **Focus on other components** - Glossing, exercises, dialect detection can work with manual transcripts
3. **Conductor orchestration** - Build workflow infrastructure for when transcription improves
4. **Proof-of-concept** - Use manually transcribed samples to demonstrate the full pipeline

### For Irish Language Community (Long-term)

**Recommended Actions:**
1. **Organize transcription efforts** - Community-driven Raidió na Gaeltachta transcription project
2. **Partner with universities** - Academic projects to build training datasets
3. **Engage RTE** - National broadcaster could fund/support Irish ASR research
4. **Open source datasets** - Make any transcriptions publicly available
5. **Coordinate with Common Voice** - But focus on natural speech, not read sentences

---

## Technical Artifacts Generated

### Files Created During Exploration

**Whisper Transcripts (Welsh):**
- `data/episodes/rnag_barrscealta_20251017_1100/transcript.txt`
- `data/episodes/rnag_barrscealta_20251017_1100/raw_whisper.json`
- `data/episodes/rnag_barrscealta_20251017_1100/subtitles.vtt`

**wav2vec2 Transcript (Garbled Irish):**
- `data/episodes/rnag_barrscealta_20251017_1100/media/transcript_irish_wav2vec2.txt`

**Test Scripts:**
- `scripts/try_transcription.py` (Whisper testing)
- `scripts/try_irish_wav2vec2.py` (wav2vec2 testing)
- `scripts/extract_test_clip.py` (Test clip extraction)

**Dependencies Added:**
- `transformers` (Hugging Face)
- `librosa` (Audio processing)

### Code Worth Keeping

Even though Irish transcription failed, we built useful infrastructure:

✅ **Keep:**
- Whisper transcription pipeline (works for other languages)
- Test clip extraction (useful for rapid iteration)
- GPU transcription setup (cuDNN wrapper)
- Episode storage structure

❌ **Remove/Archive:**
- Irish wav2vec2 specific code
- AI post-processing experiments (never implemented)

---

## Lessons Learned

### Technical Lessons

1. **Language support matters** - ASR quality is irrelevant if it's the wrong language
2. **Training data quality >> quantity** - 5K clean sentences < 100 hours broadcast
3. **Domain mismatch is fatal** - Read speech ≠ broadcast speech
4. **Post-processing can't fix fundamental issues** - Garbage in, garbage out applies to AI too

### Product Lessons

1. **Validate core assumptions early** - Should have tested Irish transcription quality before building pipeline
2. **Manual processes are okay** - Not everything needs to be automated
3. **Failed experiments are valuable** - This documentation helps others avoid same path
4. **Pivot when blocked** - Don't force solutions to unsolvable problems

### Project Management Lessons

1. **Build incrementally** - We successfully completed Iterations 1-2 before hitting this wall
2. **Document everything** - This writeup makes the failure useful
3. **Set realistic expectations** - "AI-enhanced" doesn't mean "fully automated"

---

## Status: Shelved

**Reason:** No viable automated Irish transcription solution exists with current models and training data.

**Impact on Project:**
- Core vision (AI-enhanced learning materials) still valid
- Requires manual transcription as input instead of automated
- Other components (glossing, exercises, dialect detection) can proceed
- Conductor orchestration can be built around manual + AI hybrid workflow

**Reopening Criteria:**
- New Irish ASR model released with proven broadcast quality
- Access to large corpus of transcribed broadcast Irish
- Funding secured for manual transcription project
- Community transcription effort reaches critical mass

---

## Appendix: Model Details

### Whisper (faster-whisper)
- **Version:** faster-whisper (CTranslate2 backend)
- **Model Size:** medium (769M parameters)
- **Supported Languages:** 97 languages (Irish not included)
- **Training Data:** 680,000 hours (mostly English)
- **Performance:** 5.5x realtime on RTX 4080

### wav2vec2-large-xls-r-1b-ga-ie
- **Provider:** Aditya3107 (Hugging Face)
- **Base Model:** facebook/wav2vec2-xls-r-1b
- **Training Data:** Common Voice Irish + Living Irish Audio
- **Training Size:** ~5,156 utterances (90% train, 10% test)
- **Test WER:** 25.94%
- **Limitations:** Trained on read speech, not broadcast

---

**Document Version:** 1.0
**Last Updated:** October 19, 2025
**Authors:** Claude Code + Human Collaboration
